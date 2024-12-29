"""RAG Chat UI with enhanced features"""

import streamlit as st
from ..rag import RAGManager
from .components.file_manager import FileManager
from .components.process_tracker import ProcessTracker
import time
from pathlib import Path
from typing import Dict


class RAGChatUI:
    def __init__(self):
        self.file_manager = FileManager()
        self.process_tracker = ProcessTracker()

        # Aseta direct oletukseksi session_statessa
        if "query_type" not in st.session_state:
            st.session_state.query_type = "direct"
        self.query_type = st.session_state.query_type

        # Initialize on startup
        if "rag_manager" not in st.session_state:
            st.session_state.rag_manager = RAGManager()

        if "messages" not in st.session_state:
            st.session_state.messages = []

    def main(self):
        """Main UI method"""
        self.setup_ui()

    def setup_ui(self):
        """Setup the UI components"""
        with st.sidebar:
            st.title("Dokumentit")
            uploaded_file = st.file_uploader(
                "Lataa dokumentti",
                type=["txt", "pdf", "md"],
            )
            if uploaded_file:
                self.handle_file_upload(uploaded_file)

            self.file_manager.render_file_list()

            st.markdown("### Asetukset")
            self.query_type = st.radio(
                "Kyselytyyppi",
                options=["direct", "rag", "summary"],
                format_func=lambda x: {
                    "rag": "Hae dokumenteista",
                    "direct": "Suora kysely",
                    "summary": "Yhteenveto",
                }[x],
                key="query_type",
            )

            # Lisätään info expander
            with st.expander("Lisätietoa", expanded=False):
                if self.query_type == "direct":
                    st.markdown("**Käytössä:** o1-mini")
                    st.markdown("- Suorat kyselyt ilman dokumenttikontekstia")
                elif self.query_type == "rag":
                    st.markdown("**Käytössä:** gpt-4o")
                    st.markdown("- Dokumenttien analysointi ja vastausten generointi")
                    st.markdown("- Kontekstin käsittely ja relevantin tiedon valinta")
                else:  # summary
                    st.markdown("**Käytössä:** o1-mini")
                    st.markdown("- Dokumenttien yhteenvetojen generointi")

            # Lisätään system prompt editor
            with st.expander("Muokkaa System Promptia"):
                if "system_prompt" not in st.session_state:
                    st.session_state.system_prompt = "Olet avulias tekoälyassistentti."

                new_prompt = st.text_area(
                    "System Prompt", st.session_state.system_prompt, height=100
                )
                if new_prompt != st.session_state.system_prompt:
                    st.session_state.system_prompt = new_prompt
                    self._save_system_prompt()

            # Muutetaan number_input slideriksi
            if "max_words" not in st.session_state:
                st.session_state.max_words = 100

            st.slider(
                "Maksimi sanamäärä vastauksessa",
                min_value=10,
                max_value=500,
                value=st.session_state.max_words,
                step=10,
                key="max_words",
                help="Liuta säätääksesi vastauksen maksimipituutta",
            )

        # Chat input ylhäällä
        if query := st.chat_input("Kirjoita kysymys..."):
            self.handle_query(query)

        # Jos on uusi kysymys/vastaus, näytä se omassa containerissa
        if len(st.session_state.messages) >= 2:
            st.markdown("### Viimeisin kysymys ja vastaus")
            with st.container():
                with st.chat_message("user"):
                    st.write(st.session_state.messages[-2]["content"])
                with st.chat_message("assistant"):
                    st.write(st.session_state.messages[-1]["content"])
                    metadata = st.session_state.messages[-1].get("metadata", {})
                    if metadata:
                        st.caption(
                            f"Malli: {metadata.get('model', 'tuntematon')}\n"
                            f"Tokenit: {metadata.get('input_tokens', 0)} (input) + "
                            f"{metadata.get('output_tokens', 0)} (output) = "
                            f"{metadata.get('total_tokens', 0)} (yhteensä)\n"
                            f"Hinta-arvio: ${metadata.get('cost_usd', 0):.4f}"
                        )
                    if (
                        "context" in st.session_state.messages[-1]
                        and st.session_state.messages[-1]["context"]
                    ):
                        with st.expander("Lähteet"):
                            for ctx in st.session_state.messages[-1]["context"]:
                                st.markdown(f"**{ctx['doc_id']}**")
                                st.markdown(ctx["chunk"])

        # Historia omassa expanderissa
        if len(st.session_state.messages) > 2:
            with st.expander("Aiemmat kysymykset ja vastaukset", expanded=False):
                for i in range(0, len(st.session_state.messages) - 2, 2):
                    with st.chat_message("user"):
                        st.write(st.session_state.messages[i]["content"])
                    with st.chat_message("assistant"):
                        st.write(st.session_state.messages[i + 1]["content"])
                        if (
                            "context" in st.session_state.messages[i + 1]
                            and st.session_state.messages[i + 1]["context"]
                        ):
                            with st.expander("Lähteet"):
                                for ctx in st.session_state.messages[i + 1]["context"]:
                                    st.markdown(f"**{ctx['doc_id']}**")
                                    st.markdown(ctx["chunk"])

    def handle_file_upload(self, file):
        """Handle file upload"""
        try:
            content = file.read().decode("utf-8")
            self.file_manager.save_file(file, {"indexed": False})
            st.session_state.rag_manager.add_document(
                content=content,
                doc_id=file.name,
                metadata={"type": file.type, "size": file.size},
            )
        except Exception as e:
            st.error(f"Virhe tiedoston käsittelyssä: {str(e)}")

    def handle_query(self, query: str):
        """Handle query"""
        try:
            st.session_state.messages.append({"role": "user", "content": query})

            # Välitä sekä max_words että system_prompt
            result = st.session_state.rag_manager.query(
                query,
                query_type=self.query_type,
                max_words=st.session_state.max_words,
                system_prompt=st.session_state.system_prompt,
            )

            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "content": result["response"],
                    "context": result.get("context", []),
                    "metadata": result.get("metadata", {}),
                }
            )
            st.rerun()

        except Exception as e:
            st.error(f"Virhe kyselyn käsittelyssä: {str(e)}")

    def _save_system_prompt(self):
        """Tallenna system prompt"""
        config_path = Path("data/config")
        config_path.mkdir(parents=True, exist_ok=True)

        with open(config_path / "system_prompt.txt", "w") as f:
            f.write(st.session_state.system_prompt)

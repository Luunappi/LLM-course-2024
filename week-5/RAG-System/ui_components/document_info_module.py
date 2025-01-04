"""
Document Module

Displays information about loaded documents and their processing status.
Shows document statistics and metadata.
"""

import streamlit as st
import pandas as pd
from datetime import datetime


def render_document_module():
    """Render document information"""
    with st.container():
        st.markdown(
            """
            <style>
            .document-container {
                background-color: rgba(17, 19, 23, 0.8);
                border: 1px solid rgba(128, 128, 128, 0.2);
                padding: 20px;
                border-radius: 4px;
                color: rgba(250, 250, 250, 0.8);
                margin: 10px 0;
            }
            .info-header {
                color: rgba(250, 250, 250, 0.9);
                font-size: 1.1em;
                margin-bottom: 10px;
            }
            .styled-table {
                width: 100%;
                border-collapse: collapse;
                margin: 10px 0;
            }
            .styled-table th {
                background-color: rgba(38, 39, 48, 0.8);
                padding: 8px;
                text-align: left;
                border-bottom: 1px solid rgba(128, 128, 128, 0.2);
            }
            .styled-table td {
                padding: 8px;
                border-bottom: 1px solid rgba(128, 128, 128, 0.1);
            }
            </style>
            """,
            unsafe_allow_html=True,
        )

        content = "<div class='document-container'>"

        # Document statistics
        if st.session_state.processed_files:
            content += "<div class='info-header'>Currently loaded documents:</div>"

            # Create table data
            data = []
            for filename, file_data in st.session_state.processed_files.items():
                chunks = file_data["chunks"]
                chunks_count = len(chunks)
                words_count = sum(len(chunk.split()) for chunk in chunks)
                timestamp = datetime.fromisoformat(
                    file_data.get("timestamp", datetime.now().isoformat())
                )
                date_str = timestamp.strftime("%Y-%m-%d")

                data.append(
                    {
                        "Filename": filename,
                        "Chunks": chunks_count,
                        "Words": words_count,
                        "Loaded": date_str,
                    }
                )

            # Convert to HTML table
            if data:
                df = pd.DataFrame(data)
                content += df.to_html(index=False, classes="styled-table")

                # Add embedding info
                for filename, file_data in st.session_state.processed_files.items():
                    if "embeddings" in file_data:
                        content += f"<br>Embeddings shape for {filename}: {file_data['embeddings'].shape}"
        else:
            content += "<p>No documents loaded</p>"

        content += "</div>"
        st.markdown(content, unsafe_allow_html=True)

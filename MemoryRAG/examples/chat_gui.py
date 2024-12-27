"""Graafinen käyttöliittymä MemoryRAG:n testaamiseen"""

import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox
from pathlib import Path
from memoryrag import MemoryRAG
from memoryrag.file_handlers import read_document


class MemoryRagGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("MemoryRAG Chat")
        self.rag = MemoryRAG()

        self.setup_ui()

    def setup_ui(self):
        # Pääkehys
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Vasen puoli - Dokumentit ja muisti
        left_frame = ttk.LabelFrame(
            main_frame, text="Dokumentit ja muisti", padding="5"
        )
        left_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5)

        # Dokumenttien latausnapit
        ttk.Button(
            left_frame, text="Lataa dokumentti", command=self.load_document
        ).grid(row=0, column=0, pady=5)
        ttk.Button(left_frame, text="Lataa muisti", command=self.load_memory).grid(
            row=1, column=0, pady=5
        )
        ttk.Button(left_frame, text="Tallenna muisti", command=self.save_memory).grid(
            row=2, column=0, pady=5
        )
        ttk.Button(left_frame, text="Tyhjennä muisti", command=self.clear_memory).grid(
            row=3, column=0, pady=5
        )

        # Muistin tila
        ttk.Label(left_frame, text="Muistin tila:").grid(row=4, column=0, pady=5)
        self.memory_stats = scrolledtext.ScrolledText(left_frame, width=30, height=10)
        self.memory_stats.grid(row=5, column=0, pady=5)

        # Oikea puoli - Chat
        right_frame = ttk.LabelFrame(main_frame, text="Chat", padding="5")
        right_frame.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5)

        # Chat-historia
        self.chat_history = scrolledtext.ScrolledText(right_frame, width=50, height=20)
        self.chat_history.grid(row=0, column=0, columnspan=2, pady=5)

        # Syötekenttä
        self.input_field = ttk.Entry(right_frame, width=40)
        self.input_field.grid(row=1, column=0, pady=5)
        self.input_field.bind("<Return>", self.send_message)

        # Lähetä-nappi
        ttk.Button(right_frame, text="Lähetä", command=self.send_message).grid(
            row=1, column=1, pady=5, padx=5
        )

        # Päivitä muistin tila
        self.update_memory_stats()

    def load_document(self):
        files = filedialog.askopenfilenames(
            title="Valitse dokumentit",
            filetypes=[
                ("Kaikki tuetut", "*.pdf;*.docx;*.txt;*.csv;*.xlsx;*.html"),
                ("PDF tiedostot", "*.pdf"),
                ("Word tiedostot", "*.docx"),
                ("Tekstitiedostot", "*.txt"),
                ("CSV tiedostot", "*.csv"),
                ("Excel tiedostot", "*.xlsx"),
                ("HTML tiedostot", "*.html"),
            ],
        )

        if not files:
            return

        for file in files:
            try:
                paragraphs = read_document(file)
                self.add_to_chat(f"Ladattu: {file} ({len(paragraphs)} kappaletta)")
                for p in paragraphs:
                    self.rag._store_memory("semantic", p, importance=0.7)
            except Exception as e:
                self.add_to_chat(f"Virhe ladattaessa {file}: {e}")

        self.update_memory_stats()

    def load_memory(self):
        file = filedialog.askopenfilename(
            title="Lataa muisti", filetypes=[("JSON tiedostot", "*.json")]
        )
        if file:
            try:
                self.rag.storage.load_memories(file)
                self.add_to_chat(f"Muisti ladattu: {file}")
                self.update_memory_stats()
            except Exception as e:
                messagebox.showerror("Virhe", f"Virhe ladattaessa muistia: {e}")

    def save_memory(self):
        file = filedialog.asksaveasfilename(
            title="Tallenna muisti",
            defaultextension=".json",
            filetypes=[("JSON tiedostot", "*.json")],
        )
        if file:
            try:
                self.rag.storage.save_memories(file)
                self.add_to_chat(f"Muisti tallennettu: {file}")
            except Exception as e:
                messagebox.showerror("Virhe", f"Virhe tallennettaessa muistia: {e}")

    def clear_memory(self):
        if messagebox.askyesno("Vahvista", "Haluatko varmasti tyhjentää muistin?"):
            self.rag.clear_memories()
            self.add_to_chat("Muisti tyhjennetty")
            self.update_memory_stats()

    def update_memory_stats(self):
        stats = {k: len(v) for k, v in self.rag.memory_types.items()}
        self.memory_stats.delete("1.0", tk.END)
        for type_, count in stats.items():
            self.memory_stats.insert(tk.END, f"{type_}: {count} muistia\n")

    def add_to_chat(self, message: str, prefix: str = ""):
        self.chat_history.insert(tk.END, f"{prefix}{message}\n")
        self.chat_history.see(tk.END)

    def send_message(self, event=None):
        query = self.input_field.get().strip()
        if not query:
            return

        self.input_field.delete(0, tk.END)
        self.add_to_chat(query, "Sinä: ")

        try:
            response = self.rag.process_query(query)
            self.add_to_chat(response, "Assistentti: ")

            # Näytä käytetyt muistit
            context = self.rag.context_manager.get_last_context()
            if context.strip():
                self.add_to_chat("\nKäytetyt muistit:", "")
                for i, mem in enumerate(context.split("\n"), 1):
                    if mem.strip():
                        self.add_to_chat(f"{i}. {mem}", "")

        except Exception as e:
            self.add_to_chat(f"Virhe: {e}", "")


def main():
    root = tk.Tk()
    app = MemoryRagGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()

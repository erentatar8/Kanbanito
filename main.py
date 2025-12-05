import tkinter as tk
from tkinter import ttk
import sv_ttk
from drag_manager import DragManager
from components import Column

# -------------------------------------------------------------------------
# Ana Uygulama Sınıfı
# -------------------------------------------------------------------------
class KanbanApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Modern Kanban")
        self.geometry("1100x700")
        self.minsize(900, 600)

        # Temayı başlat (Dark mode varsayılan)
        sv_ttk.set_theme("dark")
        self.is_dark = True
        
        # DragManager'ı başlat (Tüm uygulama için ortak)
        self.drag_manager = DragManager(self)
        self._setup_ui()

    def _setup_ui(self):
        # Arayüz elemanlarını yerleştirir.
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        # --- Üst Bar (Başlık ve Tema Butonu) ---
        topbar = ttk.Frame(self, padding=10)
        topbar.grid(row=0, column=0, sticky="ew")
        topbar.columnconfigure(1, weight=1) # Başlığı sola, butonu sağa itmek için orta alanı esnek yapabilirdik ama burada basit grid kullanıyoruz.

        title_lbl = ttk.Label(topbar, text="Kanban Board", font=("Segoe UI Variable Display", 20, "bold"))
        title_lbl.grid(row=0, column=0, sticky="w")

        self.theme_btn = ttk.Button(topbar, text="Switch to Light Mode", command=self.toggle_theme)
        self.theme_btn.grid(row=0, column=2, sticky="e")

        # --- Ana İçerik Alanı (Sütunlar) ---
        content = ttk.Frame(self, padding=15)
        content.grid(row=1, column=0, sticky="nsew")
        
        # 3 Sütun için ızgarayı ayarla (uniform ile hepsi eşit genişlikte olur)
        for i in range(3):
            content.columnconfigure(i, weight=1, uniform="col")
        content.rowconfigure(0, weight=1)

        self.columns = []
        titles = ["To Do", "In Progress", "Done"]
        
        # Sütunları döngüyle oluşturup yerleştir
        for i, t in enumerate(titles):
            # Components'tan gelen Column sınıfını kullanıyoruz
            col = Column(content, t, self.drag_manager)
            col.grid(row=0, column=i, sticky="nsew", padx=10)
            self.columns.append(col)

    def toggle_theme(self):
        # Aydınlık/Karanlık mod arasında geçiş yapar.
        if self.is_dark:
            sv_ttk.set_theme("light")
            self.theme_btn.configure(text="Switch to Dark Mode")
            self.is_dark = False
        else:
            sv_ttk.set_theme("dark")
            self.theme_btn.configure(text="Switch to Light Mode")
            self.is_dark = True


if __name__ == "__main__":
    app = KanbanApp()
    app.mainloop()

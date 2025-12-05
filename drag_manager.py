
import tkinter as tk
from tkinter import ttk

# -------------------------------------------------------------------------
# Sürükle-Bırak işlemlerini yöneten sınıf
# -------------------------------------------------------------------------
class DragManager:
    
   # Bu sınıf, kartların sürüklenip bırakılma (Drag & Drop) mantığını yönetir.
   # Sürükleme başladığında 'hayalet' bir pencere oluşturur ve bunu fareyle takip ettirir.
   # Bırakıldığında ise altına denk gelen sütunu bulup kartı oraya taşır.
    def __init__(self, root):
        self.root = root
        self.drag_data = {"x": 0, "y": 0, "item": None}
        self.drag_window = None

    def start_drag(self, event, widget):

       # Sürükleme işlemini başlatır.

        # Kullanıcı metin düzenliyorsa (Entry widget) sürüklemeyi engelle
        if isinstance(event.widget, ttk.Entry):
            return

        self.drag_data["item"] = widget
        self.drag_data["x"] = event.x
        self.drag_data["y"] = event.y

        # Sürükleme efekti için geçici bir "hayalet" pencere (Toplevel) oluştur
        # Bu pencere ana pencerenin üstünde, yarı saydam ve çerçevesiz olacak.
        self.drag_window = tk.Toplevel(self.root)
        self.drag_window.overrideredirect(True) # Pencere kenarlıklarını kaldır
        self.drag_window.attributes("-alpha", 0.7) # Şeffaflık
        self.drag_window.attributes("-topmost", True) # Her zaman üstte
        
        # Sürüklenen widget'ın metnini alıp hayalet pencereye kopyala
        text = getattr(widget, "text_content", "")
        if not text and hasattr(widget, "label"):
             text = widget.label.cget("text")

        lbl = ttk.Label(self.drag_window, text=text, padding=10, relief="solid", borderwidth=1)
        lbl.pack()
        
        # Hayalet pencereyi farenin o anki konumuna yerleştir
        x = self.root.winfo_pointerx() - event.x
        y = self.root.winfo_pointery() - event.y
        self.drag_window.geometry(f"+{x}+{y}")

    def do_drag(self, event):
        # Fare hareket ettikçe hayalet pencereyi günceller.
        if self.drag_window:
            x = self.root.winfo_pointerx() - self.drag_data["x"]
            y = self.root.winfo_pointery() - self.drag_data["y"]
            self.drag_window.geometry(f"+{x}+{y}")

    def stop_drag(self, event):
        # Sürükleme bittiğinde (fare tuşu bırakıldığında) çalışır.
        # Hayalet pencereyi yok eder ve kartı yeni konumuna taşır.
        if self.drag_window:
            self.drag_window.destroy()
            self.drag_window = None

        widget = self.drag_data["item"]
        if not widget:
            return

        # Farenin bırakıldığı yerdeki widget'ı bul (hangi sütunun üzerindeyiz?)
        x, y = self.root.winfo_pointerx(), self.root.winfo_pointery()
        # winfo_containing o koordinattaki en alt widget'ı döndürür (label, buton vb.)
        target = self.root.winfo_containing(x, y)
        
        # Hiyerarşide yukarı çıkarak geçerli bir hedef (Sütun/Column) ara.
        current_widget = target
        new_column = None
        while current_widget:
            # Eğer widget bir Column ise (accept_drop özelliği varsa)
            if isinstance(current_widget, ttk.Frame) and hasattr(current_widget, "accept_drop"):
                new_column = current_widget
                break
            # Eğer bir Kart'ın üzerine bıraktıysak, o kartın sütununu hedef al.
            # DUZELTME: Circular Import onlemek icin isinstance(current_widget, Card) yerine duck typing kullaniyoruz.
            if hasattr(current_widget, "master_column"):
                new_column = current_widget.master_column
                break
            current_widget = current_widget.master

        # Eğer geçerli bir sütun bulduysak kartı taşı.
        if new_column and hasattr(new_column, "adopt_card"):
            original_column = widget.master_column
            if original_column != new_column:
                # Eski sütundan sil, yeni sütuna ekle.
                text = widget.text_content
                original_column.remove_card(widget)
                new_column.add_card_by_text(text)

        self.drag_data["item"] = None

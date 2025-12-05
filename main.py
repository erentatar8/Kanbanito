import tkinter as tk
from tkinter import ttk, simpledialog, messagebox
import sv_ttk

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
            if isinstance(current_widget, Card):
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


# -------------------------------------------------------------------------
# Tek bir görevi temsil eden Kart sınıfı
# -------------------------------------------------------------------------
class Card(ttk.Frame):
    # Kanban tahtasındaki her bir kartı temsil eder.
    # Hem görüntüleme (Label) hem de düzenleme (Entry) modlarını destekler.
    def __init__(self, master_column, master_frame, text: str, on_delete, drag_manager: DragManager, is_editing=False):
        super().__init__(master_frame, style="Card.TFrame", padding=(10, 8))
        self.master_column = master_column # Hangi sütuna ait olduğu
        self.text_content = text
        self.drag_manager = drag_manager
        self._on_delete = on_delete
        
        self.columnconfigure(0, weight=1)

        # Eğer düzenleme modundaysak (Yeni kart eklerken) Entry kutusu göster.
        if is_editing:
            self.entry = ttk.Entry(self)
            self.entry.grid(row=0, column=0, columnspan=2, sticky="ew")
            self.entry.insert(0, text)
            self.entry.focus_set() # İmleci direk içine odakla
            
            # Klavye kısayolları:
            self.entry.bind("<Return>", self._save_edit)  # Enter: Kaydet
            self.entry.bind("<Escape>", self._cancel_edit) # Esc: İptal
            self.entry.bind("<FocusOut>", self._save_edit) # Odak çıkınca: Kaydet
        else:
            self._render_view_mode() # Normal görüntüleme modu

    def _render_view_mode(self):
        # Kartın normal görünümünü oluşturur (Label ve Sil butonu).
        # Önceki widgetları temizle (Entry varsa silinsin)
        for child in self.winfo_children():
            child.destroy()

        self.label = ttk.Label(self, text=self.text_content, anchor="w", wraplength=220)
        self.label.grid(row=0, column=0, sticky="ew")
        
        self.delete_btn = ttk.Button(self, text="×", width=2, command=self._delete, style="Toolbutton")
        self.delete_btn.grid(row=0, column=1, sticky="e", padx=(5,0))

        # Görsel ayrım için çizgi
        self.sep = ttk.Separator(self, orient="horizontal")
        self.sep.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(5,0))

        # Sürükle-bırak için olayları (event) bağla.
        # Hem çerçeveye hem de içindeki yazıya tıklayınca sürüklemesi için hepsine bind ediyoruz.
        for w in (self, self.label):
            w.bind("<Button-1>", self._on_drag_start)       # Tıklama: Başla
            w.bind("<B1-Motion>", self._on_drag_motion)     # Sürükleme: Hareket et
            w.bind("<ButtonRelease-1>", self._on_drag_stop) # Bırakma: Bitir

    def _save_edit(self, event=None):
        # Düzenleme modundaki metni kaydeder.
        if not hasattr(self, 'entry'): return
        new_text = self.entry.get().strip()
        if new_text:
            self.text_content = new_text
            self._render_view_mode()
        else:
            # Eğer metin boşsa kartı sil (İptal etmiş varsayıyoruz)
            self._delete()

    def _cancel_edit(self, event=None):
        # Düzenlemeyi iptal eder.
        if not self.text_content:
            self._delete()
        else:
            self._render_view_mode()

    # --- Sürükleme Olay Yönlendiricileri ---
    def _on_drag_start(self, event):
        self.drag_manager.start_drag(event, self)

    def _on_drag_motion(self, event):
        self.drag_manager.do_drag(event)

    def _on_drag_stop(self, event):
        self.drag_manager.stop_drag(event)

    def _delete(self):
        # Kartı silme işlemini tetikler.
        if callable(self._on_delete):
            self._on_delete(self)


# -------------------------------------------------------------------------
# Sütun Sınıfı (Örn: To Do, In Progress)
# -------------------------------------------------------------------------
class Column(ttk.Frame):
    # Bir Kanban sütununu temsil eder.
    # İçinde kaydırılabilir (scrollable) bir alan ve kartlar barındırır.
    def __init__(self, master, title: str, drag_manager: DragManager):
        super().__init__(master, padding=(10, 10))
        self.columnconfigure(0, weight=1)
        self.drag_manager = drag_manager
        self.accept_drop = True # Sürükle-bırak hedefi olabilir

        # --- Başlık Alanı ---
        header = ttk.Frame(self)
        header.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        header.columnconfigure(0, weight=1)

        self.title_label = ttk.Label(header, text=title, font=("Segoe UI Variable", 12, "bold"))
        self.title_label.grid(row=0, column=0, sticky="w")

        # "+" Butonu: Direkt satır içine kart ekler
        self.add_btn = ttk.Button(header, text="+ Add", command=self.add_card_inline)
        self.add_btn.grid(row=0, column=1, sticky="e")

        # --- Kaydırılabilir İçerik Alanı ---
        # Scrollbar'ın düzgün çalışması için bir Canvas ve onun içinde bir Frame kullanıyoruz.
        self.canvas_frame = ttk.Frame(self) 
        self.canvas_frame.grid(row=1, column=0, sticky="nsew")
        self.canvas_frame.columnconfigure(0, weight=1)
        self.canvas_frame.rowconfigure(0, weight=1)
        self.rowconfigure(1, weight=1) # Sütunun dikeyde büyümesine izin ver

        self.canvas = tk.Canvas(self.canvas_frame, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self.canvas_frame, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.grid(row=0, column=0, sticky="nsew")
        # Scrollbar grid işlemi _update_scrollbar içinde dinamik yapılıyor (Gerekirse göster).

        self.cards_frame = ttk.Frame(self.canvas)
        # Canvas içine pencere olarak frame ekliyoruz
        self.canvas_window = self.canvas.create_window((0, 0), window=self.cards_frame, anchor="nw")
        
        # Boyut değişikliklerini dinle
        self.cards_frame.bind("<Configure>", self._on_frame_configure)
        self.canvas.bind("<Configure>", self._on_canvas_configure)

        self.cards: list[Card] = []

    def _on_frame_configure(self, event):
        # İçerik değiştiğinde scroll alanını güncelle.
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        self._update_scrollbar()

    def _on_canvas_configure(self, event):
        # Pencere boyutu değiştiğinde içindeki kartların genişliğini ayarla.
        self.canvas.itemconfigure(self.canvas_window, width=event.width)
        self._update_scrollbar()

    def _update_scrollbar(self):
        # Scrollbar'ı sadece içerik taştığında görünür yapar.
        self.canvas.update_idletasks() # Geometrik hesaplamaların bitmesini bekle
        bbox = self.canvas.bbox("all")
        if not bbox: return
        
        content_height = bbox[3] # İçeriğin toplam yüksekliği
        canvas_height = self.canvas.winfo_height() # Görünen alanın yüksekliği

        if content_height > canvas_height:
            self.scrollbar.grid(row=0, column=1, sticky="ns") # Göster
        else:
            self.scrollbar.grid_forget() # Gizle

    def add_card_inline(self):
        # Satır içi düzenleme modunda yeni bir kart ekler.
        def on_delete(c):
            self.remove_card(c)
        # is_editing=True ile başlatıyoruz
        card = Card(self, self.cards_frame, "", on_delete, self.drag_manager, is_editing=True)
        self.add_card_widget(card)

    def add_card_by_text(self, text: str):
        # Verilen metinle direkt (düzenleme modu olmadan) kart ekler.
        if not text: return
        def on_delete(c):
            self.remove_card(c)
        card = Card(self, self.cards_frame, text, on_delete, self.drag_manager, is_editing=False)
        self.add_card_widget(card)

    def add_card_widget(self, card: Card):
        # Oluşturulmuş kart widget'ını listeye ve ekrana ekler.
        self.cards.append(card)
        # En alta ekle
        card.grid(in_=self.cards_frame, row=len(self.cards) - 1, column=0, sticky="ew", pady=4)
        self.cards_frame.update_idletasks() # Kaydırma çubuğunun güncellenmesi için

    def remove_card(self, card: Card):
        # Kartı listeden ve ekrandan siler.
        if card in self.cards:
            self.cards.remove(card)
            card.destroy()
            # Kalan kartları tekrar sırala (boşluk kalmasın)
            for i, c in enumerate(self.cards):
                c.grid(row=i)
            self._update_scrollbar()

    def adopt_card(self, card: Card):
        # Başka bir sütundan sürüklenen kartı kabul eder.
        # Mevcut kartın metniyle burada yeni bir kart oluşturur.
        self.add_card_by_text(card.text_content)


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

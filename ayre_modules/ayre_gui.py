import tkinter as tk
from tkinter import filedialog, ttk
from pathlib import Path
import threading

# Check if tkinterdnd2 is available
try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
    HAS_DND = True
except ImportError:
    HAS_DND = False

class AyreGUI:
    def __init__(self, file_queue):
        self.file_queue = file_queue
        
        # Enable high DPI support before creating window
        try:
            from ctypes import windll
            windll.shcore.SetProcessDpiAwareness(1)
        except:
            pass
        
        if HAS_DND:
            self.root = TkinterDnD.Tk()
        else:
            self.root = tk.Tk()
            
        self.setup_window()
        self.create_widgets()
        self.recent_files = []
    
    def setup_window(self):
        """Setup window to match terminal style"""
        self.root.title("AYRE - File Interface")
        self.root.geometry("700x500")
        self.root.configure(bg="#1a1a1a")  # Same dark background as terminal
        self.root.resizable(True, True)
        
        try:
            self.root.iconbitmap("./ayre_gemini/ayre_icon.ico")
        except:
            pass
        
        self.center_window()
    
    def center_window(self):
        """Center window on screen"""
        self.root.update_idletasks()
        w, h = self.root.winfo_width(), self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (w // 2)
        y = (self.root.winfo_screenheight() // 2) - (h // 2)
        self.root.geometry(f'{w}x{h}+{x}+{y}')
    
    def create_widgets(self):
        """Create terminal-style widgets"""
        # Main container
        main_frame = tk.Frame(self.root, bg="#1a1a1a")
        main_frame.pack(expand=True, fill="both", padx=20, pady=20)
        
        # Header with AYRE ASCII-style title
        header_frame = tk.Frame(main_frame, bg="#1a1a1a")
        header_frame.pack(fill="x", pady=(0, 20))
        
        title_label = tk.Label(
            header_frame,
            text="AYRE FILE INTERFACE",
            bg="#1a1a1a",
            fg="#ff4b4b",  # Same red as terminal
            font=("Consolas", 20, "bold"),
            justify="center"
        )
        title_label.pack()
        
        subtitle_label = tk.Label(
            header_frame,
            text="Your Resonant AI Companion (Gemini)",
            bg="#1a1a1a",
            fg="#ff4b4b",
            font=("Consolas", 10, "italic"),
            justify="center"
        )
        subtitle_label.pack(pady=(5, 0))
        
        # Red border line (like terminal box)
        border_frame = tk.Frame(main_frame, bg="#ff4b4b", height=2)
        border_frame.pack(fill="x", pady=(0, 20))
        
        # Drop area with terminal styling
        drop_container = tk.Frame(main_frame, bg="#ff4b4b", bd=2, relief="solid")
        drop_container.pack(expand=True, fill="both", pady=(0, 20))
        
        self.drop_area = tk.Frame(drop_container, bg="#1a1a1a")
        self.drop_area.pack(expand=True, fill="both", padx=2, pady=2)
        
        # Drop instructions
        drop_text = "📁 DRAG & DROP FILES HERE 📁\n\nSupported file types:\n• Images (jpg, png, gif, etc.)\n• Code files (py, js, html, etc.)\n• Documents (pdf, txt, md, etc.)\n\n👆 Click anywhere to browse files"
        if not HAS_DND:
            drop_text = "📁 CLICK TO BROWSE FILES 📁\n\nSupported file types:\n• Images (jpg, png, gif, etc.)\n• Code files (py, js, html, etc.)\n• Documents (pdf, txt, md, etc.)\n\n(Drag & drop requires: pip install tkinterdnd2)"
        
        self.drop_label = tk.Label(
            self.drop_area,
            text=drop_text,
            bg="#1a1a1a",
            fg="#ffffff",  # White text like terminal
            font=("Consolas", 12),
            justify="center"
        )
        self.drop_label.pack(expand=True, fill="both")
        
        # Enable drag & drop if available
        if HAS_DND:
            self.drop_label.drop_target_register(DND_FILES)
            self.drop_label.dnd_bind('<<Drop>>', self.handle_drop)
        
        self.drop_label.bind("<Button-1>", self.browse_file)
        self.drop_label.bind("<Enter>", self.on_drop_enter)
        self.drop_label.bind("<Leave>", self.on_drop_leave)
        
        # Status section
        status_frame = tk.Frame(main_frame, bg="#1a1a1a")
        status_frame.pack(fill="x", pady=(0, 15))
        
        self.status_label = tk.Label(
            status_frame,
            text="🟢 Ready for file upload",
            bg="#1a1a1a",
            fg="#00ff00",  # Green like terminal
            font=("Consolas", 11, "bold")
        )
        self.status_label.pack()
        
        # Recent files section
        recent_container = tk.Frame(main_frame, bg="#1a1a1a")
        recent_container.pack(fill="x", pady=(0, 15))
        
        recent_header = tk.Label(
            recent_container,
            text="Recent uploads:",
            bg="#1a1a1a",
            fg="#888888",  # Gray like terminal secondary text
            font=("Consolas", 10)
        )
        recent_header.pack(anchor="w")
        
        # Recent files listbox
        listbox_frame = tk.Frame(recent_container, bg="#ff4b4b", bd=1, relief="solid")
        listbox_frame.pack(fill="x", pady=(5, 0))
        
        self.recent_listbox = tk.Listbox(
            listbox_frame,
            bg="#1a1a1a",
            fg="#ffffff",
            font=("Consolas", 9),
            height=3,
            selectbackground="#ff4b4b",
            selectforeground="#ffffff",
            relief="flat",
            bd=0,
            highlightthickness=0
        )
        self.recent_listbox.pack(fill="x", padx=1, pady=1)
        
        # Button section
        button_frame = tk.Frame(main_frame, bg="#1a1a1a")
        button_frame.pack(fill="x")
        
        # Browse button (terminal style)
        self.browse_button = tk.Button(
            button_frame,
            text="📂 Browse Files",
            bg="#ff4b4b",
            fg="#ffffff",
            font=("Consolas", 11, "bold"),
            relief="flat",
            bd=0,
            padx=20,
            pady=8,
            command=self.browse_file,
            activebackground="#cc3333",
            activeforeground="#ffffff",
            cursor="hand2"
        )
        self.browse_button.pack(side="left")
        
        # Clear button
        self.clear_button = tk.Button(
            button_frame,
            text="🗑️ Clear Recent",
            bg="#666666",
            fg="#ffffff",
            font=("Consolas", 11),
            relief="flat",
            bd=0,
            padx=20,
            pady=8,
            command=self.clear_recent,
            activebackground="#888888",
            activeforeground="#ffffff",
            cursor="hand2"
        )
        self.clear_button.pack(side="right")
        
        # Close button
        self.close_button = tk.Button(
            button_frame,
            text="❌ Close",
            bg="#333333",
            fg="#ffffff",
            font=("Consolas", 11),
            relief="flat",
            bd=0,
            padx=20,
            pady=8,
            command=self.close_window,
            activebackground="#555555",
            activeforeground="#ffffff",
            cursor="hand2"
        )
        self.close_button.pack(side="right", padx=(0, 10))
    
    def on_drop_enter(self, event):
        """Highlight drop area on hover"""
        self.drop_area.config(bg="#2a2a2a")
        self.drop_label.config(bg="#2a2a2a", fg="#ff4b4b")
    
    def on_drop_leave(self, event):
        """Remove highlight when not hovering"""
        self.drop_area.config(bg="#1a1a1a")
        self.drop_label.config(bg="#1a1a1a", fg="#ffffff")
    
    def close_window(self):
        """Close the GUI window"""
        self.root.destroy()
    
    def handle_drop(self, event):
        """Handle dropped files"""
        if HAS_DND:
            files = self.root.tk.splitlist(event.data)
            for file_path in files:
                self.process_file(file_path)
    
    def browse_file(self, event=None):
        """Browse for files"""
        file_path = filedialog.askopenfilename(
            title="Select file for Ayre",
            filetypes=[
                ("Images", "*.jpg *.jpeg *.png *.gif *.webp *.bmp"),
                ("Code Files", "*.py *.js *.html *.css *.txt *.md"),
                ("Documents", "*.pdf *.doc *.docx"),
                ("All Files", "*.*")
            ]
        )
        if file_path:
            self.process_file(file_path)
    
    def process_file(self, file_path):
        """Process selected file"""
        filename = Path(file_path).name
        self.update_status(f"🔄 Processing: {filename}", "#ffaa00")
        
        # Add to recent
        if filename not in self.recent_files:
            self.recent_files.append(filename)
            self.recent_listbox.insert(0, filename)
            if len(self.recent_files) > 10:
                self.recent_files.pop()
                self.recent_listbox.delete(tk.END)
        
        # Queue for processing
        self.file_queue.put(("process", file_path))
        self.update_status(f"✅ Uploaded: {filename}", "#00ff00")
    
    def clear_recent(self):
        """Clear recent files"""
        self.recent_files.clear()
        self.recent_listbox.delete(0, tk.END)
        self.update_status("🗑️ Recent files cleared", "#888888")
    
    def update_status(self, message, color):
        """Update status with terminal styling"""
        self.status_label.config(text=message, fg=color)
        # Auto-reset to ready after 3 seconds
        self.root.after(3000, lambda: self.status_label.config(
            text="🟢 Ready for file upload", fg="#00ff00"
        ))

def start_gui(file_queue):
    """Start GUI interface"""
    try:
        gui = AyreGUI(file_queue)
        gui.root.mainloop()
    except Exception as e:
        print(f"GUI Error: {e}")
        if not HAS_DND:
            print("For full drag & drop support, install: pip install tkinterdnd2")
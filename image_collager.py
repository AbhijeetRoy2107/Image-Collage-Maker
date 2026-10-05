
import tkinter as tk
from tkinter import ttk, filedialog, colorchooser, messagebox
from pathlib import Path
from PIL import Image, ImageTk, ImageOps, ImageDraw

SUPPORTED = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif", ".tif", ".tiff"}

class ImageCollager:
    def __init__(self, root):
        self.root = root
        self.root.title("Image Collager")
        self.root.geometry("1200x820")
        self.root.minsize(900, 650)

        self.files = []
        self.images = []
        self.bg = "#ffffff"
        self.preview_photo = None

        self.width_var = tk.IntVar(value=2048)
        self.height_var = tk.IntVar(value=2048)
        self.cols_var = tk.IntVar(value=8)
        self.gap_var = tk.IntVar(value=8)
        self.margin_var = tk.IntVar(value=0)
        self.fit_var = tk.StringVar(value="Contain")
        self.bg_var = tk.StringVar(value=self.bg)
        self.auto_cols_var = tk.BooleanVar(value=True)

        self._build_ui()
        self._refresh()

    def _build_ui(self):
        style = ttk.Style()
        try:
            style.theme_use("vista")
        except tk.TclError:
            pass

        top = ttk.Frame(self.root, padding=10)
        top.pack(fill="x")

        # Canvas size
        size_box = ttk.LabelFrame(top, text="Output size (pixels)", padding=8)
        size_box.pack(side="left", fill="y", padx=(0, 8))

        ttk.Label(size_box, text="Width").grid(row=0, column=0, padx=4)
        ttk.Spinbox(size_box, from_=64, to=20000, textvariable=self.width_var,
                    width=8, command=self._refresh).grid(row=0, column=1, padx=4)
        ttk.Label(size_box, text="Height").grid(row=0, column=2, padx=4)
        ttk.Spinbox(size_box, from_=64, to=20000, textvariable=self.height_var,
                    width=8, command=self._refresh).grid(row=0, column=3, padx=4)

        # Layout
        layout_box = ttk.LabelFrame(top, text="Layout", padding=8)
        layout_box.pack(side="left", fill="y", padx=8)

        ttk.Label(layout_box, text="Columns").grid(row=0, column=0, padx=4)
        ttk.Spinbox(layout_box, from_=1, to=100, textvariable=self.cols_var,
                    width=5, command=self._refresh).grid(row=0, column=1, padx=4)
        ttk.Label(layout_box, text="Gap").grid(row=0, column=2, padx=4)
        ttk.Spinbox(layout_box, from_=0, to=500, textvariable=self.gap_var,
                    width=5, command=self._refresh).grid(row=0, column=3, padx=4)
        ttk.Label(layout_box, text="Margin").grid(row=0, column=4, padx=4)
        ttk.Spinbox(layout_box, from_=0, to=1000, textvariable=self.margin_var,
                    width=6, command=self._refresh).grid(row=0, column=5, padx=4)

        # Image behavior
        behavior_box = ttk.LabelFrame(top, text="Images", padding=8)
        behavior_box.pack(side="left", fill="y", padx=8)

        ttk.Label(behavior_box, text="Fit").grid(row=0, column=0, padx=4)
        fit = ttk.Combobox(behavior_box, textvariable=self.fit_var,
                           values=["Contain", "Cover", "Stretch"], state="readonly", width=9)
        fit.grid(row=0, column=1, padx=4)
        fit.bind("<<ComboboxSelected>>", lambda e: self._refresh())

        # Background
        bg_box = ttk.LabelFrame(top, text="Background", padding=8)
        bg_box.pack(side="left", fill="y", padx=8)
        ttk.Button(bg_box, text="Choose", command=self._choose_bg).pack(side="left")
        self.bg_preview = tk.Label(bg_box, width=3, bg=self.bg, relief="sunken")
        self.bg_preview.pack(side="left", padx=6)

        # Buttons
        buttons = ttk.Frame(self.root, padding=(10, 0, 10, 8))
        buttons.pack(fill="x")
        ttk.Button(buttons, text="Add Images", command=self._add_images).pack(side="left", padx=(0, 6))
        ttk.Button(buttons, text="Add Folder", command=self._add_folder).pack(side="left", padx=6)
        ttk.Button(buttons, text="Remove Selected", command=self._remove_selected).pack(side="left", padx=6)
        ttk.Button(buttons, text="Clear All", command=self._clear).pack(side="left", padx=6)
        ttk.Button(buttons, text="Auto Columns", command=self._auto_columns).pack(side="left", padx=6)
        ttk.Button(buttons, text="Export PNG", command=lambda: self._export("PNG")).pack(side="right", padx=4)
        ttk.Button(buttons, text="Export JPEG", command=lambda: self._export("JPEG")).pack(side="right", padx=4)

        main = ttk.Panedwindow(self.root, orient="horizontal")
        main.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        left = ttk.Frame(main, padding=5)
        right = ttk.Frame(main, padding=5)
        main.add(left, weight=0)
        main.add(right, weight=1)

        ttk.Label(left, text="Images").pack(anchor="w")
        self.listbox = tk.Listbox(left, width=34, selectmode=tk.EXTENDED)
        self.listbox.pack(fill="both", expand=True, pady=(5, 0))
        self.listbox.bind("<<ListboxSelect>>", lambda e: self._draw_preview())

        self.count_label = ttk.Label(left, text="0 images")
        self.count_label.pack(anchor="w", pady=5)

        ttk.Label(right, text="Preview").pack(anchor="w")
        preview_frame = ttk.Frame(right)
        preview_frame.pack(fill="both", expand=True, pady=(5, 0))

        self.canvas = tk.Canvas(preview_frame, bg="#dddddd", highlightthickness=0)
        self.hbar = ttk.Scrollbar(preview_frame, orient="horizontal", command=self.canvas.xview)
        self.vbar = ttk.Scrollbar(preview_frame, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(xscrollcommand=self.hbar.set, yscrollcommand=self.vbar.set)
        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.vbar.grid(row=0, column=1, sticky="ns")
        self.hbar.grid(row=1, column=0, sticky="ew")
        preview_frame.rowconfigure(0, weight=1)
        preview_frame.columnconfigure(0, weight=1)

        for var in (self.width_var, self.height_var, self.cols_var, self.gap_var, self.margin_var):
            var.trace_add("write", lambda *_: self._refresh())

        self.root.bind("<Control-o>", lambda e: self._add_images())
        self.root.bind("<Control-e>", lambda e: self._export("PNG"))
        self.root.bind("<Delete>", lambda e: self._remove_selected())

    def _choose_bg(self):
        color = colorchooser.askcolor(color=self.bg, title="Choose background")[1]
        if color:
            self.bg = color
            self.bg_var.set(color)
            self.bg_preview.configure(bg=color)
            self._draw_preview()

    def _add_images(self):
        paths = filedialog.askopenfilenames(
            title="Select images",
            filetypes=[("Images", "*.png *.jpg *.jpeg *.webp *.bmp *.gif *.tif *.tiff"),
                       ("All files", "*.*")]
        )
        self._add_paths(paths)

    def _add_folder(self):
        folder = filedialog.askdirectory(title="Select image folder")
        if not folder:
            return
        paths = sorted(str(p) for p in Path(folder).iterdir()
                       if p.is_file() and p.suffix.lower() in SUPPORTED)
        self._add_paths(paths)

    def _add_paths(self, paths):
        added = 0
        existing = set(self.files)
        for p in paths:
            p = str(Path(p))
            if p not in existing:
                try:
                    im = Image.open(p)
                    im.load()
                    self.files.append(p)
                    self.images.append(im.convert("RGBA"))
                    self.listbox.insert("end", Path(p).name)
                    existing.add(p)
                    added += 1
                except Exception:
                    pass
        self._update_count()
        self._refresh()
        if added == 0 and paths:
            messagebox.showwarning("No images added", "The selected files could not be opened as images.")

    def _remove_selected(self):
        selected = list(self.listbox.curselection())
        if not selected:
            return
        for i in reversed(selected):
            self.listbox.delete(i)
            self.files.pop(i)
            self.images.pop(i)
        self._update_count()
        self._refresh()

    def _clear(self):
        self.files.clear()
        self.images.clear()
        self.listbox.delete(0, "end")
        self._update_count()
        self._refresh()

    def _update_count(self):
        n = len(self.files)
        self.count_label.config(text=f"{n} image{'s' if n != 1 else ''}")

    def _auto_columns(self):
        n = max(1, len(self.images))
        # Reasonable grid for large collections: roughly square.
        import math
        cols = max(1, math.ceil(math.sqrt(n)))
        self.cols_var.set(cols)
        self._refresh()

    def _layout(self):
        n = len(self.images)
        if n == 0:
            return []
        cols = max(1, min(int(self.cols_var.get()), n))
        rows = (n + cols - 1) // cols
        W = max(64, int(self.width_var.get()))
        H = max(64, int(self.height_var.get()))
        gap = max(0, int(self.gap_var.get()))
        margin = max(0, int(self.margin_var.get()))

        usable_w = max(1, W - 2 * margin - gap * (cols - 1))
        usable_h = max(1, H - 2 * margin - gap * (rows - 1))
        cell_w = usable_w / cols
        cell_h = usable_h / rows

        result = []
        for i in range(n):
            r, c = divmod(i, cols)
            x = margin + c * (cell_w + gap)
            y = margin + r * (cell_h + gap)
            result.append((int(round(x)), int(round(y)),
                           max(1, int(round(cell_w))), max(1, int(round(cell_h)))))
        return result

    def _place(self, im, size):
        cw, ch = size
        mode = self.fit_var.get()
        if mode == "Stretch":
            return im.resize((cw, ch), Image.Resampling.LANCZOS)
        if mode == "Cover":
            return ImageOps.fit(im, (cw, ch), method=Image.Resampling.LANCZOS, centering=(0.5, 0.5))
        # Contain
        copy = im.copy()
        copy.thumbnail((cw, ch), Image.Resampling.LANCZOS)
        out = Image.new("RGBA", (cw, ch), self.bg)
        out.paste(copy, ((cw - copy.width)//2, (ch - copy.height)//2), copy)
        return out

    def _render(self, max_preview=None):
        W = max(64, int(self.width_var.get()))
        H = max(64, int(self.height_var.get()))
        positions = self._layout()

        out = Image.new("RGBA", (W, H), self.bg)
        for im, (x, y, cw, ch) in zip(self.images, positions):
            tile = self._place(im, (cw, ch))
            out.alpha_composite(tile, (x, y))
        return out

    def _refresh(self):
        try:
            self._draw_preview()
        except Exception:
            pass

    def _draw_preview(self):
        self.canvas.delete("all")
        if not self.images:
            self.canvas.create_text(300, 200, text="Add images to begin",
                                    fill="#555555", font=("Segoe UI", 16))
            self.canvas.configure(scrollregion=(0, 0, 700, 500))
            return

        try:
            out = self._render()
        except Exception:
            return

        # Fit the full collage into a useful preview size while retaining its aspect ratio.
        max_w, max_h = 900, 650
        scale = min(max_w / out.width, max_h / out.height, 1.0)
        pw, ph = max(1, int(out.width * scale)), max(1, int(out.height * scale))
        preview = out.resize((pw, ph), Image.Resampling.LANCZOS)
        self.preview_photo = ImageTk.PhotoImage(preview)

        self.canvas.create_image(10, 10, image=self.preview_photo, anchor="nw")
        self.canvas.configure(scrollregion=(0, 0, pw + 20, ph + 20))

    def _export(self, fmt):
        if not self.images:
            messagebox.showinfo("Nothing to export", "Add some images first.")
            return

        ext = ".png" if fmt == "PNG" else ".jpg"
        path = filedialog.asksaveasfilename(
            title="Save collage",
            defaultextension=ext,
            filetypes=[(fmt, f"*{ext}")]
        )
        if not path:
            return

        try:
            out = self._render()
            if fmt == "JPEG":
                out = out.convert("RGB")
                out.save(path, "JPEG", quality=95, subsampling=0, optimize=True)
            else:
                out.save(path, "PNG", optimize=True)
            messagebox.showinfo(
                "Export complete",
                f"Saved:\n{path}\n\nSize: {out.width} × {out.height} px\nImages: {len(self.images)}"
            )
        except Exception as e:
            messagebox.showerror("Export failed", str(e))

if __name__ == "__main__":
    root = tk.Tk()
    app = ImageCollager(root)
    root.mainloop()

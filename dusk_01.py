import cv2
import tkinter as tk
from PIL import Image, ImageTk

# ── CONFIG ─────────────────────────────────────────────
CAMERA_INDEX = 0        # Change this if it picks the wrong camera (try 1, 2, etc.)
START_WIDTH  = 960
START_HEIGHT = 540
START_X      = 100
START_Y      = 100
# ───────────────────────────────────────────────────────

class CamOverlay:
    def __init__(self):
        self.root = tk.Tk()
        self.root.overrideredirect(True)          # borderless
        self.root.attributes('-topmost', True)    # always on top
        self.root.geometry(f'{START_WIDTH}x{START_HEIGHT}+{START_X}+{START_Y}')
        self.root.configure(bg='black')

        self.canvas = tk.Canvas(self.root, bg='black', highlightthickness=0, cursor='fleur')
        self.canvas.pack(fill='both', expand=True)

        self.cap = cv2.VideoCapture(CAMERA_INDEX, cv2.CAP_DSHOW)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)

        if not self.cap.isOpened():
            print(f"[ERROR] Could not open camera index {CAMERA_INDEX}. Try changing CAMERA_INDEX.")
            self.root.destroy()
            return

        # ── Dragging ──
        self._drag_x = 0
        self._drag_y = 0
        self.canvas.bind('<Button-1>',   self.drag_start)
        self.canvas.bind('<B1-Motion>',  self.drag_move)

        # ── Resize by scroll wheel ──
        self.canvas.bind('<MouseWheel>', self.scroll_resize)

        # ── Right-click menu ──
        self.menu = tk.Menu(self.root, tearoff=0)
        self.menu.add_command(label='Toggle Always on Top', command=self.toggle_topmost)
        self.menu.add_separator()
        self.menu.add_command(label='Close',                command=self.quit)
        self.canvas.bind('<Button-3>', self.show_menu)

        # ── Resize grip (bottom-right corner) ──
        self.grip = tk.Label(self.root, text='⤡', bg='#333', fg='white',
                             font=('Arial', 10), cursor='size_nw_se')
        self.grip.place(relx=1.0, rely=1.0, anchor='se')
        self.grip.bind('<Button-1>',  self.resize_start)
        self.grip.bind('<B1-Motion>', self.resize_move)

        self._topmost = True
        self.update_frame()
        self.root.mainloop()

    # ── Frame loop ────────────────────────────────────────
    def update_frame(self):
        ret, frame = self.cap.read()
        if ret:
            w = self.root.winfo_width()
            h = self.root.winfo_height()
            if w > 0 and h > 0:
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                frame = cv2.resize(frame, (w, h), interpolation=cv2.INTER_LINEAR)
                img   = Image.fromarray(frame)
                imgtk = ImageTk.PhotoImage(image=img)
                self.canvas.imgtk = imgtk          # keep reference
                self.canvas.create_image(0, 0, anchor='nw', image=imgtk)
        self.root.after(16, self.update_frame)     # ~60 fps

    # ── Drag ─────────────────────────────────────────────
    def drag_start(self, e):
        self._drag_x, self._drag_y = e.x, e.y

    def drag_move(self, e):
        x = self.root.winfo_x() + e.x - self._drag_x
        y = self.root.winfo_y() + e.y - self._drag_y
        self.root.geometry(f'+{x}+{y}')

    # ── Scroll resize ─────────────────────────────────────
    def scroll_resize(self, e):
        factor = 1.1 if e.delta > 0 else 0.9
        w = max(320, int(self.root.winfo_width()  * factor))
        h = max(180, int(self.root.winfo_height() * factor))
        # Keep 16:9
        h = int(w * 9 / 16)
        self.root.geometry(f'{w}x{h}')

    # ── Corner resize ─────────────────────────────────────
    def resize_start(self, e):
        self._rx = e.x_root
        self._ry = e.y_root
        self._rw = self.root.winfo_width()
        self._rh = self.root.winfo_height()

    def resize_move(self, e):
        dw = e.x_root - self._rx
        w  = max(320, self._rw + dw)
        h  = int(w * 9 / 16)
        self.root.geometry(f'{w}x{h}')

    # ── Right-click menu ──────────────────────────────────
    def show_menu(self, e):
        self.menu.tk_popup(e.x_root, e.y_root)

    def toggle_topmost(self):
        self._topmost = not self._topmost
        self.root.attributes('-topmost', self._topmost)

    def quit(self):
        self.cap.release()
        self.root.destroy()


if __name__ == '__main__':
    CamOverlay()

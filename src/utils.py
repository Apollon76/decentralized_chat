import threading
import time
import tkinter


class Daemon:
    def __init__(self, name=None, target=None, timeout=0.5):
        self.name = name
        self._target = target
        self._stopped = threading.Event()
        self._stopped.set()
        self.timeout = timeout

    def run(self):
        if not self._stopped.is_set():
            return
        self._stopped.clear()
        threading.Thread(name=self.name, target=self._updating).start()

    def _updating(self):
        while not self._stopped.wait(self.timeout):
            self._target()

    def stop(self):
        self._stopped.set()


class SafeSet(set):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._lock = threading.RLock()

    def add(self, *args, **kwargs):
        with self._lock:
            super().add(*args, **kwargs)

    def remove(self, *args, **kwargs):
        with self._lock:
            super().remove(*args, **kwargs)

    def __contains__(self, item):
        with self._lock:
            return super().__contains__(item)


class VerticalScrolledFrame(tkinter.Frame):
    def __init__(self, parent, **kw):
        tkinter.Frame.__init__(self, parent, **kw)

        vscrollbar = tkinter.Scrollbar(self, orient=tkinter.VERTICAL)
        vscrollbar.pack(fill=tkinter.Y, side=tkinter.RIGHT, expand=tkinter.FALSE)
        canvas = tkinter.Canvas(self, bd=0, highlightthickness=0, yscrollcommand=vscrollbar.set)
        canvas.pack(side=tkinter.LEFT, fill=tkinter.BOTH, expand=tkinter.TRUE)
        vscrollbar.config(command=canvas.yview)

        canvas.xview_moveto(0)
        canvas.yview_moveto(0)

        self.interior = interior = tkinter.Frame(canvas)
        interior_id = canvas.create_window(0, 0, window=interior, anchor=tkinter.NW)

        def _configure_interior(event):
            size = (interior.winfo_reqwidth(), interior.winfo_reqheight())
            canvas.config(scrollregion="0 0 %s %s" % size)
            if interior.winfo_reqwidth() != canvas.winfo_width():
                canvas.config(width=interior.winfo_reqwidth())
        interior.bind('<Configure>', _configure_interior)

        def _configure_canvas(event):
            if interior.winfo_reqwidth() != canvas.winfo_width():
                canvas.itemconfigure(interior_id, width=canvas.winfo_width())
        canvas.bind('<Configure>', _configure_canvas)

if __name__ == '__main__':
    class SampleApp(tkinter.Tk):
        def __init__(self, *args, **kwargs):
            root = tkinter.Tk.__init__(self, *args, **kwargs)
            self.frame = VerticalScrolledFrame(root)
            self.frame.pack()
            self.label = tkinter.Label(text="Shrink the window to activate the scrollbar.")
            self.label.pack()
            buttons = []
            for i in range(10):
                buttons.append(tkinter.Button(self.frame.interior, text="Button " + str(i)))
                buttons[-1].pack()

    app = SampleApp()
    app.mainloop()
    s = SafeSet()
    s.add(1)
    s.add(2)
    s.remove(1)
    print(s)

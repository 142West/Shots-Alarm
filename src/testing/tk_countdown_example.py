import sys
import time

version = sys.hexversion
if 0x03000000 <= version < 0x03010000 :
    import tkinter
    import ttk
elif version >= 0x03010000:
    import tkinter
    import tkinter.ttk as ttk
else: # version < 0x03000000
    import Tkinter as tkinter
    import ttk

now = time.time #NOTE: subject to time adjustments

class Countdown:
    "Show countdown and call `callback` in `delay` seconds unless cancelled."
    def __init__(self, root, delay):
        self.frame = ttk.Frame(root, padding="5 5")
        self.frame.master.attributes('-fullscreen',True)
        self.frame.master = root #XXX
        self.seconds_var = tkinter.StringVar()
        self.update_id = None
        
        ttk.Label(self.frame, textvariable=self.seconds_var, font=("Courier", 100, "bold")).grid(row=1, column=1)
        ttk.Button(self.frame, text='Cancel', command=self.cancel).grid(row=2, column=1, sticky="s")
        self.frame.grid_rowconfigure(1, weight=1)
        self.frame.grid_columnconfigure(1, weight=1)
        self.frame.grid_rowconfigure(1, minsize=700)
        self.frame.grid()
        self.frame.master.protocol("WM_DELETE_WINDOW", self.cancel)
        self.update(now() + delay)

        print(self.frame.grid_size())

    def update(self, end_time):
        """Update countdown or call the callback and exit."""
        if end_time <= now():
            print("END COUNTDOWN")
            self.frame.master.destroy()
        else:
            self.seconds_var.set('SHOTS IN: %.0f' % (end_time - now()))
            self.update_id = self.frame.after(100, self.update, end_time)

    def cancel(self):
        """Cancel callback, exit."""
        if self.update_id is not None:
            self.frame.after_cancel(self.update_id)
        self.frame.master.destroy()

def durr():
    print("TEST")

if __name__=="__main__":
    import subprocess

    root = tkinter.Tk()
    root.grid_rowconfigure(0, weight=1)
    root.grid_columnconfigure(0, weight=1)
    Countdown(root, 59)
    root.mainloop()

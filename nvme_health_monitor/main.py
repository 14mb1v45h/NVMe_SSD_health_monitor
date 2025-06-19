import tkinter as tk
from nvme_health_monitor.monitor import NVMeHealthMonitor

if __name__ == "__main__":
    root = tk.Tk()
    app = NVMeHealthMonitor(root)
    root.protocol("WM_DELETE_WINDOW", app.cleanup)
    root.mainloop()
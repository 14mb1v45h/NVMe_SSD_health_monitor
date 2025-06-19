import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
from datetime import datetime
from .utils import get_nvme_devices, get_nvme_metrics, log_metrics_to_db
from .logging_config import setup_logging
import logging

class NVMeHealthMonitor:
    def __init__(self, root, db_path="nvme_health.db", update_interval=30):
        self.root = root
        self.root.title("NVMe SSD Health Monitor")
        self.root.geometry("600x400")
        self.running = True
        self.db_path = db_path
        self.update_interval = update_interval
        self.logger = setup_logging()

        self.setup_gui()
        self.update_thread = threading.Thread(target=self.update_metrics, daemon=True)
        self.update_thread.start()

    def setup_gui(self):
        """Set up the Tkinter GUI."""
        self.logger.info("Initializing GUI")
        tk.Label(self.root, text="Select NVMe Device:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.device_var = tk.StringVar()
        self.device_combo = ttk.Combobox(self.root, textvariable=self.device_var, state="readonly")
        self.device_combo.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        self.populate_devices()
        self.device_combo.bind("<<ComboboxSelected>>", self.on_device_select)

        self.metrics_frame = ttk.LabelFrame(self.root, text="NVMe Health Metrics")
        self.metrics_frame.grid(row=1, column=0, columnspan=2, padx=10, pady=10, sticky="nsew")

        tk.Label(self.metrics_frame, text="Temperature:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.temp_label = tk.Label(self.metrics_frame, text="N/A", font=("Arial", 12))
        self.temp_label.grid(row=0, column=1, padx=5, pady=5, sticky="w")

        tk.Label(self.metrics_frame, text="Wear Level (% Used):").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.wear_label = tk.Label(self.metrics_frame, text="N/A", font=("Arial", 12))
        self.wear_label.grid(row=1, column=1, padx=5, pady=5, sticky="w")

        tk.Label(self.metrics_frame, text="Critical Warning:").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.warning_label = tk.Label(self.metrics_frame, text="N/A", font=("Arial", 12))
        self.warning_label.grid(row=2, column=1, padx=5, pady=5, sticky="w")

        tk.Label(self.metrics_frame, text="Last Updated:").grid(row=3, column=0, padx=5, pady=5, sticky="w")
        self.time_label = tk.Label(self.metrics_frame, text="N/A", font=("Arial", 10))
        self.time_label.grid(row=3, column=1, padx=5, pady=5, sticky="w")

        self.refresh_button = tk.Button(self.root, text="Refresh Now", command=self.manual_refresh)
        self.refresh_button.grid(row=2, column=0, padx=5, pady=5, sticky="w")

        self.history_button = tk.Button(self.root, text="View History", command=self.show_history)
        self.history_button.grid(row=2, column=1, padx=5, pady=5, sticky="w")

    def populate_devices(self):
        """Populate combobox with NVMe devices."""
        try:
            devices = get_nvme_devices()
            self.device_combo["values"] = devices
            if devices:
                self.device_var.set(devices[0])
                self.on_device_select(None)
            else:
                self.logger.warning("No NVMe devices found")
                messagebox.showwarning("Warning", "No NVMe devices detected")
        except Exception as e:
            self.logger.error(f"Error populating devices: {e}")
            messagebox.showerror("Error", f"Failed to list NVMe devices: {e}")

    def on_device_select(self, event):
        """Handle device selection."""
        self.logger.info(f"Selected device: {self.device_var.get()}")
        self.manual_refresh()

    def update_metrics(self):
        """Update metrics in background."""
        self.logger.info("Starting background metrics update")
        while self.running:
            device = self.device_var.get()
            if device:
                metrics = get_nvme_metrics(device)
                if metrics:
                    self.root.after(0, self.update_gui, metrics)
                    log_metrics_to_db(self.db_path, metrics)
                else:
                    self.logger.error(f"Failed to fetch metrics for {device}")
                    self.root.after(0, self.show_error, "Failed to fetch metrics")
            time.sleep(self.update_interval)

    def manual_refresh(self):
        """Manually refresh metrics."""
        device = self.device_var.get()
        self.logger.info(f"Manual refresh for device: {device}")
        if device:
            metrics = get_nvme_metrics(device)
            if metrics:
                self.update_gui(metrics)
                log_metrics_to_db(self.db_path, metrics)
            else:
                self.logger.error(f"Manual refresh failed for {device}")
                self.show_error("Failed to fetch metrics")

    def update_gui(self, metrics):
        """Update GUI labels."""
        self.logger.debug(f"Updating GUI with metrics: {metrics}")
        self.temp_label.config(text=f"{metrics['temperature']} °C")
        self.wear_label.config(text=f"{metrics['wear_level']}%")
        self.warning_label.config(text=metrics['critical_warning'])
        self.time_label.config(text=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    def show_error(self, message):
        """Show error message."""
        self.logger.error(f"Displaying error: {message}")
        messagebox.showerror("Error", message)

    def show_history(self):
        """Display historical data."""
        self.logger.info("Opening history window")
        history_window = tk.Toplevel(self.root)
        history_window.title("NVMe Health History")
        history_window.geometry("600x400")

        columns = ("Timestamp", "Temperature", "Wear Level", "Critical Warning")
        tree = ttk.Treeview(history_window, columns=columns, show="headings")
        tree.heading("Timestamp", text="Timestamp")
        tree.heading("Temperature", text="Temperature (°C)")
        tree.heading("Wear Level", text="Wear Level (%)")
        tree.heading("Critical Warning", text="Critical Warning")
        tree.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        scrollbar = ttk.Scrollbar(history_window, orient="vertical", command=tree.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        tree.configure(yscrollcommand=scrollbar.set)

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT timestamp, temperature, wear_level, critical_warning FROM nvme_health ORDER BY timestamp DESC")
            for row in cursor.fetchall():
                tree.insert("", "end", values=row)
            conn.close()
        except sqlite3.Error as e:
            self.logger.error(f"Error fetching history: {e}")
            messagebox.showerror("Error", f"Failed to load history: {e}")

    def cleanup(self):
        """Clean up resources."""
        self.logger.info("Cleaning up resources")
        self.running = False
        self.root.destroy()

import subprocess
import json
import sqlite3
from datetime import datetime

def get_nvme_devices():
    """Fetch list of NVMe devices."""
    try:
        result = subprocess.run(["nvme", "list", "-o", "json"], capture_output=True, text=True, check=True)
        devices = json.loads(result.stdout).get("Devices", [])
        return [device["DevicePath"] for device in devices]
    except (subprocess.CalledProcessError, json.JSONDecodeError):
        return []

def get_nvme_metrics(device):
    """Fetch NVMe metrics for a device."""
    try:
        result = subprocess.run(
            ["nvme", "smart-log", device, "-o", "json"],
            capture_output=True,
            text=True,
            check=True
        )
        smart_log = json.loads(result.stdout)
        temperature = int(smart_log.get("temperature", 0)) - 273  # Kelvin to Celsius
        wear_level = int(smart_log.get("percentage_used", 0))
        critical_warning = "Yes" if smart_log.get("critical_warning", "0") != "0" else "None"
        return {
            "temperature": temperature,
            "wear_level": wear_level,
            "critical_warning": critical_warning
        }
    except (subprocess.CalledProcessError, json.JSONDecodeError, ValueError):
        return None

def log_metrics_to_db(db_path, metrics):
    """Log metrics to SQLite database."""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS nvme_health (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                temperature INTEGER,
                wear_level INTEGER,
                critical_warning TEXT
            )
        """)
        cursor.execute("""
            INSERT INTO nvme_health (timestamp, temperature, wear_level, critical_warning)
            VALUES (?, ?, ?, ?)
        """, (
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            metrics["temperature"],
            metrics["wear_level"],
            metrics["critical_warning"]
        ))
        conn.commit()
        conn.close()
    except sqlite3.Error:
        pass
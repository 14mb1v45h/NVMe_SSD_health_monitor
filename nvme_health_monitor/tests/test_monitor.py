import pytest
import tkinter as tk
from unittest.mock import patch, MagicMock
from nvme_health_monitor.monitor import NVMeHealthMonitor

@pytest.fixture
def root():
    root = tk.Tk()
    yield root
    root.destroy()

@pytest.fixture
def monitor(root, tmp_path):
    db_path = tmp_path / "test.db"
    return NVMeHealthMonitor(root, db_path=str(db_path), update_interval=0.1)

class TestNVMeHealthMonitor:
    def test_init(self, monitor):
        assert monitor.root.title() == "NVMe SSD Health Monitor"
        assert monitor.running is True
        assert isinstance(monitor.logger, logging.Logger)

    @patch("nvme_health_monitor.monitor.get_nvme_devices")
    def test_populate_devices(self, mock_get_devices, monitor):
        mock_get_devices.return_value = ["/dev/nvme0", "/dev/nvme1"]
        monitor.populate_devices()
        assert monitor.device_combo["values"] == ("/dev/nvme0", "/dev/nvme1")
        assert monitor.device_var.get() == "/dev/nvme0"

    @patch("nvme_health_monitor.monitor.get_nvme_devices")
    def test_populate_devices_empty(self, mock_get_devices, monitor):
        mock_get_devices.return_value = []
        with patch("nvme_health_monitor.monitor.messagebox.showwarning") as mock_warning:
            monitor.populate_devices()
            assert monitor.device_combo["values"] == ()
            mock_warning.assert_called_once()

    @patch("nvme_health_monitor.monitor.get_nvme_metrics")
    @patch("nvme_health_monitor.monitor.log_metrics_to_db")
    def test_manual_refresh_success(self, mock_log, mock_get_metrics, monitor):
        mock_get_metrics.return_value = {
            "temperature": 35,
            "wear_level": 10,
            "critical_warning": "None"
        }
        monitor.device_var.set("/dev/nvme0")
        monitor.manual_refresh()
        assert monitor.temp_label.cget("text") == "35 °C"
        assert monitor.wear_label.cget("text") == "10%"
        assert mock_log.called

    @patch("nvme_health_monitor.monitor.get_nvme_metrics")
    def test_manual_refresh_failure(self, mock_get_metrics, monitor):
        mock_get_metrics.return_value = None
        monitor.device_var.set("/dev/nvme0")
        with patch("nvme_health_monitor.monitor.messagebox.showerror") as mock_error:
            monitor.manual_refresh()
            mock_error.assert_called_once_with("Error", "Failed to fetch metrics")
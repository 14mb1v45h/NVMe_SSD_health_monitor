import pytest
import sqlite3
from unittest.mock import patch, MagicMock
from nvme_health_monitor.utils import get_nvme_devices, get_nvme_metrics, log_metrics_to_db

class TestUtils:
    @patch("subprocess.run")
    def test_get_nvme_devices_success(self, mock_run):
        mock_run.return_value = MagicMock(stdout='{"Devices":[{"DevicePath":"/dev/nvme0"}]}')
        devices = get_nvme_devices()
        assert devices == ["/dev/nvme0"]

    @patch("subprocess.run")
    def test_get_nvme_devices_failure(self, mock_run):
        mock_run.side_effect = subprocess.CalledProcessError(1, "nvme list")
        devices = get_nvme_devices()
        assert devices == []

    @patch("subprocess.run")
    def test_get_nvme_metrics_success(self, mock_run):
        mock_run.return_value = MagicMock(stdout='{"temperature":308,"percentage_used":5,"critical_warning":"0"}')
        metrics = get_nvme_metrics("/dev/nvme0")
        assert metrics == {
            "temperature": 35,
            "wear_level": 5,
            "critical_warning": "None"
        }

    @patch("subprocess.run")
    def test_get_nvme_metrics_failure(self, mock_run):
        mock_run.side_effect = subprocess.CalledProcessError(1, "nvme smart-log")
        metrics = get_nvme_metrics("/dev/nvme0")
        assert metrics is None

    def test_log_metrics_to_db(self, tmp_path):
        db_path = tmp_path / "test.db"
        metrics = {
            "temperature": 35,
            "wear_level": 10,
            "critical_warning": "None"
        }
        log_metrics_to_db(str(db_path), metrics)
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        cursor.execute("SELECT temperature, wear_level, critical_warning FROM nvme_health")
        result = cursor.fetchone()
        assert result == (35, 10, "None")
        conn.close()

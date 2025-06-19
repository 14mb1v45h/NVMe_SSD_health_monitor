# NVMe SSD Health Monitor

A Python application to monitor NVMe SSD health using Tkinter, nvme-cli, and SQLite. Displays real-time temperature, wear level, and critical warnings, with historical data logging.

## Features
- Select NVMe devices from a dropdown.
- Real-time metrics updated every 30 seconds.
- SQLite database for historical data.
- View history in a scrollable table.
- Logging to file and console.
- Pytest test suite for reliability.

## Prerequisites
- Python 3.7+
- nvme-cli (`sudo apt-get install nvme-cli` on Ubuntu)
- Dependencies: `pip install -r requirements.txt`

## Installation
1. Clone or download the project.
2. Install dependencies: `pip install -r requirements.txt`
3. Run the app: `python -m nvme_health_monitor.main`

## Running Tests
1. Install pytest: `pip install pytest`
2. Run tests: `pytest nvme_health_monitor/tests -v`

## Project Structure
- `main.py`: Application entry point.
- `monitor.py`: Core monitoring and GUI logic.
- `utils.py`: Utility functions for nvme-cli and database.
- `logging_config.py`: Logging setup.
- `tests/`: Pytest test suite.

## Packaging for Sale
- Create executable: `pip install pyinstaller; pyinstaller --onefile nvme_health_monitor/main.py`
- Zip the executable, README, and demo video for Gumroad.
- For SaaS, host on Heroku with a Flask API.

## License
MIT License
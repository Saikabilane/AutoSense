# AutoSense — Predictive Vehicle Health Monitoring

AutoSense is a Python prototype for vehicle-health monitoring that combines engine and battery diagnostic models with analytics and scheduling components. It reads telemetry/inference data from CSV files, applies saved machine-learning models, and coordinates diagnostic results with an analytics agent.

## Features
- Engine diagnostics based on engine RPM, lubricant/fuel/coolant pressures and temperatures.
- Battery diagnostics using voltage, current, temperature, motor speed and estimated state of charge, plus derived features.
- Saved model artifacts and label encoders for inference.
- Analytics and diagnostic agents, a scheduler, and a dashboard entry point.
- CSV inputs and service-calendar data for experimentation.

## Main files
- `main_runner.py` — coordinates engine and battery diagnostic runs.
- `diagnostic_agent.py` — diagnostic inference logic.
- `analytics_agent.py` — analysis/decision support.
- `scheduler_agent.py` — scheduling-related functionality.
- `dashboard.py` — dashboard interface.
- `EngineRF.joblib`, `BatteryRF.joblib` and matching `*LE.joblib` files — saved model/label-encoder artifacts.
- `engine_inference.csv`, `battery_inference.csv`, `telemetry.csv`, `AutoSense_ServiceCalendar.csv` — input and supporting data.
- `requirements.txt` — Python dependencies.

## Setup
```bash
git clone https://github.com/Saikabilane/AutoSense.git
cd AutoSense
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
python -m pip install -r requirements.txt
```

Ensure the expected CSV files and model artifacts are present in the working directory. Run the diagnostic workflow with:
```bash
python main_runner.py
```
Inspect `dashboard.py` for the dashboard's intended launch command and configuration.

## Safety and limitations
This is an experimental decision-support project, not a certified automotive diagnostic system. Model outputs can be wrong; validate them against real measurements and qualified technicians before taking maintenance or safety-critical action. Only load trusted `.joblib` artifacts, since deserializing untrusted files can execute code.

## License
No license file is currently included. Contact the repository owner for reuse permission.

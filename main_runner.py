import os
import time
from diagnostic_agent import DiagnosticAgent
from analytics_agent import DataAnalystAgent

ENGINE_CSV = "engine_inference.csv"
BATTERY_CSV = "battery_inference.csv"

ENGINE_FEATS = ["Engine rpm", "Lub oil pressure", "Fuel pressure", "Coolant pressure", "lub oil temp", "Coolant temp"]
BATTERY_RAW = ["Voltage (V)", "Current (A)", "Temperature (°C)", "Motor Speed (RPM)", "Estimated SOC (%)"]
BATTERY_FINAL = BATTERY_RAW + ["Power_Watts", "Internal_Res_Proxy", "Temp_Stress"]


def module_1():
    analyst = DataAnalystAgent(service_threshold=5000)

    engine_diag = DiagnosticAgent(
        "ENGINE",
        "EngineRF.joblib",
        "EngineLE.joblib",
        ENGINE_FEATS,
        analyst,
        base_dir="",
        verbose=False,
        conservative_on_error=True
    )

    battery_diag = DiagnosticAgent(
        "BATTERY",
        "BatteryRF.joblib",
        "BatteryLE.joblib",
        BATTERY_FINAL,
        analyst,
        base_dir="",
        verbose=False,
        conservative_on_error=True
    )

    if not os.path.exists(ENGINE_CSV):
        #print("No CSV Available.")
        return None

    last_decision = None
    while True:
        engine_done = engine_diag.run(ENGINE_CSV)
        battery_done = battery_diag.run(BATTERY_CSV)

        # Read the latest decision saved by analyst (could be None until first report)
        if hasattr(analyst, "last_output"):
            last_decision = analyst.last_output

        if engine_done and battery_done:
            break

        time.sleep(0.5)  # small polling delay

    # return the last decision (string) for the caller to use
    return last_decision


if __name__ == "__main__":
    result = module_1()
    print("Result: ", result)
    # result already printed by analyst; module also returns it
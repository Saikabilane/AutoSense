import os
import pandas as pd
import numpy as np
import joblib
import traceback
import ollama

class DiagnosticAgent:
    """
    DiagnosticAgent processes one CSV row at a time and sends payloads to the analyst.
    By default it is silent (no prints). Set verbose=True to enable debug prints.
    """

    def __init__(
        self,
        subsystem,
        model_path,
        le_path,
        features,
        analyst,
        base_dir=r"./",
        conservative_on_error=False,
        verbose=False
    ):
        self.name = subsystem
        self.features = features
        self.analyst = analyst
        self.base_dir = base_dir
        self.conservative_on_error = conservative_on_error
        self.verbose = verbose

        # Load models and label encoder
        try:
            self.model = joblib.load(os.path.join(self.base_dir, model_path))
            if self.verbose:
                print(f"[{self.name}] Model loaded: {model_path}")
        except Exception as e:
            if self.verbose:
                print(f"[{self.name}][ERROR] Failed to load model {model_path}: {e}")
            self.model = None

        try:
            self.le = joblib.load(os.path.join(self.base_dir, le_path))
            if self.verbose:
                print(f"[{self.name}] LabelEncoder loaded: {le_path}")
        except Exception as e:
            if self.verbose:
                print(f"[{self.name}][ERROR] Failed to load label encoder {le_path}: {e}")
            self.le = None

    def run(self, csv_path):
        """Process one row from csv_path. Return True if "done" (no file or empty)."""
        if not os.path.exists(csv_path):
            # silent: no print
            return True  # nothing to do

        try:
            df = pd.read_csv(csv_path)
        except Exception as e:
            if self.verbose:
                print(f"[{self.name}][ERROR] Failed to read CSV {csv_path}: {e}")
                traceback.print_exc()
            return True

        if df.empty:
            return True

        # Take first row
        row = df.iloc[0]
        data = row.to_dict()
        data['_subsystem'] = self.name

        # Write remaining rows back safely
        try:
            df.iloc[1:].to_csv(csv_path, index=False)
        except Exception as e:
            if self.verbose:
                print(f"[{self.name}][ERROR] Failed to write CSV back: {e}")
                traceback.print_exc()

        # Battery feature engineering
        if self.name == "BATTERY":
            try:
                v = float(data.get("Voltage (V)", 0) or 0)
                c = float(data.get("Current (A)", 0) or 0)
                t = float(data.get("Temperature (°C)", 0) or 0)
                data["Power_Watts"] = v * c
                data["Internal_Res_Proxy"] = v / (c + 0.1)
                data["Temp_Stress"] = t / (c + 1.0)
            except Exception as e:
                if self.verbose:
                    print(f"[{self.name}][WARN] Feature engineering error: {e}")
                    traceback.print_exc()

        # ML Prediction
        ml_pred = "Error"
        ml_conf = 0.0
        is_failure = False

        if self.model is None or self.le is None:
            if self.verbose:
                print(f"[{self.name}][ERROR] Model or label encoder not available.")
            if self.conservative_on_error:
                ai_verdict = "FAULT"
                payload = {"subsystem": self.name, "ai_verdict": ai_verdict, "km_driven": data.get("km_driven", 10)}
                self.analyst.analyze_and_report(payload)
                return False
            return False

        try:
            # Create input dataframe but guard missing columns
            input_df = pd.DataFrame([data])

            # Check each expected feature exists or add default 0
            for feat in self.features:
                if feat not in input_df.columns:
                    if self.verbose:
                        print(f"[{self.name}][WARN] Missing feature '{feat}' in input — adding default 0.")
                    input_df[feat] = 0

            # Select only the columns expected (order matters for some models)
            input_df = input_df[self.features]

            if self.verbose:
                print(f"[{self.name}] Input DF for model:\n{input_df.to_dict(orient='records')[0]}")

            probs = self.model.predict_proba(input_df)[0]
            idx = int(np.argmax(probs))
            ml_pred = self.le.inverse_transform([idx])[0]
            ml_conf = float(probs[idx])
            if self.verbose:
                print(f"[{self.name}] ML predicted = {ml_pred}, conf = {ml_conf:.4f}")

            is_failure = (ml_pred != "Normal" and ml_conf > 0.60)
            if self.verbose:
                print(f"[{self.name}] is_failure = {is_failure}")

        except Exception as e:
            if self.verbose:
                print(f"[{self.name}][ERROR] Prediction failed: {e}")
                traceback.print_exc()
            if self.conservative_on_error:
                ai_verdict = "FAULT"
                payload = {"subsystem": self.name, "ai_verdict": ai_verdict, "km_driven": data.get("km_driven", 10)}
                self.analyst.analyze_and_report(payload)
                return False
            is_failure = False

        # Agentic LLaMA check (only if is_failure)
        try:
            # pass ml_pred and ml_conf to help LLM align (ask_llama may ignore if silent)
            ai_verdict = self.ask_llama(data, is_failure, ml_pred=ml_pred, ml_conf=ml_conf)
        except Exception as e:
            if self.verbose:
                print(f"[{self.name}][ERROR] ask_llama raised: {e}")
                traceback.print_exc()
            ai_verdict = "FAULT" if self.conservative_on_error else "SAFE"

        # CONSERVATIVE OVERRIDE: if ML says failure but LLM did not return FAULT, force FAULT
        if is_failure and ai_verdict != "FAULT":
            if self.verbose:
                print(f"[{self.name}] Overriding ai_verdict '{ai_verdict}' -> 'FAULT' because is_failure=True")
            ai_verdict = "FAULT"

        # Send the payload to analyst (analyst will print)
        payload = {
            "subsystem": self.name,
            "ai_verdict": ai_verdict,
            "km_driven": data.get("km_driven", 10)
        }
        # silent: do not print payload
        self.analyst.analyze_and_report(payload)

        return False  # still running

    def ask_llama(self, data, is_failure, ml_pred=None, ml_conf=None):
        """
        Strict ask_llama that also logs raw model reply only when verbose=True.
        Returns "SAFE"/"WARNING"/"FAULT". If LLM errors, returns FAULT if conservative_on_error else FAULT.
        """
        if not is_failure:
            return "SAFE"

        essential = {k: v for k, v in data.items() if k in ['Voltage (V)', 'Temperature (°C)', 'lub oil temp', 'Engine rpm']}

        # Build a strong prompt including ML evidence
        system_msg = {
            "role": "system",
            "content": (
                "You are a STRICT diagnostic assistant. Answer with EXACTLY ONE WORD: FAULT or WARNING. "
                "No punctuation, no explanation, no extra text."
            )
        }

        user_content = f"Data: {essential}\n"
        if ml_pred is not None and ml_conf is not None:
            user_content += f"ML_prediction = {ml_pred}, ML_confidence = {ml_conf:.3f}\n"
            user_content += "If ML_confidence >= 0.60 and ML_prediction != 'Normal', you MUST output FAULT. Otherwise output WARNING.\n"
        else:
            user_content += "Is this dangerous? Output ONLY FAULT or WARNING.\n"

        user_msg = {"role": "user", "content": user_content}

        try:
            resp = ollama.chat(model="llama3.2:1b", messages=[system_msg, user_msg])
            raw = resp.get("message", {}).get("content", "")
            if self.verbose:
                print(f"[{self.name}][LLM RAW] {raw!r}")

            first_line = next((ln.strip() for ln in raw.splitlines() if ln.strip()), "").upper()
            if first_line in ("FAULT", "WARNING"):
                return first_line
            if "FAULT" in first_line:
                return "FAULT"
            if "WARNING" in first_line:
                return "WARNING"

            return "FAULT" if self.conservative_on_error else "FAULT"

        except Exception as e:
            if self.verbose:
                print(f"[{self.name}][ERROR] ollama.chat failed: {e}")
                traceback.print_exc()
            return "FAULT" if self.conservative_on_error else "FAULT"
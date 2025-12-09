import ollama
from datetime import datetime

class DataAnalystAgent:
    ALLOWED = {"BATTERY ISSUE", "ENGINE ISSUE", "MAINTENANCE DUE", "NO SERVICE"}

    def __init__(self, service_threshold=5000):
        self.total_km = 1000.0
        self.last_service_km = 0.0
        self.service_threshold = service_threshold
        self.next_service_date = datetime(2025, 12, 31)

        # NEW: holds the last decision string
        self.last_output = None

    def _local_decision(self, sub, fact_fault, fact_km, fact_date):
        if fact_fault and sub == "BATTERY":
            return "BATTERY ISSUE"
        if fact_fault and sub == "ENGINE":
            return "ENGINE ISSUE"
        if fact_km or fact_date:
            return "MAINTENANCE DUE"
        return "NO SERVICE"

    def analyze_and_report(self, msg):
        sub = msg["subsystem"]
        verdict = msg["ai_verdict"]
        km_inc = float(msg["km_driven"])

        # Update odometer
        self.total_km += km_inc
        km_since_service = self.total_km - self.last_service_km
        today = datetime.now()

        # Facts
        fact_fault = (verdict == "FAULT")
        fact_km = (km_since_service >= self.service_threshold)
        fact_date = (today > self.next_service_date)

        # STRICT PROMPT WITHOUT extra arguments
        prompt = f"""
        ONLY OUTPUT ONE OF THESE OPTIONS (UPPERCASE, EXACT MATCH, NO EXTRA WORDS):
        BATTERY ISSUE
        ENGINE ISSUE
        MAINTENANCE DUE
        NO SERVICE

        NEVER output explanations.

        Use these rules:
        - If Fault Detected is True AND Subsystem is BATTERY -> BATTERY ISSUE
        - If Fault Detected is True AND Subsystem is ENGINE -> ENGINE ISSUE
        - If Odometer Crossed is True OR Date Crossed is True -> MAINTENANCE DUE
        - Otherwise -> NO SERVICE

        INPUT:
        Subsystem = {sub}
        Fault Detected = {fact_fault}
        Odometer Crossed = {fact_km}
        Date Crossed = {fact_date}

        Respond with ONLY one of the four outputs.
        """

        try:
            resp = ollama.chat(
                model="llama3.1:8b",
                messages=[{"role": "user", "content": prompt}]
            )

            raw = resp["message"]["content"].strip().upper()
            line = raw.splitlines()[0].strip()

            if line in self.ALLOWED:
                final_output = line
            else:
                match = next((a for a in self.ALLOWED if a in line), None)
                if match:
                    final_output = match
                else:
                    final_output = self._local_decision(sub, fact_fault, fact_km, fact_date)

        except Exception:
            # If LLM fails, fallback to deterministic rules
            final_output = self._local_decision(sub, fact_fault, fact_km, fact_date)

        # Print exactly one line: the final decision from the analyst
        #print(final_output)

        # NEW: save last output so callers can inspect or return it
        self.last_output = final_output

        if final_output == "MAINTENANCE DUE":
            self.last_service_km = self.total_km

        return final_output
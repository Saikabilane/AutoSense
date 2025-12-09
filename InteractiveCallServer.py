from flask import Flask, request, Response
from twilio.twiml.voice_response import VoiceResponse
from twilio.rest import Client
from pyngrok import ngrok
from threading import Timer
import threading
import sys
import json

# Twilio credentials
TWILIO_ACCOUNT_SID = 'yoursid'
TWILIO_AUTH_TOKEN = 'yourauthtoken'
TWILIO_CALLER_ID = '+987654321'

client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
app = Flask(__name__)

# ---- GLOBAL STORAGE ----
SESSION = {
    "script": "",
    "slots": [],
    "response": None       # <-- user response captured here
}

# This event allows Flask to stop when user response is captured
response_event = threading.Event()

@app.route("/start-call", methods=["POST"])
def start_call_twiml():
    resp = VoiceResponse()

    gather = resp.gather(
        input="speech",
        timeout="auto",
        action="/handle-response",
        method="POST"
    )

    gather.say(
        SESSION["script"],
        voice="Polly.Aditi",
        language="en-IN"
    )

    resp.say("Your response is not clear to us.",
             voice="Polly.Aditi", language="en-IN")

    return Response(str(resp), mimetype="text/xml")

@app.route("/handle-response", methods=["POST"])
def handle_response():
    user_input = (request.values.get("SpeechResult") or "").lower()

    SESSION["response"] = user_input
    response_event.set()

    # Build TwiML manually (no VoiceResponse)
    xml = """<?xml version="1.0" encoding="UTF-8"?>
    <Response>
        <Say voice="Polly.Aditi" language="en-IN">
            Your response has been recorded.
        </Say>
    </Response>
    """

    return Response(xml, mimetype="text/xml")


def run_call(script, slots, to_number):
    SESSION["script"] = script
    SESSION["slots"] = slots

    tunnel = ngrok.connect(5000)
    public_url = tunnel.public_url
    print("NGROK URL:", public_url)

    def trigger():
        call = client.calls.create(
            to=to_number,
            from_=TWILIO_CALLER_ID,
            url=f"{public_url}/start-call",
            method="POST"
        )
        print("Call SID:", call.sid)

    Timer(3, trigger).start()

    server_thread = threading.Thread(
        target=lambda: app.run(port=5000, debug=False, use_reloader=False)
    )
    server_thread.start()

    response_event.wait()

    print("Captured user input:", SESSION["response"])
    ngrok.kill()

    return SESSION["response"]

if __name__ == "__main__":
    data = json.loads(sys.argv[1])
    result = run_call(data["script"], data["slots"], data["number"])
    print("FINAL RETURN VALUE:", result)
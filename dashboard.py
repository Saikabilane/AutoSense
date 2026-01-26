import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# ----------------------------
# Load CSV Files
# ----------------------------
telemetry_file = "telemetry.csv"
calendar_file = "AutoSense_ServiceCalendar.csv"

telemetry_df = pd.read_csv(telemetry_file)
calendar_df = pd.read_csv(calendar_file)

# ----------------------------
# Sidebar Navigation
# ----------------------------
st.sidebar.title("🚗 AutoSense Dashboard")
page = st.sidebar.radio(
    "Select Portal",
    ["User Portal", "Manufacturer Portal", "Service Center Portal"]
)

# ----------------------------
# PAGE 1 — USER PORTAL
# ----------------------------
if page == "User Portal":
    st.title("👤 Vehicle Owner Portal")

    st.subheader("Live Vehicle Health Prediction")

    # Show last telemetry row
    latest = telemetry_df.tail(1)

    st.write("### Latest Telemetry Data")
    st.dataframe(latest)

    # Example Prediction Output
    st.write("### Detected Condition")
    st.success("Battery Issue Detected ⚠️")

    st.write("### Recommended Service Slots")

    free_slots = calendar_df[calendar_df["Status"] == "FREE"].head(3)

    st.dataframe(free_slots)

    st.info("Customer Engagement Call Triggered 📞")
    st.write("Slot will be frozen once user confirms.")

# ----------------------------
# PAGE 2 — MANUFACTURER PORTAL
# ----------------------------
elif page == "Manufacturer Portal":
    st.title("🏭 Manufacturer Fault Analytics")

    st.subheader("Fault Trends & Most Repaired Parts")

    # Dummy Fault Data (replace with feedback agent output)
    fault_data = pd.DataFrame({
        "Component": ["Battery", "Engine", "Coolant", "Brakes"],
        "FaultCount": [15, 10, 6, 4]
    })

    st.write("### Most Frequently Failing Components")
    st.dataframe(fault_data)

    st.write("### Fault Distribution Chart")

    plt.figure()
    plt.bar(fault_data["Component"], fault_data["FaultCount"])
    st.pyplot(plt)

    st.info("Future Scope: RCA/CAPA Reports & Manufacturer Alerts")

# ----------------------------
# PAGE 3 — SERVICE CENTER PORTAL
# ----------------------------
elif page == "Service Center Portal":
    st.title("🏢 Service Center Monitoring")

    st.subheader("Service Calendar Overview")

    st.write("### Full Slot Calendar")
    st.dataframe(calendar_df.head(15))

    st.subheader("Booking Summary")

    booked = calendar_df[calendar_df["Status"] == "BOOKED"]
    free = calendar_df[calendar_df["Status"] == "FREE"]

    st.metric("Booked Slots", len(booked))
    st.metric("Free Slots", len(free))

    st.write("### Engagement Status")
    st.success("Calls placed successfully for urgent faults")

    st.info("Future Scope: Workload Peaks + Satisfaction Monitoring")

import streamlit as st
import pandas as pd

# ------------------------------
# Page Config
# ------------------------------
st.set_page_config(page_title="AutoSense Dashboard", layout="wide")

st.title("🚗 AutoSense – Predictive Maintenance Dashboard")

# Load CSV files
calendar_file = "../AutoSense_ServiceCalendar.csv"
telemetry_file = "../telemetry.csv"

# ------------------------------
# Sidebar Navigation
# ------------------------------
page = st.sidebar.radio(
    "Select Dashboard View",
    ["👤 Vehicle Owner", "🏭 Manufacturer View", "🏢 Service Center View"]
)

# ------------------------------
# PAGE 1 – Vehicle Owner
# ------------------------------
if page == "👤 Vehicle Owner":
    st.header("👤 Vehicle Owner Portal")

    vehicle_id = st.text_input("Enter Vehicle ID", "VN001")

    st.subheader("📅 Upcoming Service Slots")

    df_cal = pd.read_csv(calendar_file)

    user_slots = df_cal[df_cal["VehicleID"] == vehicle_id]

    if user_slots.empty:
        st.warning("No service slot booked yet.")
    else:
        st.success("Your booked service slots:")
        st.dataframe(user_slots)

    st.subheader("🔍 Vehicle Status")
    st.info("Failure Risk Prediction + Call Alert will be shown here after Master Agent execution.")

# ------------------------------
# PAGE 2 – Manufacturer View
# ------------------------------
elif page == "🏭 Manufacturer View":
    st.header("🏭 Manufacturer Fault Analytics")

    st.subheader("Most Common Fault Types (Demo Data)")

    fault_data = {
        "Fault Type": ["Battery Issue", "Engine Overheat", "Brake Failure"],
        "Count": [12, 8, 5]
    }

    df_fault = pd.DataFrame(fault_data)

    st.dataframe(df_fault)

    st.subheader("📊 Top Repaired Parts")
    st.bar_chart(df_fault.set_index("Fault Type"))

    st.info("This report helps manufacturers detect recurring faults and improve design.")

# ------------------------------
# PAGE 3 – Service Center View
# ------------------------------
elif page == "🏢 Service Center View":
    st.header("🏢 Service Center Monitoring")

    df_cal = pd.read_csv(calendar_file)

    st.subheader("📌 Slot Booking Overview")

    booked = df_cal[df_cal["Status"] == "BOOKED"]
    free = df_cal[df_cal["Status"] == "FREE"]

    col1, col2 = st.columns(2)

    with col1:
        st.metric("Total Booked Slots", len(booked))

    with col2:
        st.metric("Total Free Slots", len(free))

    st.subheader("📅 Full Service Calendar")
    st.dataframe(df_cal)

    st.success("Service managers can monitor workload and upcoming bookings here.")

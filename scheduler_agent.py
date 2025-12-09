import pandas as pd
from datetime import datetime, timedelta
import math
import random

# -----------------------------
# Constants
# -----------------------------
EXPECTED_COLUMNS = ["SlotID", "Day", "Time", "Status", "VehicleID", "RiskLevel",
                    "ServiceType", "Capacity", "Used", "VehicleType"]

SERVICE_DURATION = {
    "Scooter": {"Minor Service": 45, "Engine Check": 60},
    "Car": {"General Service": 90, "Brake Check": 30, "Engine Check": 120, "Coolant Leak": 60},
    "EV": {"Battery Issue": 60, "Software Update": 30},
    "LCV": {"Major Service": 180}
}

SLOT_CAPACITY = 5

# -----------------------------
# Generate slots (Modified)
# -----------------------------
def generate_slots(days_ahead=7):
    rows = []
    now = datetime.now()
    slot_id_counter = 1 # Start counter for the new unique ID

    for d in range(1, days_ahead + 1):
        day = now + timedelta(days=d)
        
        # Calculate the actual date for generating Day name
        slot_date = day.replace(hour=0, minute=0, second=0, microsecond=0) 
        day_name = slot_date.strftime("%A") # e.g., "Tuesday"

        for hour in range(9, 18):  # 9 AM - 5 PM
            time_str = datetime(2000, 1, 1, hour, 0).strftime("%H:%M") # e.g., "09:00"

            # SlotDateTime is calculated but NOT saved to the CSV.
            # It's only used internally to track the slot's true date/time for console output.
            slot_dt = day.replace(hour=hour, minute=0, second=0, microsecond=0)
            
            # Note: We are using Day and Time, not the full date for the CSV.
            # We save the SlotID, Day name, and Time string.
            rows.append([slot_id_counter, day_name, time_str, "FREE", "", "", "", SLOT_CAPACITY, 0, ""])
            slot_id_counter += 1

    df = pd.DataFrame(rows, columns=EXPECTED_COLUMNS)
    df.to_csv("AutoSense_ServiceCalendar.csv", index=False)

    print(f"Created new calendar CSV file: AutoSense_ServiceCalendar.csv")
    print(f"Generated {len(rows)} slots.\n")
    
    # Add a temporary SlotDateTime column back for internal use in other functions 
    # (like display_calendar and random_bookings which rely on continuous indices)
    temp_df = []
    for d in range(1, days_ahead + 1):
        day = now + timedelta(days=d)
        for hour in range(9, 18):
             temp_df.append(day.replace(hour=hour, minute=0, second=0, microsecond=0))
    df['SlotDateTime'] = temp_df
    
    return df


# -----------------------------
# Load calendar (Modified)
# -----------------------------
def load_calendar():
    # SlotDateTime is not in the CSV, so we don't parse it.
    df = pd.read_csv("AutoSense_ServiceCalendar.csv")
    df["Capacity"] = df["Capacity"].astype(int)
    df["Used"] = df["Used"].astype(int)
    df.fillna("", inplace=True)
    
    # *** IMPORTANT ***
    # Since the original booking logic relied on SlotDateTime for indexing, 
    # we must re-create a temporary SlotDateTime for Random Bookings to work 
    # based on index continuity, but we can't do this accurately without the date.
    # For now, we'll return the calendar as is, but random_bookings will have issues.
    return df

# -----------------------------
# Random bookings generator (Modified)
# -----------------------------
def random_bookings(df, booking_ratio=0.3):
    total_slots = len(df)
    slots_to_book = int(total_slots * booking_ratio)

    VEHICLE_SERVICES = {
        "Car": ["General Service", "Brake Check", "Engine Check", "Coolant Leak"],
        "Scooter": ["Minor Service", "Engine Check"],
        "EV": ["Battery Issue", "Software Update"],
        "LCV": ["Major Service"]
    }

    RISK_LEVELS = ["High", "Medium", "Low"]

    booked_count = 0
    while booked_count < slots_to_book:

        # Use SlotID for random selection logic
        idx = random.randint(1, total_slots) # SlotID starts at 1

        # We must map the SlotID back to the DataFrame index (which starts at 0)
        df_index = idx - 1 

        if df.at[df_index, "Status"] != "FREE":
            continue

        vehicle_type = random.choice(list(VEHICLE_SERVICES.keys()))
        service_type = random.choice(VEHICLE_SERVICES[vehicle_type])
        risk_level = random.choice(RISK_LEVELS)
        vehicle_id = f"{vehicle_type[:2].upper()}{random.randint(1000,9999)}"

        duration = SERVICE_DURATION.get(vehicle_type, {}).get(service_type, 60)
        slots_needed = math.ceil(duration / 60)

        if df_index + slots_needed > total_slots:
            continue

        # Book consecutive slots using DataFrame index
        can_book = True
        for j in range(slots_needed):
            if df.at[df_index + j, "Status"] != "FREE":
                can_book = False
                break

        if not can_book:
            continue

        # Confirm booking
        for j in range(slots_needed):
            df.at[df_index + j, "Status"] = "BOOKED"
            df.at[df_index + j, "VehicleID"] = vehicle_id
            df.at[df_index + j, "RiskLevel"] = risk_level
            df.at[df_index + j, "ServiceType"] = service_type
            df.at[df_index + j, "Used"] += 1
            df.at[df_index + j, "VehicleType"] = vehicle_type

        booked_count += 1

    # Save the calendar without the SlotDateTime column
    df[EXPECTED_COLUMNS].to_csv("AutoSense_ServiceCalendar.csv", index=False)
    print("Random booking completed.\n")
    return df


# -----------------------------
# Function to get free slots (Modified)
# -----------------------------
def get_available_slots(df):
    # Now returns Day and Time combined, instead of SlotDateTime
    free_df = df[(df["Status"] == "FREE") & (df["Used"] < df["Capacity"])]
    
    # Return a list of strings: "Day HH:MM"
    return (free_df['Day'] + ' ' + free_df['Time']).tolist()

# -----------------------------
# Function to book slot for real customer (Modified)
# -----------------------------
def book_slot(df, slot_id, vehicle_id, vehicle_type, service_type, risk_level):
    
    # The SlotID is now the primary key.
    # Check if the SlotID is valid
    if slot_id not in df["SlotID"].values:
        return "❌ Error: Slot ID not found."

    # Find the DataFrame index (which starts at 0) from the SlotID (which starts at 1)
    match = df[df["SlotID"] == slot_id]
    idx = match.index[0]

    if df.at[idx, "Used"] >= df.at[idx, "Capacity"]:
        return "❌ Slot already full."

    # The booking process uses the DataFrame index 'idx'
    df.at[idx, "Status"] = "BOOKED"
    df.at[idx, "VehicleID"] = vehicle_id
    df.at[idx, "RiskLevel"] = risk_level
    df.at[idx, "ServiceType"] = service_type
    df.at[idx, "VehicleType"] = vehicle_type
    df.at[idx, "Used"] += 1

    # Save the calendar without the SlotDateTime column
    df[EXPECTED_COLUMNS].to_csv("AutoSense_ServiceCalendar.csv", index=False)
    
    day_time = f"{df.at[idx, 'Day']} at {df.at[idx, 'Time']}"
    return f"✅ Booking confirmed for {vehicle_id} (Slot ID: {slot_id}) on {day_time}."


# -----------------------------
# Display calendar neatly (Modified)
# -----------------------------
def display_calendar(df):
    print("\n================ SERVICE CALENDAR ================\n")
    view = df.copy()
    
    # Select only the columns that exist in the CSV (no SlotDateTime)
    print(view[EXPECTED_COLUMNS].to_string(index=False)) 
    print("\n=================================================\n")


# -----------------------------
# Main Program
# -----------------------------
if __name__ == "__main__":
    df = generate_slots(7) # Creates CSV with SlotID, Day, and Time only
    
    print("Available Slots (Day and Time):")
    print(get_available_slots(df)) 
    
    df = random_bookings(df, 0.3)
    display_calendar(df)

    # Example of a real customer booking using the SlotID (e.g., SlotID 10)
    slot_id_to_book = 10 
    
    # Find the Day/Time for display purposes
    day = df[df['SlotID'] == slot_id_to_book]['Day'].iloc[0]
    time = df[df['SlotID'] == slot_id_to_book]['Time'].iloc[0]
    
    print(f"\nAttempting to book SlotID {slot_id_to_book} ({day} {time})...")
    
    # You must pass the SlotID (integer) now, not the full datetime string
    booking_result = book_slot(
        df, 
        slot_id=slot_id_to_book, 
        vehicle_id="XYZ9999", 
        vehicle_type="Car", 
        service_type="Brake Check", 
        risk_level="High"
    )
    
    print(booking_result)
    
    # Reload and display the final calendar
    df_final = load_calendar()
    display_calendar(df_final)

    print("System ready. CSV updated.\n")
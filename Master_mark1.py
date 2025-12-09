import pandas as pd
from main_runner import module_1
from EngagementAgent import schedule_customer_call
from scheduler_agent import *

def process_csv(input_file, output_file1, output_file2):
    
    df = pd.read_csv(input_file)
    
    df = df[df['Name'] != 'Name']
    df = df.reset_index(drop=True)
    
    engine_columns = ['Engine rpm', 'Lub oil pressure', 'Fuel pressure', 
                      'Coolant pressure', 'lub oil temp', 'Coolant temp', 'km_driven']
    
    electrical_columns = ['Voltage (V)', 'Current (A)', 'Temperature (°C)', 
                          'Motor Speed (RPM)', 'Estimated SOC (%)', 'km_driven']
    
    total_rows = len(df)
    print(f"Total rows to process: {total_rows}\n")
    
    freeSlot = generate_slots()
    
    for index, row in df.iterrows():
        freeSlots = freeSlot
        print("\n")
        print(f"Processing row {index + 1}/{total_rows}")
        print(f"Name: {row['Name']}, Phone: {row['Phone Number']}")
        
        engine_data = {col: row[col] for col in engine_columns}
        
        electrical_data = {col: row[col] for col in electrical_columns}
        
        engine_df = pd.DataFrame([engine_data])
        electrical_df = pd.DataFrame([electrical_data])
        
        engine_df.to_csv(output_file1, index=False)
        electrical_df.to_csv(output_file2, index=False)

        result = module_1()
        print(f"Row {index+1} Condition: {result}")

        if "ISSUE" in result:
            freeSlots = random_bookings(freeSlots, 0.3)
            freeSlots = get_available_slots(freeSlots)

            if len(freeSlots) == 0:
                continue
            else:
                phNo = "+"+str(row['Phone Number'])
                bookedSlot = schedule_customer_call(
                    customer_name=row['Name'],
                    customer_number=phNo,
                    customer_vehicle="Vehicle",
                    service_reason=result,
                    available_slots=freeSlots
                )

                booking = book_slot(
                    df, bookedSlot, "Vehicle", "None", result, "None"
                )

                print(booking)
    
    print(f"ALL {total_rows} ROWS PROCESSED SUCCESSFULLY!")

if __name__ == "__main__":
    input_csv = "telemetry.csv"
    output_engine_csv = "engine_inference.csv"
    output_electrical_csv = "battery_inference.csv"
    
    process_csv(input_csv, output_engine_csv, output_electrical_csv)
import subprocess
import json

def schedule_customer_call(customer_name, customer_number, customer_vehicle, service_reason, available_slots):
    """
    Schedule and execute an interactive customer service call.
    
    Args:
        customer_name (str): Name of the customer
        customer_number (str): Phone number of the customer
        customer_vehicle (str): Vehicle model
        service_reason (str): Reason for service
        available_slots (list): List of available appointment slots
    
    Returns:
        subprocess.CompletedProcess: Result from the subprocess call
    """
    # Generate customer message
    output = f"Hello {customer_name},\nThis call is to inform you that your {customer_vehicle} needs service due to {service_reason}.\nAvailable slots are: "
    for slot in available_slots:
        output += slot + "\n"
    
    # Prepare JSON payload
    payload = json.dumps({
        "script": output,
        "slots": available_slots,
        "number": customer_number
    })
    
    # Execute the interactive call server (same as your original code)
    result = subprocess.run(["python", "InteractiveCallServer.py", payload])
    
    return result

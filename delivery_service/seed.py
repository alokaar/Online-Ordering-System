from database import driver_collection

drivers = [
    {"name": "Kamal", "phone": "0771234567" , "vehicle_no": "ABC234", "vehicle_type": "Bike"},
    {"name": "Nimal", "phone": "0779876543", "vehicle_no": "ABC834", "vehicle_type": "Car"},
    {"name": "Sunil", "phone": "0714567890", "vehicle_no": "ABC254", "vehicle_type": "Scooter"}
]

driver_collection.insert_many(drivers)

print("Drivers inserted!")
from pymongo import MongoClient
from datetime import datetime
import sys

try:
    client = MongoClient('mongodb://localhost:27017/')

    # 1. Menu Items
    client['menu_db'].menu_items.drop()
    client['menu_db'].menu_items.insert_many([
        {'name': 'Margherita Pizza', 'description': 'Classic cheese', 'price': 12.99, 'category': 'Pizza', 'is_available': True, 'created_at': datetime.utcnow()},
        {'name': 'Chicken Fried Rice', 'description': 'Special fried rice', 'price': 14.99, 'category': 'Rice', 'is_available': True, 'created_at': datetime.utcnow()}
    ])

    # 2. Customers
    client['customer_db'].customers.drop()
    client['customer_db'].customers.insert_one({
        'user_id': 'user_001',
        'email': 'customer@example.com',
        'name': 'John Doe',
        'phone': '1234567890',
        'address': '123 Main St',
        'created_at': datetime.utcnow()
    })

    # 3. Auth Users
    client['auth_db'].users.drop()
    client['auth_db'].users.insert_one({
        'email': 'customer@example.com',
        'hashed_password': 'dummy_hashed_password',
        'role': 'customer',
        'is_active': True,
        'created_at': datetime.utcnow()
    })

    # 4. Restaurants
    client['restaurant_db'].restaurants.drop()
    client['restaurant_db'].restaurants.insert_one({
        'name': 'The Great Pizza',
        'cuisine': 'Italian',
        'rating': 4.5,
        'created_at': datetime.utcnow()
    })

    # 5. Delivery Drivers
    client['delivery_db'].drivers.drop()
    client['delivery_db'].drivers.insert_one({
        'name': 'Speedy Driver',
        'vehicle': 'Motorcycle',
        'status': 'available',
        'created_at': datetime.utcnow()
    })

    print('Sample data successfully seeded into separated databases.')
except Exception as e:
    print(f'Error: {e}')
    sys.exit(1)

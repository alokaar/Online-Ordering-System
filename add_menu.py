import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timezone

async def add_sample_menu():
    client = AsyncIOMotorClient('mongodb+srv://aloka:Aloka180402@cluster1.h0mabke.mongodb.net/food_ordering')
    db = client.food_ordering

    # Check if menu items already exist
    existing_count = await db.menu_items.count_documents({})
    print(f'Existing menu items: {existing_count}')

    if existing_count == 0:
        menu_items = [
            {
                'name': 'Margherita Pizza',
                'description': 'Classic pizza with tomato sauce, mozzarella, and basil',
                'price': 12.99,
                'category': 'Pizza',
                'image_url': None,
                'is_available': True,
                'created_at': datetime.now(timezone.utc)
            },
            {
                'name': 'Chicken Burger',
                'description': 'Grilled chicken burger with lettuce, tomato, and mayo',
                'price': 8.99,
                'category': 'Burgers',
                'image_url': None,
                'is_available': True,
                'created_at': datetime.now(timezone.utc)
            },
            {
                'name': 'Caesar Salad',
                'description': 'Fresh romaine lettuce with Caesar dressing and croutons',
                'price': 6.99,
                'category': 'Salads',
                'image_url': None,
                'is_available': True,
                'created_at': datetime.now(timezone.utc)
            },
            {
                'name': 'Chocolate Brownie',
                'description': 'Rich chocolate brownie with vanilla ice cream',
                'price': 4.99,
                'category': 'Desserts',
                'image_url': None,
                'is_available': True,
                'created_at': datetime.now(timezone.utc)
            }
        ]

        result = await db.menu_items.insert_many(menu_items)
        print(f'Added {len(result.inserted_ids)} menu items')
    else:
        print('Menu items already exist, skipping insertion')

    await client.close()

if __name__ == "__main__":
    asyncio.run(add_sample_menu())
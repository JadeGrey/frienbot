import json, random
from typing import Literal
from main import DB_FOLDER

def get_currency_data():
    with open(f'{DB_FOLDER}currency_data.json', 'r') as f:
        data = json.load(f)
        f.close()
        return data
    
def save_currency_data(data: dict) -> None:
    with open(f'{DB_FOLDER}currency_data.json', 'w') as f:
        json.dump(data, f, indent=3)
        f.close()

def add_user_to_currency_data(id: str) -> None:
    data = get_currency_data()
    data[id] = 0
    save_currency_data(data)

def get_drop_data():
    with open(f'{DB_FOLDER}drops.json', 'r') as f:
        data = json.load(f)
        f.close()
        return data
    
def save_drop_data(data: dict) -> None:
    with open(f'{DB_FOLDER}drops.json', 'w') as f:
        json.dump(data, f, indent=3)
        f.close()

def add_user_to_drop_data(id: str) -> None:
    data = get_drop_data()
    data[id] = {
        'daily': 0,
        'weekly': 0,
        'monthly': 0
    }
    save_drop_data(data)

def calculate_drop(type: Literal['Daily', 'Weekly', 'Monthly']) -> dict[str, any]:

    rarity_int = random.randint(1, 100)

    match type:

        case 'Daily':
            if 50 >= rarity_int:
                rarity = 'Common'
                amount = random.randint(100, 250)
            elif 75 >= rarity_int > 50:
                rarity = 'Uncommon'
                amount = random.randint(250, 400)
            elif 95 >= rarity_int > 75:
                rarity = 'Rare'
                amount = random.randint(400, 550)
            elif 100 >= rarity_int > 95:
                rarity = 'Legendary'
                amount = random.randint(550, 1000)
            
        case 'Weekly':
            if 33 >= rarity_int:
                rarity = 'Common'
                amount = random.randint(200, 550)
            elif 65 >= rarity_int > 33:
                rarity = 'Uncommon'
                amount = random.randint(550, 850)
            elif 85 >= rarity_int > 65:
                rarity = 'Rare'
                amount = random.randint(850, 1200)
            elif 100 >= rarity_int > 85:
                rarity = 'Legendary'
                amount = random.randint(1200, 2000)
            
        case 'Monthly':
            if 25 >= rarity_int:
                rarity = 'Common'
                amount = random.randint(1000, 1250)
            elif 50 >= rarity_int > 25:
                rarity = 'Uncommon'
                amount = random.randint(1250, 1500)
            elif 75 >= rarity_int > 50:
                rarity = 'Rare'
                amount = random.randint(1500, 1750)
            elif 100 >= rarity_int > 75:
                rarity = 'Legendary'
                amount = random.randint(1750, 3000)
    
    return {'rarity': rarity, 'amount': amount}
    
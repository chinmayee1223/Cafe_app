from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from pymongo import MongoClient
from datetime import datetime

app = Flask(__name__)
CORS(app)

# MongoDB connection
# mongodb+srv://admin:<db_password>@cluster0.tszjsu0.mongodb.net/
# mongodb+srv://admin:<db_password>@cluster0.ee7vq.mongodb.net/
# mongodb+srv://admin:<db_password>@cluster0.ee7vq.mongodb.net/
# mongodb+srv://admin:<db_password>@cluster0.tszjsu0.mongodb.net/
# mongodb+srv://admin:<db_password>@cluster0.kxwpz.mongodb.net/

client = MongoClient(
    "mongodb+srv://admin:admin123@cluster0.kxwpz.mongodb.net/?retryWrites=true&w=majority",
    ssl=True,
    tlsAllowInvalidCertificates=True  # Use for testing only
)
# mongodb+srv://admin:<db_password>@cluster0.kxwpz.mongodb.net/
db = client["cafe_db"]
inventory_collection = db["inventory"]

# Initial inventory data
inventory_items = [
    {"name": "Hot Coffee", "price": 80, "stock": 10, "threshold": 1, "popularity": 0},
    {"name": "Black Coffee", "price": 80, "stock": 10, "threshold": 1, "popularity": 0},
    {"name": "Hazelnut Cold Coffee", "price": 125, "stock": 10, "threshold": 1, "popularity": 0},
    {"name": "Chocolate Cold Coffee", "price": 125, "stock": 10, "threshold": 1, "popularity": 0},
    {"name": "Caramel Cold Coffee", "price": 125, "stock": 10, "threshold": 1, "popularity": 0},
    {"name": "Classic Cold Coffee", "price": 100, "stock": 10, "threshold": 1, "popularity": 0},
    {"name": "Iced Americano", "price": 160, "stock": 10, "threshold": 1, "popularity": 0},
    {"name": "Maggie", "price": 30, "stock": 10, "threshold": 1, "popularity": 0}
]

def insert_initial_inventory():
    """Insert initial inventory items into the database."""
    for item in inventory_items:
        if not inventory_collection.find_one({"name": item["name"]}):
            inventory_collection.insert_one(item)

def calculate_dynamic_price(item):
    """Calculate the dynamic price based on demand, time, and inventory."""
    base_price = item['price']
    popularity = item['popularity']
    stock = item['stock']

    # Time-based adjustment
    current_hour = datetime.now().hour
    peak_hours = (8 <= current_hour <= 10) or (18 <= current_hour <= 20)
    time_multiplier = 1.20 if peak_hours else 1.00  # Increase price during peak hours

    # Popularity-based adjustment
    if popularity > 20:
        demand_multiplier = 1.20  # High demand
    elif popularity > 2:
        demand_multiplier = 1.10  # Moderate demand
    else:
        demand_multiplier = 1.00  # Normal demand

    # Inventory-based adjustment
    inventory_multiplier = 1.15 if stock < 10 else 1.00  # Increase if stock is low

    # Calculate current price
    current_price = base_price * time_multiplier * demand_multiplier * inventory_multiplier

    # Ensure price doesn't decrease below base price
    return round(max(current_price, base_price), 2)

@app.route('/')
def index():
    """Render the index page."""
    return render_template("index.html")

@app.route('/store-cart', methods=['POST'])
def store_cart():
    """Handle storing of orders and updating inventory."""
    try:
        order_data = request.get_json()
        cart = order_data.get('cart', {})
        
        for item in cart.values():
            item_name = item['name']
            item_quantity = item['quantity']
            
            inventory_item = inventory_collection.find_one({"name": item_name})
            if inventory_item and inventory_item['stock'] >= item_quantity:
                new_stock = inventory_item['stock'] - item_quantity
                inventory_collection.update_one(
                    {"name": item_name},
                    {"$set": {"stock": new_stock}, "$inc": {"popularity": item_quantity}}
                )

                if new_stock <= inventory_item['threshold']:
                    print(f"Notification: {item_name} stock is low.")
            else:
                return jsonify({"message": f"Not enough stock for {item_name}"}), 400
        
        return jsonify({"message": "Order placed successfully!"}), 200
    
    except Exception as e:
        return jsonify({"message": "Error processing order", "error": str(e)}), 500

@app.route('/get-prices', methods=['GET'])
def get_prices():
    """API to get all items with dynamically adjusted prices."""
    items = inventory_collection.find()
    items_with_prices = []
    for item in items:
        item['current_price'] = calculate_dynamic_price(item)
        item['_id'] = str(item['_id'])
        items_with_prices.append(item)
    return jsonify(items_with_prices)

if __name__ == '__main__':
    insert_initial_inventory()
    app.run(debug=True)

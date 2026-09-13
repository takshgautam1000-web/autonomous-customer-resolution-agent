import json

def check_inventory(product_id):
    with open("data/inventories.json", "r") as file:
        inventory = json.load(file)

    if product_id not in inventory:
        return {
            "success": False,
            "error": "PRODUCT_NOT_FOUND"
        }

    return {
        "success": True,
        "product_id": product_id,
        "stock": inventory[product_id]["stock"]
    }
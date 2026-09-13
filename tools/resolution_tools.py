import json 
import uuid 
def issue_refund(order_id):
    with open("data/orders.json", "r") as file:
        orders = json.load(file)
    if order_id not in orders:
        return {
            "success": False,
            "error": "ORDER_NOT_FOUND"
        }
    # Simulate a temporary failure for our demo
    if order_id == "O501":
        return {
            "success": False,
            "error": "REFUND_SERVICE_UNAVAILABLE"
        }
    transaction_id = "T" + str(uuid.uuid4())[:6]
    with open("data/transactions.json", "r") as file:
        transactions = json.load(file)
    transactions[transaction_id] = {
        "type": "refund",
        "order_id": order_id,
        "amount": orders[order_id]["price"],
        "status": "completed"
    }
    with open("data/transactions.json", "w") as file:
        json.dump(transactions, file, indent=2)
    return {
        "success": True,
        "transaction_id": transaction_id,
        "message": "Refund successfully issued"
    } 
def create_replacement(order_id):
    with open("data/orders.json", "r") as file:
        orders = json.load(file)

    if order_id not in orders:
        return {
            "success": False,
            "error": "ORDER_NOT_FOUND"
        }
    product_id = orders[order_id]["product_id"]
    with open("data/inventories.json", "r") as file:
        inventory = json.load(file)

    if inventory[product_id]["stock"] <= 0:
        return {
            "success": False,
            "error": "OUT_OF_STOCK"
        }
    inventory[product_id]["stock"] -= 1
    with open("data/inventories.json", "w") as file:
        json.dump(inventory, file, indent=2)
    transaction_id = "T" + str(uuid.uuid4())[:6]
    with open("data/transactions.json", "r") as file:
        transactions = json.load(file)
    transactions[transaction_id] = {
        "type": "replacement",
        "order_id": order_id,
        "status": "completed"
    }
    with open("data/transactions.json", "w") as file:
        json.dump(transactions, file, indent=2)
    return {
        "success": True,
        "transaction_id": transaction_id,
        "message": "Replacement successfully created"
    }
def issue_store_credit(customer_id, amount):
    transaction_id = "T" + str(uuid.uuid4())[:6]
    with open("data/transactions.json", "r") as file:
        transactions = json.load(file)
    transactions[transaction_id] = {
        "type": "store_credit",
        "customer_id": customer_id,
        "amount": amount,
        "status": "completed"
    }
    with open("data/transactions.json", "w") as file:
        json.dump(transactions, file, indent=2)
    return {
        "success": True,
        "transaction_id": transaction_id,
        "message": "Store credit successfully issued"
    }

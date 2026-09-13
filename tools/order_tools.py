import json
import uuid
def get_order(order_id):
    with open("data/orders.json", "r") as file:
        orders = json.load(file)
    if order_id not in orders:
        return {
            "success": False,
            "error": "ORDER_NOT_FOUND"
        }
    return {
        "success": True,
        "order": orders[order_id]
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
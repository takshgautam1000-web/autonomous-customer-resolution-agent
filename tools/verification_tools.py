import json 
def verify_transaction(transaction_id):
    with open("data/transactions.json", "r") as file:
        transactions = json.load(file)
    if transaction_id not in transactions:
        return {
            "success": False,
            "error": "TRANSACTION_NOT_FOUND"
        }
    transaction=transactions[transaction_id]
    if transaction["status"] == "completed":
        return {
            "success": True,
            "verified": True,
            "transaction": transaction
        }
    return {
        "success": True,
        "verified": False,
        "transaction": transaction
    }
    
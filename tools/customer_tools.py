import json
def get_customer(customer_id):
    with open("data/customers.json","r") as file:
        customers=json.load(file)
    if customer_id not in customers:
        return{
            "success":False,
            "error":"CUSTOMER_NOT_FOUND"
        }
    return {
        "success": True,
        "customer": customers[customer_id]
    }   
# from tools.resolution_tools import (
#     issue_refund,
#     create_replacement,
#     issue_store_credit
# )

# print("REPLACEMENT TEST:")
# print(create_replacement("O501"))

# print("\nREFUND TEST:")
# print(issue_refund("O501"))

# print("\nSTORE CREDIT TEST:")
# print(issue_store_credit("C101", 4999))

from tools.resolution_tools import issue_store_credit
from tools.verification_tools import verify_transaction


result = issue_store_credit("C101", 4999)

print("ACTION RESULT:")
print(result)

transaction_id = result["transaction_id"]

verification = verify_transaction(transaction_id)

print("\nVERIFICATION RESULT:")
print(verification)
import json

def check_policy(issue_type):
    with open("data/policies.json", "r") as file:
        policies = json.load(file)
    if issue_type not in policies:
        return {
            "success": False,
            "error": "POLICY_NOT_FOUND"
        }
    return {
        "success": True,
        "policy": policies[issue_type]
    }
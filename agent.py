import os
import json
from dotenv import load_dotenv
from groq import Groq
from tools.customer_tools import get_customer
from tools.order_tools import get_order
from tools.inventory_tools import check_inventory
from tools.poilcy_tools import check_policy
from tools.resolution_tools import (
    issue_refund,
    create_replacement,
    issue_store_credit
)
from tools.verification_tools import verify_transaction
# The tool ID is a unique ID that the API gives to a particular tool call made by the LLM.
load_dotenv()
client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)
# The tools list describes that function to the LLM
available_tools = {
    "get_customer": get_customer,
    "get_order": get_order,
    "check_policy": check_policy,
    "check_inventory": check_inventory,
    "create_replacement": create_replacement,
    "issue_refund": issue_refund,
    "issue_store_credit": issue_store_credit,
    "verify_transaction": verify_transaction
}
# Now we need the tools = [...] definition to describe these tools to the LLM.
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_customer",
            "description": "Get customer information using the customer ID.",
            "parameters": {
            # Because "type": "object" means the parameters are grouped together as one JSON object.
            # {\n "customer_id": "C101" \n} That whole thing is an object.
            # parameter data is represented as an object, like above
                "type": "object",
                "properties": {
                    "customer_id": {
                        "type": "string",
                        "description": "The unique customer ID."
                    }
                },
                "required": ["customer_id"]
            }
        }
    },

    {
        "type": "function",
        "function": {
            "name": "get_order",
            "description": "Get order information using the order ID.",
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id": {
                        "type": "string",
                        "description": "The unique order ID."
                    }
                },
                "required": ["order_id"]
            }
        }
    },

    {
        "type": "function",
        "function": {
            "name": "check_inventory",
            "description": "Check the available stock for a product.",
            "parameters": {
                "type": "object",
                "properties": {
                    "product_id": {
                        "type": "string",
                        "description": "The unique product ID."
                    }
                },
                "required": ["product_id"]
            }
        }
    },

    {
        "type": "function",
        "function": {
            "name": "check_policy",
            "description": "Check the customer support policy for an issue type.",
            "parameters": {
                "type": "object",
                "properties": {
                    "issue_type": {
                        "type": "string",
                        "description": "The type of customer issue."
                    }
                },
                "required": ["issue_type"]
            }
        }
    },
# An API endpoint is the specific URL/address where your program sends a request to an API.
    {
        "type": "function",
        "function": {
            "name": "create_replacement",
            "description": "Create a replacement for an order.",
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id": {
                        "type": "string",
                        "description": "The unique order ID."
                    }
                },
                "required": ["order_id"]
            }
        }
    },

    {
        "type": "function",
        "function": {
            "name": "issue_refund",
            "description": "Issue a refund for an order.",
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id": {
                        "type": "string",
                        "description": "The unique order ID."
                    }
                },
                "required": ["order_id"]
            }
        }
    },

    {
        "type": "function",
        "function": {
            "name": "issue_store_credit",
            "description": "Issue store credit to a customer.",
            "parameters": {
                "type": "object",
                "properties": {
                    "customer_id": {
                        "type": "string",
                        "description": "The unique customer ID."
                    },
                    "amount": {
                        "type": "number",
                        "description": "The amount of store credit."
                    }
                },
                "required": ["customer_id", "amount"]
            }
        }
    },

    {
        "type": "function",
        "function": {
            "name": "verify_transaction",
            "description": "Verify whether a refund, replacement, or store-credit transaction was successfully completed.",
            "parameters": {
                "type": "object",
                "properties": {
                    "transaction_id": {
                        "type": "string",
                        "description": "The unique transaction ID."
                    }
                },
                "required": ["transaction_id"]
            }
        }
    }
]
# messages = [
#     {   # role tells the LLM who/where the message came from in the conversation.
#         "role": "user",
#         "content": "Customer C101 says their order O501 has a problem. Investigate the issue and resolve it appropriately."
#     }
# ]
messages = [
        {
            "role": "user",
            "content": """
            Customer C101 says their order O501 has a problem.
            Investigate the issue and resolve it appropriately.
            Use the available tools as needed.
            Verify any successful transaction before giving the final answer.
            """
        }
]
while True: # The LLM decides → Python executes → result goes back → LLM decides again.
    response = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=messages,
        tools=tools,
        tool_choice="auto"
    )
    message = response.choices[0].message
    if message.tool_calls: 
        # tool_call is the specific tool request made by the LLM. 
        # Think of it as : "I want to call get_customer with customer_id = C101."
        tool_call = message.tool_calls[0] # "Take the first tool request made by the LLM."
        print("TOOL NAME:")
        print(tool_call.function.name)
        print("\nARGUMENTS:")
        #JSON Text
        # print(tool_call.function.arguments)
        # Why are the arguments a string?
        # The API usually gives the arguments in JSON-formatted text, so we'll convert them into a Python dictionary.
        function_name = tool_call.function.name
        arguments = json.loads(tool_call.function.arguments) # {"order_id":"O503"}
        print(arguments)
        print()
        function = available_tools[function_name]
        result = function(**arguments) # No need to manually write (get_customer(arguments["customer_id"]))
        # print(result)
        messages.append(message) # "I want to call get_customer with C101";The LLM needs to see what it previously requested and what the tool returned.
        # Because the API expects the tool result as message content, 
        # and JSON is a convenient structured format for passing data from Python to the LLM.
    #   messages:
    # 1. User:
    #    Get customer information for C101
    # 2. LLM:
    #    I want to call get_customer
    #    customer_id = C101
        messages.append({
            "role": "tool",
            "tool_call_id": tool_call.id, # The tool_call.id is a unique identifier for that particular tool call.
            "content": json.dumps(result)
        })
        # "LLM, here's the entire conversation again, including the result of the tool. Now decide what to do."
        # final_response = client.chat.completions.create(
        #     model="openai/gpt-oss-120b",
        #     messages=messages,
        #     tools=tools
        # )
        # print(final_response.choices[0].message.content)
    else:
        print("LLM RESPONSE:")
        print(message.content)
        break

    # Why are the arguments a string?
    # The API usually gives the arguments in JSON-formatted text, so we'll convert them into a Python dictionary.
# Instead, your Python program basically says:
# "Here are the tools. Here are their results. You decide what to do."
# That's the agentic part of your project.
# One small distinction: the LLM isn't magically deciding based on hidden business rules. 
# You provide those rules through the policy tool/data and tool descriptions,
#  and the LLM reasons over the information it receives.

# but only the permission to replacement is allow and suppose for refund it is also allowed then llm makes its own decision right
# Yes — exactly. 🔥
# If the policy says both are allowed, for example:
# Refund       → allowed ✅
# Replacement  → allowed ✅
# Store credit → allowed ✅
# then the LLM has to decide which resolution is appropriate based on the other information it has.

# Policy tool = tells the LLM what is permitted.
# Other tools = give the LLM the current situation.
# LLM = chooses among the permitted options.
# That's the key agentic behavior you're demonstrating.

# One caveat: if multiple options are equally valid, 
# the LLM's choice isn't necessarily deterministic or guaranteed to match a company's preferred priority.
#  If you need a strict business priority such as "always prefer replacement over refund",
#  that priority should be explicitly encoded in your policy/business rules rather than left entirely to the model.

# the description of the functions allows the llm to choose them right'
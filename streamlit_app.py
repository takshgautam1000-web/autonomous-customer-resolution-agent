
import os
import json
import streamlit as st
from dotenv import load_dotenv
from groq import Groq

from tools.customer_tools import get_customer
from tools.order_tools import get_order
from tools.inventory_tools import check_inventory
from tools.poilcy_tools import check_policy
from tools.resolution_tools import (
    issue_refund,
    create_replacement,
    issue_store_credit,
)
from tools.verification_tools import verify_transaction


load_dotenv()

st.set_page_config(
    page_title="Autonomous Customer Resolution Agent",
    page_icon="🤖",
    layout="wide",
)

st.title("🤖 Autonomous Customer Resolution Agent")
st.caption(
    "Investigate → Decide → Act → Observe → Replan → Verify"
)

# -----------------------------
# Tool registry
# -----------------------------

available_tools = {
    "get_customer": get_customer,
    "get_order": get_order,
    "check_policy": check_policy,
    "check_inventory": check_inventory,
    "create_replacement": create_replacement,
    "issue_refund": issue_refund,
    "issue_store_credit": issue_store_credit,
    "verify_transaction": verify_transaction,
}

tools = [
    {
        "type": "function",
        "function": {
            "name": "get_customer",
            "description": "Get customer information using the customer ID.",
            "parameters": {
                "type": "object",
                "properties": {
                    "customer_id": {
                        "type": "string",
                        "description": "The unique customer ID.",
                    }
                },
                "required": ["customer_id"],
            },
        },
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
                        "description": "The unique order ID.",
                    }
                },
                "required": ["order_id"],
            },
        },
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
                        "description": "The unique product ID.",
                    }
                },
                "required": ["product_id"],
            },
        },
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
                        "description": "The type of customer issue.",
                    }
                },
                "required": ["issue_type"],
            },
        },
    },
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
                        "description": "The unique order ID.",
                    }
                },
                "required": ["order_id"],
            },
        },
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
                        "description": "The unique order ID.",
                    }
                },
                "required": ["order_id"],
            },
        },
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
                        "description": "The unique customer ID.",
                    },
                    "amount": {
                        "type": "number",
                        "description": "The amount of store credit.",
                    },
                },
                "required": ["customer_id", "amount"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "verify_transaction",
            "description": (
                "Verify whether a refund, replacement, or store-credit "
                "transaction was successfully completed."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "transaction_id": {
                        "type": "string",
                        "description": "The unique transaction ID.",
                    }
                },
                "required": ["transaction_id"],
            },
        },
    },
]


def run_agent(customer_id, order_id, issue):
    api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        raise RuntimeError(
            "GROQ_API_KEY is missing. Add it to your local .env file."
        )

    client = Groq(api_key=api_key)

    messages = [
        {
            "role": "user",
            "content": f"""
Customer {customer_id} says their order {order_id} has the following issue:

{issue}

Investigate the issue and resolve it appropriately.
Use the available tools as needed.
Verify any successful transaction before giving the final answer.
""",
        }
    ]

    events = []

    # The LLM decides → Python executes → observation goes back → LLM decides again.
    for _ in range(20):
        response = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=messages,
            tools=tools,
            tool_choice="auto",
        )

        message = response.choices[0].message

        if not message.tool_calls:
            return message.content, events

        # Preserve the assistant tool-call message so the LLM has the
        # complete intermediate task state on the next iteration.
        messages.append(message)

        # Handle every tool call returned in this assistant message.
        for tool_call in message.tool_calls:
            function_name = tool_call.function.name
            arguments = json.loads(tool_call.function.arguments)

            events.append(
                {
                    "type": "tool_call",
                    "name": function_name,
                    "arguments": arguments,
                }
            )

            function = available_tools.get(function_name)

            if function is None:
                result = {
                    "success": False,
                    "error": f"Unknown tool: {function_name}",
                }
            else:
                try:
                    result = function(**arguments)
                except Exception as exc:
                    result = {
                        "success": False,
                        "error": str(exc),
                    }

            events.append(
                {
                    "type": "tool_result",
                    "name": function_name,
                    "result": result,
                }
            )

            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(result),
                }
            )

    return (
        "The agent reached its maximum number of reasoning steps without "
        "producing a final resolution.",
        events,
    )


# -----------------------------
# UI
# -----------------------------

with st.sidebar:
    st.header("Case Input")

    customer_id = st.text_input("Customer ID", value="C101")
    order_id = st.text_input("Order ID", value="O501")
    issue = st.text_area(
        "Customer issue",
        value="The product is defective and I need a resolution.",
        height=120,
    )

    run = st.button(
        "🚀 Resolve Customer Issue",
        type="primary",
        use_container_width=True,
    )

    st.divider()
    st.markdown("### Demo cases")
    st.markdown(
        """
        **O501** — defective product, out of stock  
        Demonstrates failure → replanning → store credit → verification.

        **O502** — delivered order, replacement stock available  
        Demonstrates replacement → verification.

        **O999** — invalid order  
        Demonstrates safe handling without an invalid state change.
        """
    )

if run:
    if not customer_id.strip() or not order_id.strip() or not issue.strip():
        st.error("Please provide customer ID, order ID, and issue.")
    else:
        st.subheader("Agent Execution")

        try:
            with st.spinner("Agent is investigating and resolving the case..."):
                final_answer, events = run_agent(
                    customer_id.strip(),
                    order_id.strip(),
                    issue.strip(),
                )

            for event in events:
                if event["type"] == "tool_call":
                    with st.expander(
                        f"🔧 {event['name']}",
                        expanded=True,
                    ):
                        st.code(
                            json.dumps(event["arguments"], indent=2),
                            language="json",
                        )

                elif event["type"] == "tool_result":
                    result = event["result"]
                    success = (
                        isinstance(result, dict)
                        and result.get("success") is True
                    )

                    if success:
                        st.success(
                            f"✓ {event['name']} returned successfully"
                        )
                    else:
                        st.warning(
                            f"⚠ {event['name']} returned: "
                            f"{json.dumps(result)}"
                        )

                    with st.expander(
                        f"Observation from {event['name']}",
                        expanded=False,
                    ):
                        st.code(
                            json.dumps(result, indent=2),
                            language="json",
                        )

            st.subheader("Final Resolution")
            st.success(final_answer)

        except Exception as exc:
            st.error(f"Agent execution failed: {exc}")

else:
    st.info(
        "Enter a customer case and click **Resolve Customer Issue**. "
        "The interface will show the agent's tool calls, observations, "
        "and final verified resolution."
    )

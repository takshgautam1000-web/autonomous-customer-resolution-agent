# 🤖 Autonomous Customer Resolution Agent

### Track 3 — Smart Automation  
### Problem Statement 5 — Autonomous Customer Resolution Agent

> **An agent that doesn't just answer customer tickets — it investigates, decides, acts, adapts, and verifies.**

---

## 🚀 Overview

Customer support systems often stop at **ticket classification or response generation**.

This project takes a different approach.

We built an **autonomous customer-resolution agent** that can interact with multiple simulated enterprise systems to actually resolve a customer's issue.

Given a customer request, the agent can:

1. Understand the customer's goal
2. Retrieve customer and order information
3. Check inventory and relevant support policies
4. Decide which resolution is appropriate
5. Execute a state-changing action
6. Observe the result
7. Replan if the chosen action is blocked
8. Verify the successful transaction
9. Provide the final resolution to the customer

The system uses an LLM as the **decision-making/orchestration layer**, while Python tools interact with the simulated enterprise environment.

---

# 🎯 Alignment With the Problem Statement

The solution was designed directly around the required agentic workflow.

| Problem Requirement | Our Implementation |
|---|---|
| Understand customer's goal | LLM interprets the customer request |
| Retrieve customer information | `get_customer` |
| Retrieve order information | `get_order` |
| Retrieve inventory information | `check_inventory` |
| Retrieve policy information | `check_policy` |
| Select an appropriate resolution | LLM chooses among available resolution tools |
| Execute state-changing action | Refund / replacement / store credit tools |
| Verify state change | `verify_transaction` |
| Adapt when action is blocked | LLM receives tool failure and selects another available action |
| Maintain task state | Conversation messages contain previous tool calls and results |
| Failure/conflict scenario | O501 refund-service failure |
| Escalate when objective cannot safely be completed | Agent avoids taking action when required information/order is invalid |

This directly targets the problem's central requirement:

> **The system must autonomously pursue a goal through multiple tool interactions rather than merely generate a response.**

---

# 🧠 What Makes It Agentic?

The key difference is that the system does **not use a fixed workflow**.

A traditional hardcoded workflow could be:

```text
Customer says "damaged"
        ↓
Check inventory
        ↓
Create replacement
        ↓
Done
```

Our system instead works as a feedback loop:

```text
                 ┌───────────────┐
                 │      USER     │
                 └───────┬───────┘
                         ↓
                 ┌───────────────┐
                 │      LLM      │
                 │   Decision    │
                 │     Layer     │
                 └───────┬───────┘
                         ↓
                    Tool Call
                         ↓
                 ┌───────────────┐
                 │ Python Tool   │
                 │ Enterprise    │
                 │ Environment   │
                 └───────┬───────┘
                         ↓
                    Observation
                         ↓
                 ┌───────────────┐
                 │      LLM      │
                 │ Re-evaluates  │
                 └───────┬───────┘
                         ↓
                    Next Action
                         ↓
                        ...
                         ↓
                 ┌───────────────┐
                 │   Verified    │
                 │   Resolution  │
                 └───────────────┘
```

The next action is selected from the **current state and previous tool results**.

The application does not contain a hardcoded sequence such as:

```python
if issue == "damaged":
    create_replacement()
```

Instead, the LLM receives the available tool descriptions and decides which capability is needed.

---

# 🏗️ System Architecture

```text
                         CUSTOMER REQUEST
                                │
                                ▼
                    ┌──────────────────────┐
                    │       LLM Agent      │
                    │                      │
                    │ Understand + Decide  │
                    └──────────┬───────────┘
                               │
                       Tool Call + Arguments
                               │
                               ▼
                    ┌──────────────────────┐
                    │   Tool Dispatcher    │
                    │  available_tools{}   │
                    └──────────┬───────────┘
                               │
              ┌────────────────┼─────────────────┐
              │                │                 │
              ▼                ▼                 ▼
        Customer DB       Order System      Inventory
        get_customer       get_order       check_inventory
              │                │                 │
              └────────────────┼─────────────────┘
                               │
                               ▼
                         Policy System
                        check_policy
                               │
                               ▼
                       Resolution Tools
              ┌────────────────┼────────────────┐
              ▼                ▼                ▼
         issue_refund    create_replacement   store_credit
              │                │                │
              └────────────────┼────────────────┘
                               ▼
                      Verification System
                       verify_transaction
                               │
                               ▼
                          FINAL RESULT
```

---

# 🔧 Tools

The agent currently has the following capabilities:

| Tool | Purpose | Type |
|---|---|---|
| `get_customer` | Retrieve customer information | Read |
| `get_order` | Retrieve order information | Read |
| `check_inventory` | Check product stock | Read |
| `check_policy` | Retrieve applicable support policy | Read |
| `issue_refund` | Attempt a refund | State-changing |
| `create_replacement` | Create a replacement order | State-changing |
| `issue_store_credit` | Issue customer credit | State-changing |
| `verify_transaction` | Verify completed transaction | Verification |

The tool definitions expose each function's:

- Name
- Description
- Parameters
- Required arguments
- Argument types

For example:

```python
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
}
```

This allows the LLM to understand **what a tool does and what information it needs** before deciding whether to call it.

---

# 🔌 LLM Tool Calling

The project uses Groq's tool/function-calling interface.

The process is:

```text
1. Send user request + available tools
                 ↓
2. LLM selects a tool
                 ↓
3. API returns tool_call
                 ↓
4. Extract function name + arguments
                 ↓
5. Python finds corresponding function
                 ↓
6. Python executes the function
                 ↓
7. Result is returned to the LLM
                 ↓
8. LLM decides the next action
```

For example, the LLM may generate:

```json
{
    "name": "get_order",
    "arguments": {
        "order_id": "O503"
    }
}
```

The application extracts:

```python
function_name = tool_call.function.name
arguments = json.loads(tool_call.function.arguments)
```

Then maps the requested name to the real Python function:

```python
function = available_tools[function_name]
```

and executes it:

```python
result = function(**arguments)
```

The result is then added to the conversation so the LLM can continue reasoning.

---

# 🧩 Tool Dispatcher

The project maintains a mapping between the names exposed to the LLM and the actual Python implementations:

```python
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
```

This creates a clean separation:

### `tools`

Defines **what the LLM can request**.

### `available_tools`

Defines **what Python actually executes**.

The LLM does not directly execute Python functions.

---

# 🔄 Persistent Task State

The agent maintains the task state through the `messages` conversation.

After the LLM requests a tool, the application stores the assistant's tool-call message:

```python
messages.append(message)
```

Then it adds the tool's result:

```python
messages.append({
    "role": "tool",
    "tool_call_id": tool_call.id,
    "content": json.dumps(result)
})
```

This means the next LLM call can see:

```text
User request
      +
Previous tool request
      +
Tool result
      +
Previous context
```

and make its next decision using the accumulated state.

---

# 🔁 Replanning and Failure Recovery

This is one of the most important parts of the project.

The agent is not required to succeed on its first action.

### Example: O501

The simulated environment contains:

```text
Order: O501
Customer: C101
Product: P201
Product: Wireless Headphones
Stock: 0
```

The refund tool for this test case is deliberately configured to simulate:

```text
REFUND_SERVICE_UNAVAILABLE
```

The agent therefore encounters:

```text
Attempted resolution
        ↓
Refund unavailable
        ↓
Observation returned to LLM
        ↓
LLM reassesses available options
        ↓
Store credit selected
        ↓
Transaction created
        ↓
Verification
```

This demonstrates the required **action → observation → replanning** behavior.

The fallback is not implemented as a fixed:

```python
if refund_failed:
    issue_store_credit()
```

Instead, the failed tool result is returned to the LLM, which can select another available resolution.

---

# 📋 Policy-Driven Decisions

Policies are stored as structured data and accessed through the policy tool.

Example policy structure:

```json
{
    "damaged": {
        "replacement": true,
        "refund": true,
        "store_credit": true,
        "return_window_days": 7
    },
    "late_delivery": {
        "replacement": true,
        "refund": false,
        "store_credit": true,
        "return_window_days": 0
    }
}
```

The policy tool provides the LLM with information about which resolutions are permitted for an issue.

The LLM then combines policy information with other evidence such as:

- Order status
- Delivery timing
- Inventory availability
- Payment status
- Tool failures

to select an appropriate action.

> **Important design choice:** the LLM is the decision/orchestration layer; the enterprise tools remain responsible for performing the actual operations.

---

# ✅ Verification

A resolution is not treated as complete merely because a state-changing tool was called.

After a successful resolution, the agent can call:

```text
verify_transaction
```

using the returned transaction ID.

The intended flow is:

```text
Resolution Tool
      ↓
Transaction ID
      ↓
verify_transaction
      ↓
Successful verification
      ↓
Final customer response
```

This provides an explicit **action → observation → verification** cycle.

---

# 🧪 Demonstrated Scenarios

The system was tested against multiple situations corresponding to the problem statement.

---

## 🧪 Scenario 1 — Blocked Refund + Replanning

### Input

```text
Customer C101 says their order O501 has a problem.
Investigate and resolve it appropriately.
```

### Observed tool sequence

```text
get_order
     ↓
check_inventory
     ↓
check_policy
     ↓
issue_refund
     ↓
REFUND_SERVICE_UNAVAILABLE
     ↓
issue_store_credit
     ↓
verify_transaction
```

### Result

The refund service was unavailable.

The agent adapted by selecting store credit, then verified the resulting transaction.

**✅ Passed**

### Why this matters

This is the strongest demonstration of the project's agentic behavior:

> **The environment changed the available path, and the agent adapted instead of following a fixed workflow.**

---

# 🧪 Scenario 2 — Replacement Available

### Input

```text
Customer C102 says their order O502 has a problem.
Investigate and resolve it appropriately.
```

### Observed behavior

```text
get_order
     ↓
check_inventory
     ↓
create_replacement
     ↓
verify_transaction
```

The product was in stock, so the agent selected replacement and verified the resulting transaction.

**✅ Passed**

---

# 🧪 Scenario 3 — Late Delivery

### Input

```text
Customer C103 says their order O503 was delivered late.
Investigate the issue and resolve it appropriately.
```

The agent inspected the late-delivery situation and selected an available compensation.

```text
check_policy
     ↓
get_order
     ↓
issue_store_credit
     ↓
verify_transaction
```

The resulting transaction was successfully verified.

**✅ Passed**

---

# 🧪 Scenario 4 — Invalid Order

### Input

```text
Customer C101 says their order O999 has a problem.
Investigate and resolve it appropriately.
```

The agent checked the order and determined that `O999` did not exist.

It did **not** attempt a refund, replacement, or store credit.

Instead, it requested the correct order information.

**✅ Passed**

### Why this matters

The agent does not blindly execute a state-changing action when the necessary information is missing.

---

# 🧠 Example Agent Decision

A typical resolution can be represented as:

```text
Customer Issue
      │
      ▼
"Investigate the case"
      │
      ▼
     LLM
      │
      ├──── get_order ──────────────┐
      │                             │
      │                       Order information
      │                             │
      ├──── check_inventory ────────┤
      │                             │
      │                       Stock information
      │                             │
      ├──── check_policy ───────────┤
      │                             │
      │                       Policy information
      │                             │
      ▼                             │
     LLM ◄──────────────────────────┘
      │
      ▼
Choose resolution
      │
      ▼
Execute action
      │
      ▼
Observe result
      │
      ├──── Failure ────► Replan
      │
      ▼
Verify transaction
      │
      ▼
Final response
```

---

# 📁 Project Structure

```text
autonomous_customer_resolution/
│
├── agent.py
│
├── data/
│   ├── customers.json
│   ├── orders.json
│   ├── inventory.json
│   ├── policies.json
│   └── transactions.json
│
├── tools/
│   ├── customer_tools.py
│   ├── order_tools.py
│   ├── inventory_tools.py
│   ├── poilcy_tools.py
│   ├── resolution_tools.py
│   └── verification_tools.py
│
├── .env
├── .gitignore
└── README.md
```

> `.env` should never be committed to the repository.

---

# ⚙️ Technology Stack

- **Python** — agent runtime and tool execution
- **Groq API** — LLM inference and tool calling
- **JSON** — simulated enterprise data layer
- **python-dotenv** — environment variable management

---

# ▶️ Running the Project

## 1. Clone the repository

```bash
git clone <YOUR_REPOSITORY_URL>
cd autonomous_customer_resolution
```

## 2. Create a virtual environment

```bash
python -m venv .venv
```

On Windows:

```powershell
.venv\Scripts\activate
```

## 3. Install dependencies

```bash
pip install groq python-dotenv
```

## 4. Configure the API key

Create a `.env` file:

```env
GROQ_API_KEY=your_api_key_here
```

## 5. Run

```bash
python agent.py
```

---

# 🔐 Security

The API key is loaded from an environment variable:

```python
load_dotenv()

client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)
```

The API key should never be hardcoded or committed to the repository.

Recommended `.gitignore`:

```text
.env
.venv/
__pycache__/
```

---

# 🌟 Why This Approach?

The architecture separates three responsibilities:

### 🧠 LLM — Decision Making

The LLM:

- Understands the request
- Selects tools
- Interprets intermediate results
- Chooses the next action
- Replans after failures
- Produces the final response

### ⚙️ Python — Execution

Python:

- Executes the requested tools
- Reads and updates simulated data
- Returns structured observations
- Maintains the agent loop

### 🗄️ Simulated Enterprise Systems — Environment

The JSON-backed systems provide:

- Customer data
- Order data
- Inventory
- Policies
- Transactions

This separation allows the environment to change while the agent dynamically adapts its plan.

---

# 🏆 Agentic Requirements Coverage

| Agentic Requirement | Demonstrated? |
|---|---:|
| Goal-driven execution | ✅ |
| Multiple tool interaction | ✅ |
| Intermediate observations | ✅ |
| Persistent task state | ✅ |
| Dynamic tool selection | ✅ |
| State-changing actions | ✅ |
| Action verification | ✅ |
| Failure handling | ✅ |
| Replanning | ✅ |
| Changed-condition scenario | ✅ |
| Safe handling of invalid order | ✅ |

---

# 🔬 Key Technical Insight

The project is intentionally **not** a single LLM prompt that generates a customer-service response.

The LLM is embedded inside an execution loop:

```text
LLM decides
    ↓
Tool executes
    ↓
Environment changes / returns observation
    ↓
LLM receives observation
    ↓
LLM decides again
    ↓
...
```

This feedback loop is what turns the system from a simple chatbot into an **agentic system**.

---

# 🚧 Current Scope and Future Improvements

This prototype uses JSON files to simulate enterprise systems.

A production version could replace them with:

- SQL/NoSQL databases
- Real order-management APIs
- Payment/refund APIs
- Inventory services
- Enterprise policy/RAG systems
- Authentication and authorization
- Human escalation workflows
- Audit logs
- Agent observability dashboards

Critical business constraints can also be enforced deterministically by backend tools, while the LLM remains responsible for orchestration and adaptive decision-making.

---

# 🔮 Future Vision

The same architecture can be extended beyond customer support.

The agent could become a general **enterprise resolution layer** capable of coordinating:

```text
CRM
 │
 ├── Orders
 │
 ├── Inventory
 │
 ├── Payments
 │
 ├── Policies
 │
 ├── Logistics
 │
 └── Verification
```

Instead of merely telling an employee what to do, the system can **perform the investigation and execute the resolution itself**.

---

# 💡 Final Takeaway

### Traditional AI support

```text
Customer
   ↓
AI
   ↓
Generated response
```

### Our autonomous resolution agent

```text
Customer
   ↓
Understand
   ↓
Investigate
   ↓
Retrieve evidence
   ↓
Reason
   ↓
Act
   ↓
Observe
   ↓
Replan if necessary
   ↓
Verify
   ↓
Resolve
```

> **The objective is not to generate the best reply.  
> The objective is to successfully complete the customer's goal.**

---

## 👥 Project

**Autonomous Customer Resolution Agent**

**Track:** Smart Automation  
**Problem:** Autonomous Customer Resolution Agent

Built with **Python + Groq + LLM Tool Calling + Simulated Enterprise Systems**.

### Core principle

> **Understand → Investigate → Decide → Act → Observe → Replan → Verify → Resolve**
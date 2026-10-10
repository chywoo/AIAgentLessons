from langchain.tools import tool


# ----------------------------------------------------------------------
# Mock backend data
# ----------------------------------------------------------------------

ORDERS = {
    "12345": {
        "status": "shipped",
        "carrier": "UPS",
        "shipping_status": "Delayed by 7 days",
    },
    "67890": {
        "status": "shipped",
        "carrier": "FedEx",
        "shipping_status": "Out for delivery",
    },
}


# ----------------------------------------------------------------------
# Tools
# ----------------------------------------------------------------------

@tool
def lookup_order(order_id: str) -> str:
    """Look up basic order information such as status and carrier."""

    print(f"[TOOL] lookup_order(order_id={order_id})")

    order = ORDERS.get(order_id)

    if order is None:
        return f"Order {order_id} was not found."

    return (
        f"Order ID: {order_id}\n"
        f"Status: {order['status']}\n"
        f"Carrier: {order['carrier']}"
    )


@tool
def check_shipping(order_id: str) -> str:
    """Check the current shipping status of an order."""

    print(f"[TOOL] check_shipping(order_id={order_id})")

    order = ORDERS.get(order_id)

    if order is None:
        return f"Order {order_id} was not found."

    return (
        f"Order ID: {order_id}\n"
        f"Shipping status: {order['shipping_status']}"
    )


@tool
def create_ticket(order_id: str, issue: str) -> str:
    """Create a customer support ticket when the customer explicitly needs support or the issue cannot be resolved."""

    print(f"[TOOL] create_ticket(order_id={order_id}, issue={issue})")

    return (
        f"Support ticket created for order {order_id}.\n"
        f"Issue: {issue}\n"
        "Ticket ID: TICKET-1001"
    )


@tool
def create_ticket(
    issue: str,
) -> str:
    """Create a customer support ticket."""

    return (
        f"Support ticket created: "
        f"{issue}"
    )
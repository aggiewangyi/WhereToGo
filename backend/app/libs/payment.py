"""
支付服务封装。
可对接微信支付 / 支付宝等。
"""


async def create_payment(order_id: str, amount: float, description: str) -> dict:
    """创建支付订单"""
    # TODO: integrate real payment gateway
    return {"order_id": order_id, "status": "pending"}


async def query_payment(order_id: str) -> dict:
    """查询支付状态"""
    return {"order_id": order_id, "status": "unknown"}

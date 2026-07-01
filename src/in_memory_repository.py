from typing import Dict, List, Optional

from .domain import Order
from .repository import OrderRepository


class InMemoryOrderRepository(OrderRepository):
    def __init__(self) -> None:
        self._orders: Dict[str, Order] = {}

    def add(self, order: Order) -> None:
        self._orders[order.id] = order

    def get(self, order_id: str) -> Optional[Order]:
        return self._orders.get(order_id)

    def list_all(self) -> List[Order]:
        return list(self._orders.values())

    def remove(self, order_id: str) -> None:
        self._orders.pop(order_id, None)

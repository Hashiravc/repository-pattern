from .domain import Order
from .repository import OrderRepository


class OrderService:
    """Depende solo de la abstracción OrderRepository.
    No sabe -ni le importa- si los pedidos viven en SQLite o en memoria.
    """

    def __init__(self, repository: OrderRepository) -> None:
        self._repository = repository

    def place_order(self, customer_name: str, total_amount: float) -> Order:
        order = Order(customer_name=customer_name, total_amount=total_amount)
        self._repository.add(order)
        return order

    def apply_discount_to_order(self, order_id: str, percentage: float) -> Order:
        order = self._repository.get(order_id)
        if order is None:
            raise ValueError(f"Pedido {order_id} no encontrado")
        order.apply_discount(percentage)
        self._repository.add(order)  # actualiza
        return order

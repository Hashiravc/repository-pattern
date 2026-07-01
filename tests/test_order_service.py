import pytest
from src.in_memory_repository import InMemoryOrderRepository
from src.service import OrderService


def test_place_order_stores_it_in_repository():
    repo = InMemoryOrderRepository()
    service = OrderService(repo)

    order = service.place_order("Gustavo Mamani", 100.0)

    order_in_repo = repo.get(order.id)
    assert order_in_repo is not None
    assert order_in_repo.customer_name == "Gustavo Mamani"


def test_apply_discount_updates_total_amount():
    repo = InMemoryOrderRepository()
    service = OrderService(repo)
    order = service.place_order("Hashira", 200.0)

    updated = service.apply_discount_to_order(order.id, 25)

    assert updated.total_amount == 150.0

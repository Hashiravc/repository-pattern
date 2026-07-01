import os
from src.in_memory_repository import InMemoryOrderRepository
from src.sqlite_repository import SqliteOrderRepository
from src.service import OrderService


def run_demo(repository):
    service = OrderService(repository)
    order = service.place_order("Ariana Quispe", 250.00)
    print(f"Pedido creado: {order}")

    updated = service.apply_discount_to_order(order.id, 10)
    print(f"Pedido con descuento: {updated}")

    print("Todos los pedidos:", service._repository.list_all())


if __name__ == "__main__":
    print("--- Usando repositorio en memoria ---")
    run_demo(InMemoryOrderRepository())

    print("\n--- Usando repositorio SQLite (persistente) ---")
    db_file = "orders.db"
    # Limpiamos base de datos anterior para que la demo sea limpia
    if os.path.exists(db_file):
        try:
            os.remove(db_file)
        except OSError:
            pass
    run_demo(SqliteOrderRepository(db_file))

import sqlite3
from datetime import datetime, timezone
from typing import List, Optional

from .domain import Order
from .repository import OrderRepository


class SqliteOrderRepository(OrderRepository):
    def __init__(self, db_path: str = "orders.db") -> None:
        self._conn = sqlite3.connect(db_path)
        self._create_table()

    def _create_table(self) -> None:
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS orders (
                id TEXT PRIMARY KEY,
                customer_name TEXT NOT NULL,
                total_amount REAL NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        self._conn.commit()

    def add(self, order: Order) -> None:
        self._conn.execute(
            "INSERT OR REPLACE INTO orders VALUES (?, ?, ?, ?)",
            (order.id, order.customer_name, order.total_amount,
             order.created_at.isoformat()),
        )
        self._conn.commit()

    def get(self, order_id: str) -> Optional[Order]:
        row = self._conn.execute(
            "SELECT id, customer_name, total_amount, created_at FROM orders WHERE id = ?",
            (order_id,),
        ).fetchone()
        return self._row_to_order(row) if row else None

    def list_all(self) -> List[Order]:
        rows = self._conn.execute(
            "SELECT id, customer_name, total_amount, created_at FROM orders"
        ).fetchall()
        return [self._row_to_order(row) for row in rows]

    def remove(self, order_id: str) -> None:
        self._conn.execute("DELETE FROM orders WHERE id = ?", (order_id,))
        self._conn.commit()

    @staticmethod
    def _row_to_order(row) -> Order:
        return Order(
            id=row[0],
            customer_name=row[1],
            total_amount=row[2],
            created_at=datetime.fromisoformat(row[3]),
        )

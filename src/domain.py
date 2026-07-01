from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import uuid4


@dataclass
class Order:
    customer_name: str
    total_amount: float
    id: str = field(default_factory=lambda: str(uuid4()))
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def apply_discount(self, percentage: float) -> None:
        if not 0 <= percentage <= 100:
            raise ValueError("El descuento debe estar entre 0 y 100")
        self.total_amount -= self.total_amount * (percentage / 100)

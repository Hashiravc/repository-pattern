from abc import ABC, abstractmethod
from typing import List, Optional

from .domain import Order


class OrderRepository(ABC):
    """Contrato que toda implementación de persistencia debe cumplir.
    La lógica de negocio solo conoce esta interfaz, nunca los detalles
    de SQLite, memoria, MongoDB, etc.
    """

    @abstractmethod
    def add(self, order: Order) -> None:
        pass

    @abstractmethod
    def get(self, order_id: str) -> Optional[Order]:
        pass

    @abstractmethod
    def list_all(self) -> List[Order]:
        pass

    @abstractmethod
    def remove(self, order_id: str) -> None:
        pass

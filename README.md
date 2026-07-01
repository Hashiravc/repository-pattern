# Enterprise Design Patterns: The Repository Pattern in Practice

**Autor:** Hashira  
**Universidad:** Universidad Privada de Tacna (UPT)  
**Curso:** Patrones de Software  
**Basado en:** *Catalog of Patterns of Enterprise Application Architecture* (Martin Fowler, 2002)

---

## 1. Introducción

Martin Fowler, en su libro *Patterns of Enterprise Application Architecture* (2002), documentó un conjunto de soluciones recurrentes a problemas comunes en la construcción de software empresarial: organización de lógica de negocio, mapeo de objetos a bases de datos, estructuración de la capa de presentación, entre otros. Su catálogo online agrupa estos patrones en categorías como *Domain Logic Patterns*, *Data Source Architectural Patterns*, *Object-Relational Behavioral Patterns*, entre otros.

En este artículo desarrollamos el patrón **Repository** (perteneciente a la categoría de *Object-Relational Behavioral Patterns*) y lo acompañamos de una implementación práctica y funcional en Python.

---

## 2. ¿Qué es el patrón Repository?

Fowler define el **Repository** como una capa que media entre el dominio y la capa de acceso a datos, comportándose como una colección de objetos en memoria. La idea central es que el resto de la aplicación (los casos de uso, servicios, controladores) no debería saber si los datos provienen de una base de datos SQL, un archivo de texto, una API externa o una lista temporal en memoria. 

El repositorio oculta toda esta complejidad de infraestructura detrás de una interfaz simple:
* `add(entity)`
* `get(id)`
* `list_all()`
* `remove(id)`

### Problema que resuelve

Sin este patrón, es común ver consultas SQL o código del ORM (como SQLAlchemy, Django ORM, etc.) esparcidos por toda la lógica de negocio. Esto genera:
1. **Acoplamiento fuerte** entre la lógica de dominio y la tecnología de base de datos elegida.
2. **Dificultad para escribir pruebas unitarias** (puesto que se necesita levantar una base de datos real para cada ejecución de test).
3. **Duplicación de queries** similares en distintos puntos del sistema.

### Solución

Definir una interfaz abstracta (un contrato) que declare las operaciones sobre la colección de dominio, y luego implementar una o varias versiones concretas de esa interfaz (ej. una en memoria para pruebas rápidas y otra con SQLite para producción). El resto del sistema depende únicamente del contrato, jamás de las implementaciones.

---

## 3. Estructura y Código del Proyecto (Python)

El código de este repositorio modela un sistema simple de gestión de pedidos (`Order`) para una tienda. La estructura del proyecto está organizada de la siguiente manera:

```text
repository-pattern/
├── src/
│   ├── __init__.py
│   ├── domain.py
│   ├── repository.py
│   ├── in_memory_repository.py
│   ├── sqlite_repository.py
│   └── service.py
├── tests/
│   ├── __init__.py
│   └── test_order_service.py
├── main.py
├── requirements.txt
└── README.md
```

### 3.1 Entidad de Dominio
La entidad `Order` es una clase pura que no conoce nada acerca de bases de datos. Contiene la lógica de dominio del pedido (por ejemplo, la aplicación de descuentos).

* **Archivo:** [src/domain.py](src/domain.py)

```python
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
```

### 3.2 Interfaz del Repositorio (El Contrato)
Define los métodos abstractos que cualquier mecanismo de persistencia debe implementar obligatoriamente.

* **Archivo:** [src/repository.py](src/repository.py)

```python
from abc import ABC, abstractmethod
from typing import List, Optional
from .domain import Order

class OrderRepository(ABC):
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
```

### 3.3 Implementación en Memoria (Ideal para Testing)
Permite realizar pruebas rápidas y desacopladas sin interactuar con un motor de base de datos.

* **Archivo:** [src/in_memory_repository.py](src/in_memory_repository.py)

```python
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
```

### 3.4 Implementación en SQLite (Producción/Persistencia Real)
Implementa el acceso a la base de datos SQLite relacional real. Mapea la entidad al modelo de base de datos y viceversa.

* **Archivo:** [src/sqlite_repository.py](src/sqlite_repository.py)

```python
import sqlite3
from datetime import datetime
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
```

### 3.5 Caso de Uso / Lógica de Negocio (Service Layer)
El servicio depende **únicamente** de la interfaz abstracta `OrderRepository`. Esto garantiza que los detalles de SQLite o de memoria no se mezclen con la lógica del negocio.

* **Archivo:** [src/service.py](src/service.py)

```python
from .domain import Order
from .repository import OrderRepository

class OrderService:
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
        self._repository.add(order)  # Guarda los cambios actualizados
        return order
```

### 3.6 Demostración de Intercambio de Implementaciones
La función `run_demo` corre de forma idéntica sin importar qué repositorio se le inyecte, lo que demuestra el aislamiento de la infraestructura de persistencia.

* **Archivo:** [main.py](main.py)

---

## 4. Pruebas Unitarias (Ventaja Directa)

Una de las mayores ventajas del desacoplamiento que ofrece el patrón es que escribir pruebas unitarias es extremadamente simple y rápido, ya que no se requiere levantar una base de datos real.

* **Archivo:** [tests/test_order_service.py](tests/test_order_service.py)

```python
import pytest
from src.in_memory_repository import InMemoryOrderRepository
from src.service import OrderService

def test_place_order_stores_it_in_repository():
    repo = InMemoryOrderRepository()
    service = OrderService(repo)

    order = service.place_order("Gustavo Mamani", 100.0)

    assert repo.get(order.id) is not None
    assert repo.get(order.id).customer_name == "Gustavo Mamani"

def test_apply_discount_updates_total_amount():
    repo = InMemoryOrderRepository()
    service = OrderService(repo)
    order = service.place_order("Hashira", 200.0)

    updated = service.apply_discount_to_order(order.id, 25)

    assert updated.total_amount == 150.0
```

---

## 5. Relación con otros patrones del catálogo

* **Data Mapper:** El repositorio suele apoyarse en un mapeador de datos (Data Mapper) para traducir el objeto de dominio a tablas relacionales de la base de datos.
* **Unit of Work:** En aplicaciones complejas, el repositorio interactúa con un Unit of Work para agrupar múltiples transacciones u operaciones de escritura en una única transacción de base de datos coherente.
* **Service Layer:** `OrderService` encapsula los casos de uso, actuando como una capa de servicio (Service Layer) que orquesta la ejecución lógica y delega la persistencia al Repositorio.

---

## 6. Conclusión

El patrón **Repository** es una de las herramientas fundamentales en el diseño de arquitecturas limpias (*Clean Architecture*, *Hexagonal Architecture*) porque desacopla el "**qué**" (la lógica pura de negocio) del "**cómo**" (la infraestructura de persistencia de datos). Esta implementación en Python ilustra cómo es factible intercambiar el repositorio SQLite por uno en memoria de forma instantánea sin requerir modificaciones en la lógica del caso de uso.

---

## 7. Instrucciones para Ejecutar y Probar el Proyecto

Sigue estos pasos para levantar el proyecto localmente:

### 1. Clonar el repositorio
```bash
git clone <URL_DE_ESTE_REPOSITORIO>
cd repository-pattern
```

### 2. Configurar el Entorno Virtual (Opcional pero recomendado)
```bash
python -m venv venv
# Activar en Windows (PowerShell):
.\venv\Scripts\Activate.ps1
# Activar en Linux/macOS:
source venv/bin/activate
```

### 3. Instalar Dependencias
```bash
pip install -r requirements.txt
```

### 4. Ejecutar la Demostración
Corre la aplicación de prueba que ejecuta las operaciones sobre ambos repositorios (en memoria y SQLite):
```bash
python main.py
```

### 5. Ejecutar las Pruebas Unitarias
Ejecuta las pruebas usando `pytest` para verificar que la lógica de negocio responde correctamente:
```bash
pytest
```

---

## Referencias
* Fowler, M. (2002). *Patterns of Enterprise Application Architecture*. Addison-Wesley.
* Fowler, M. *Repository*. Catalog of Patterns of Enterprise Application Architecture. https://martinfowler.com/eaaCatalog/repository.html
* Catálogo completo: https://martinfowler.com/eaaCatalog/

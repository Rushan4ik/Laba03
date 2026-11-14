from dataclasses import dataclass
from src.transport_catalog.errors import InvalidEntityError
from src.transport_catalog.constants import CATEGORIES, TRANSPORT_TYPES


@dataclass(frozen=True)
class TransportRoute:
    id: str
    name: str
    category: str
    year: int
    transport_type: str
    start_point: str
    end_point: str

    def __post_init__(self):
        if not isinstance(self.id, str) or not self.id.strip():
            raise InvalidEntityError("ID должен быть непустой строкой")
        if not isinstance(self.name, str) or not self.name.strip():
            raise InvalidEntityError("Название не может быть пустым")
        if (not isinstance(self.year, int)) or isinstance(self.year, bool) or (self.year < 1800 or self.year > 2100):
            raise InvalidEntityError(f"Некорректный год: {self.year}")
        if not isinstance(self.transport_type, str) or self.transport_type not in TRANSPORT_TYPES:
            raise InvalidEntityError("Неизвестный тип транспорта")
        if not isinstance(self.category, str) or self.category not in CATEGORIES:
            raise InvalidEntityError("Неизвестная категория транспорта")
        if not isinstance(self.start_point, str) or not self.start_point.strip():
            raise InvalidEntityError("Начальная точкa обязательна")
        if not isinstance(self.end_point, str) or not self.end_point.strip():
            raise InvalidEntityError("Конечная точка обязательна")

        



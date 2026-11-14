from src.transport_catalog.entity import TransportRoute
from src.transport_catalog.errors import DuplicateIdError, InvalidEntityError, NotFoundError, NothingToUndoError
from dataclasses import dataclass, asdict
from enum import Enum


class ActionType(Enum):
    add = "add"
    remove = "remove"

@dataclass
class UndoHelper:
    type_of_act: ActionType 
    item_id: str
    item_data: dict | None = None
    index_item: int | None = None

class TransportCatalog:
    def __init__(self) -> None:
        self._items: dict[str, TransportRoute] = {} # мгновенный поиск по id O(1)
        self._order: list[str] = [] # список для хранения порядка
        self._undo_stack: list[UndoHelper] = [] # стэк для undo операции

    def get(self, item_id) -> TransportRoute:
        if item_id not in self._items:
            raise NotFoundError("Объект не найден ")
        return self._items[item_id]

    def add(self, item: TransportRoute) -> None:
        if not isinstance(item, TransportRoute):
            raise InvalidEntityError("Можно добавлять только TransportRoute")
        if item.id in self._items:
            raise DuplicateIdError(f"ID уже существует: {item.id}")
        self._items[item.id] = item
        self._order.append(item.id)
        self._undo_stack.append(UndoHelper(type_of_act = ActionType.add, item_id = item.id, item_data = asdict(item)))

    def remove(self, item_id) -> None:
        if item_id not in self._items:
            raise NotFoundError("Объекта не существует")
        idx = self._order.index(item_id)
        copy_data_item = asdict(self._items[item_id])

        del self._items[item_id]
        self._order.pop(idx)

        self._undo_stack.append(UndoHelper( type_of_act = ActionType.remove, item_id = item_id, item_data = copy_data_item, index_item = idx))


    # Поиск
    def find_by_category(self, category: str) -> list[TransportRoute]:
        if not isinstance(category, str):
            raise InvalidEntityError("Неверно переданная категория")
        return [
            item for item in self if item.category.lower() == category.lower()
        ]

    def find_by_name(self, query) -> list[TransportRoute]:
        if not isinstance(query, str):
            raise InvalidEntityError("Запрос должен быть строкой")
        return [
            item for item in self if query.lower() in item.name.lower()
        ]

    def read_only_view(self) -> "CatalogView":
        return CatalogView(self)

    # magic methods
    def __len__(self) -> int:
        return len(self._items)

    def __iter__(self):
        """Итерация в порядке добавления; после undo remove элемент возвращается на прежнее место."""    
        return iter(tuple(self._items[i] for i in self._order))

    def __contains__(self, item_id) -> bool:
        return item_id in self._items

    def undo(self) -> None:
        if not self._undo_stack:
            raise NothingToUndoError("Нечего откатывать")

        rollback = self._undo_stack[-1]

        if rollback.type_of_act == ActionType.add:
            if rollback.item_id not in self._items:
                raise NotFoundError(f"Невозможно откатить добавление ID {rollback.item_id} не найден")
            del self._items[rollback.item_id]
            self._order.remove(rollback.item_id)

        elif rollback.type_of_act == ActionType.remove:
            if rollback.item_id in self._items:
                raise DuplicateIdError(f"Невозможно откатить удаление ID {rollback.item_id}  уже занят")
            route = TransportRoute(**rollback.item_data)
            self._items[route.id] = route
            self._order.insert(rollback.index_item, rollback.item_id)

        self._undo_stack.pop()

    def _replace_content(self, other: "TransportCatalog") -> None:
        self._items = dict(other._items)
        self._order = list(other._order)
        self._undo_stack.clear()


class CatalogView:
    def __init__(self, catalog: TransportCatalog):
        self.__catalog = catalog

    def get(self, item_id) -> TransportRoute:
        return self.__catalog.get(item_id)

    def find_by_category(self, category: str) -> list[TransportRoute]:
        return self.__catalog.find_by_category(category)

    def find_by_name(self, query: str) -> list[TransportRoute]:
        return self.__catalog.find_by_name(query)

    def __len__(self) -> int:
        return len(self.__catalog)

    def __iter__(self):
        return iter(self.__catalog)

    def __contains__(self, item_id) -> bool:
        return item_id in self.__catalog

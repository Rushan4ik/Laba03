# Лабораторная работа 3. Каталог объектов

Предметная область: **транспортные маршруты**. Пакет содержит предметную модель
(`TransportRoute`), каталог объектов (`TransportCatalog`) с поиском, undo и
read-only view, а также сохранение/загрузку каталога в JSON.

## Структура

```
src/transport_catalog/
    entity.py      # dataclass TransportRoute + инварианты (__post_init__)
    catalog.py     # TransportCatalog (add/get/remove, поиск, undo, view)
    storage.py     # CatalogStorage: save/load в JSON с format_version
    errors.py      # CatalogError и наследники
    constants.py   # справочники категорий, типов транспорта, версия формата
    __main__.py    # пример использования
tests/
    test_catalog.py
```

## Запуск примера

```bash
python -m src.transport_catalog
```

## Запуск тестов

```bash
python -m pytest tests/ -v
```

## Пример использования

```python
from src.transport_catalog.catalog import TransportCatalog
from src.transport_catalog.entity import TransportRoute
from src.transport_catalog.storage import CatalogStorage

catalog = TransportCatalog()
catalog.add(TransportRoute(
    id="bus-12", name="Автобус 12", category="городской", year=2026,
    transport_type="автобус", start_point="Вокзал", end_point="Больница №47",
))

catalog.find_by_name("автобус")       
catalog.find_by_category("городской")

CatalogStorage.save(catalog, "catalog.json")
CatalogStorage.load(catalog, "catalog.json")

catalog.undo()                          
view = catalog.read_only_view()         
```

## Особенности

- невалидная сущность не создаётся (`InvalidEntityError`), дубликат ID запрещён (`DuplicateIdError`);
- удаление отсутствующего ID вызывает `NotFoundError`;
- поиск по ID — за O(1) через словарь; методы поиска возвращают копии списков;
- порядок итерации детерминирован — порядок добавления;
- при повреждённом файле или неизвестной версии формата существующий каталог не изменяется.

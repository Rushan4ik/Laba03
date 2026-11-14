import json
import pytest

from src.transport_catalog.catalog import TransportCatalog
from src.transport_catalog.constants import CATEGORIES, TRANSPORT_TYPES, FORMAT_VERSION
from src.transport_catalog.entity import TransportRoute
from src.transport_catalog.errors import (
    CatalogError,
    CorruptedFileError,
    DuplicateIdError,
    InvalidEntityError,
    NotFoundError,
    UnsupportedFormatVersionError,
)
from src.transport_catalog.storage import CatalogStorage


def make_route(route_id: str = "bus-12", **overrides) -> TransportRoute:
    """Создаёт корректный маршрут с возможностью переопределения полей."""
    params = dict(
        id=route_id,
        name="Автобус 12",
        category="городской",
        year=2026,
        transport_type="автобус",
        start_point="Вокзал",
        end_point="Больница №47",
    )
    params.update(overrides)
    return TransportRoute(**params)


@pytest.fixture
def catalog() -> TransportCatalog:
    return TransportCatalog()


@pytest.fixture
def filled_catalog() -> TransportCatalog:
    cat = TransportCatalog()
    cat.add(make_route("bus-12", name="Автобус 12", category="городской", year=2020))
    cat.add(make_route("tram-3", name="Трамвай 3", category="пригородный", year=2021, transport_type="трамвай", start_point="Центр", end_point="Сад"))
    cat.add(make_route("bus-77", name="Автобус 77", category="междугородний", year=2022))
    return cat




def test_valid_entity_created():
    route = make_route()
    assert route.id == "bus-12"
    assert route.year == 2026
    assert route.transport_type in TRANSPORT_TYPES
    assert route.category in CATEGORIES


@pytest.mark.parametrize("field, bad_value", [
    ("id", ""),                   # пустой id
    ("id", "   "),                # id из пробелов
    ("id", None),                 # id не строка
    ("name", ""),                 # пустое название
    ("name", None),               # название не строка
    ("year", 1799),               # год ниже допустимого
    ("year", 2101),               # год выше допустимого
    ("year", True),               # bool не считается годом
    ("year", "2020"),             # год не int
    ("category", "воздушный"),    # категория вне справочника
    ("category", None),
    ("transport_type", "поезд"),  # тип вне справочника
    ("transport_type", None),
    ("start_point", ""),
    ("start_point", None),
    ("end_point", ""),
    ("end_point", None),
])
def test_invalid_entity_raises(field, bad_value):
    with pytest.raises(InvalidEntityError):
        make_route(**{field: bad_value})


def test_invalid_entity_is_base_catalog_error():
    with pytest.raises(CatalogError):
        make_route(year=1000)



def test_add_and_get(catalog):
    route = make_route()
    catalog.add(route)
    assert catalog.get("bus-12") is route
    assert len(catalog) == 1


def test_add_non_entity_rejected(catalog):
    with pytest.raises(InvalidEntityError):
        catalog.add({"id": "bus-12"})
    assert len(catalog) == 0  # объект не появился в каталоге


def test_get_missing_raises_not_found(catalog):
    with pytest.raises(NotFoundError):
        catalog.get("nope")


def test_remove(filled_catalog):
    filled_catalog.remove("bus-12")
    assert "bus-12" not in filled_catalog
    assert len(filled_catalog) == 2
    with pytest.raises(NotFoundError):
        filled_catalog.get("bus-12")


def test_remove_missing_raises_not_found_and_keeps_state(filled_catalog):
    before = list(filled_catalog)
    with pytest.raises(NotFoundError):
        filled_catalog.remove("ghost")
    assert list(filled_catalog) == before


def test_contains_and_len(filled_catalog):
    assert "tram-3" in filled_catalog
    assert "ghost" not in filled_catalog
    assert len(filled_catalog) == 3



def test_duplicate_id_rejected(catalog):
    catalog.add(make_route("bus-12"))
    with pytest.raises(DuplicateIdError):
        catalog.add(make_route("bus-12", name="Другой автобус"))
    assert len(catalog) == 1  # дубликат не добавился


def test_duplicate_id_is_catalog_error(catalog):
    catalog.add(make_route("bus-12"))
    with pytest.raises(CatalogError):
        catalog.add(make_route("bus-12"))



def test_find_by_category(filled_catalog):
    result = filled_catalog.find_by_category("пригородный")
    assert [r.id for r in result] == ["tram-3"]


def test_find_by_category_case_insensitive(filled_catalog):
    result = filled_catalog.find_by_category("ГОРОДСКОЙ")
    assert [r.id for r in result] == ["bus-12"]


def test_find_by_category_no_match(filled_catalog):
    assert filled_catalog.find_by_category("unknown") == []


def test_find_by_name_case_insensitive(filled_catalog):
    result = filled_catalog.find_by_name("автобус")
    assert sorted(r.id for r in result) == ["bus-12", "bus-77"]


def test_find_by_name_substring(filled_catalog):
    result = filled_catalog.find_by_name("ТРАМ")
    assert [r.id for r in result] == ["tram-3"]


def test_find_returns_copy_not_internal_list(filled_catalog):
    result = filled_catalog.find_by_category("городской")
    result.clear()
    assert len(filled_catalog) == 3 
    assert len(filled_catalog.find_by_category("городской")) == 1


def test_find_invalid_argument(filled_catalog):
    with pytest.raises(InvalidEntityError):
        filled_catalog.find_by_category(123)
    with pytest.raises(InvalidEntityError):
        filled_catalog.find_by_name(None)



def test_iteration_follows_add_order(filled_catalog):
    assert [r.id for r in filled_catalog] == ["bus-12", "tram-3", "bus-77"]


def test_iteration_order_after_remove(filled_catalog):
    filled_catalog.remove("tram-3")
    assert [r.id for r in filled_catalog] == ["bus-12", "bus-77"]


def test_iteration_deterministic(filled_catalog):
    assert [r.id for r in filled_catalog] == [r.id for r in filled_catalog]



def test_save_and_load_round_trip(filled_catalog, tmp_path):
    path = tmp_path / "catalog.json"
    CatalogStorage.save(filled_catalog, path)

    raw = json.loads(path.read_text(encoding="utf-8"))
    assert raw["format_version"] == FORMAT_VERSION
    assert len(raw["items"]) == 3

    new_catalog = TransportCatalog()
    CatalogStorage.load(new_catalog, path)
    assert list(new_catalog) == list(filled_catalog)
    assert new_catalog.get("bus-12") == filled_catalog.get("bus-12")


def test_load_returns_same_catalog_object(filled_catalog, tmp_path):
    path = tmp_path / "catalog.json"
    CatalogStorage.save(filled_catalog, path)
    result = CatalogStorage.load(filled_catalog, path)
    assert result is filled_catalog



def test_corrupted_json_file(filled_catalog, tmp_path):
    path = tmp_path / "catalog.json"
    path.write_text("{ это не json ", encoding="utf-8")
    before = list(filled_catalog), len(filled_catalog)
    with pytest.raises(CorruptedFileError):
        CatalogStorage.load(filled_catalog, path)
    assert (list(filled_catalog), len(filled_catalog)) == before


def test_missing_file_is_corrupted(filled_catalog, tmp_path):
    with pytest.raises(CorruptedFileError):
        CatalogStorage.load(filled_catalog, tmp_path / "missing.json")
    assert len(filled_catalog) == 3


def test_unknown_format_version(filled_catalog, tmp_path):
    path = tmp_path / "catalog.json"
    path.write_text(json.dumps({"format_version": FORMAT_VERSION + 1, "items": []}),
                    encoding="utf-8")
    before = list(filled_catalog), len(filled_catalog)
    with pytest.raises(UnsupportedFormatVersionError):
        CatalogStorage.load(filled_catalog, path)
    assert (list(filled_catalog), len(filled_catalog)) == before


def test_no_partial_change_on_invalid_items(filled_catalog, tmp_path):
    """Файл с невалидным элементом не должен менять существующий каталог."""
    path = tmp_path / "catalog.json"
    path.write_text(json.dumps({
        "format_version": FORMAT_VERSION,
        "items": [
            {"id": "bus-12", "name": "Автобус 12", "category": "городской", "year": 2020, "transport_type": "автобус", "start_point": "Вокзал", "end_point=": "Больница"},  # лишний "=" в ключе
        ],
    }), encoding="utf-8")
    before = list(filled_catalog), len(filled_catalog)
    with pytest.raises(CorruptedFileError):
        CatalogStorage.load(filled_catalog, path)
    assert (list(filled_catalog), len(filled_catalog)) == before


def test_items_must_be_list(filled_catalog, tmp_path):
    path = tmp_path / "catalog.json"
    path.write_text(json.dumps({"format_version": FORMAT_VERSION, "items": "oops"}),
                    encoding="utf-8")
    with pytest.raises(CorruptedFileError):
        CatalogStorage.load(filled_catalog, path)
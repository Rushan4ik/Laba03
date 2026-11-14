import json
from pathlib import Path

from src.transport_catalog.catalog import TransportCatalog
from src.transport_catalog.entity import TransportRoute
from src.transport_catalog.errors import CorruptedFileError, UnsupportedFormatVersionError, CatalogError
from src.transport_catalog.constants import FORMAT_VERSION

class CatalogStorage:
    @classmethod
    def save(cls, catalog: TransportCatalog, path: str | Path) -> None:
        path = Path(path)
        data = {
            "format_version": FORMAT_VERSION,
            "items": [
                {
                    "id": route.id,
                    "name": route.name,
                    "category": route.category,
                    "year": route.year,
                    "transport_type": route.transport_type,
                    "start_point": route.start_point,
                    "end_point": route.end_point,
                }
                for route in catalog
            ]
        }

        tmp_path = path.with_name(path.name + ".tmp")
        try:
            with open(tmp_path, "w", encoding="UTF-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            tmp_path.replace(path)
        finally:
            tmp_path.unlink(missing_ok=True)


    @classmethod
    def load(cls, catalog: TransportCatalog, path: str | Path) -> TransportCatalog:
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except (json.JSONDecodeError, UnicodeDecodeError, FileNotFoundError) as e:
            raise CorruptedFileError(f"Не удалось прочитать файл: {e}") from e

        if not isinstance(data, dict):
            raise CorruptedFileError("Корень документа должен быть объектом")
        version = data.get("format_version")
        if not isinstance(version, int) or version != FORMAT_VERSION:
            raise UnsupportedFormatVersionError(f"Ожидалась версия: {FORMAT_VERSION}, получена {version}")

        if not isinstance(data.get("items"), list):
            raise CorruptedFileError("Поле 'items' должно быть списком")
        
        new_catalog = TransportCatalog()
        for item in data["items"]:
            try:
                new_catalog.add(TransportRoute(**item))
            except (TypeError, CatalogError) as e:
                raise CorruptedFileError(f"Ошибка при загрузке элемента {item!r}: {e}") from e
        catalog._replace_content(new_catalog)
        return catalog






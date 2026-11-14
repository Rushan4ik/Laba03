from src.transport_catalog import TransportCatalog, TransportRoute, CatalogStorage
from pathlib import Path

def main():
    catalog = TransportCatalog()
    
    # Создаем тестовые маршруты
    route1 = TransportRoute(
        id="bus-12", name="Автобус 12", category="пригородный", 
        transport_type="автобус", year=2026, start_point="Вокзал", end_point="Больница №47"
    )
    route2 = TransportRoute(
        id="metro-1", name="Линия 1", category="городской", 
        transport_type="метро", year=1935, start_point="Сокольники", end_point="Парк Победы"
    )
    
    catalog.add(route1)
    catalog.add(route2)
    
    print(f"Получено по ID: {catalog.get('bus-12')}")
    print(f"Найдено по категории 'пригородный': {catalog.find_by_category('пригородный')}")
    print(f"Найдено по имени 'автобус': {catalog.find_by_name('автобус')}")
    
    for route in catalog:
        print(f"- {route.name} ({route.category})")
        
    catalog.remove("bus-12")
    print(f"Удалили 'bus-12'. Длина каталога: {len(catalog)}")
    
    catalog.undo()
    print(f"Сделали undo(). Длина каталога: {len(catalog)}")
    print(f"'bus-12' снова в каталоге: {'bus-12' in catalog}")

    # Сохранение и загрузка
    path = Path("catalog.json")
    CatalogStorage.save(catalog, path)
    print(f"\nКаталог сохранен в '{path}'")
    
    new_catalog = TransportCatalog()
    CatalogStorage.load(new_catalog, path)
    print(f"Каталог загружен из файла. Длина: {len(new_catalog)}")

if __name__ == "__main__":
    main()
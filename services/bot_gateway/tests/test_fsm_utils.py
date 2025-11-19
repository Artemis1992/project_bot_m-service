from ..api.categories_service import (
    Warehouse,
    Category,
    Subcategory,
    CategoriesServiceClient,
)
from ..fsm.handlers import (
    build_summary,
    serialize_warehouses,
    deserialize_warehouses,
)


def test_build_summary_includes_all_fields() -> None:
    data = {
        "warehouse_name": "Алматы",
        "category_name": "Авто",
        "subcategory_name": "Ремонт",
        "amount": 15000,
        "comment": "Плановое ТО",
        "file_info": {"file_name": "invoice.pdf"},
    }
    summary = build_summary(data)
    assert "Алматы" in summary
    assert "invoice.pdf" in summary


def test_serialize_deserialize_warehouses_roundtrip() -> None:
    warehouses = [
        Warehouse(
            id="almaty",
            name="Алматы",
            categories=[
                Category(
                    id="auto",
                    name="Авто",
                    subcategories=[
                        Subcategory(id="repair", name="Ремонт"),
                    ],
                )
            ],
        )
    ]
    serialized = serialize_warehouses(warehouses)
    restored = deserialize_warehouses(serialized)
    assert restored[0].name == "Алматы"
    assert restored[0].categories[0].subcategories[0].name == "Ремонт"


def test_find_categories_returns_expected_branch() -> None:
    warehouses = [
        Warehouse(
            id="almaty",
            name="Алматы",
            categories=[Category(id="auto", name="Авто", subcategories=[])],
        ),
        Warehouse(
            id="kapchagai",
            name="Капчагай",
            categories=[Category(id="rent", name="Аренда", subcategories=[])],
        ),
    ]
    result = CategoriesServiceClient.find_categories(warehouses, "kapchagai")
    assert len(result) == 1
    assert result[0].name == "Аренда"


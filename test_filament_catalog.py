from filament_catalog import (
    delete_product,
    find_product_by_sku,
    initialize_catalog,
    list_products,
    upsert_product,
)


def test_catalog_upsert_and_find():
    initialize_catalog()
    product = upsert_product({
        "sku": "TEST-PLA-001",
        "brand": "Test Brand",
        "material": "PLA",
        "filament_id": "GFL99",
        "parent_template": "Generic PLA",
        "base_id": "GFSL99_04",
        "color": "Red",
        "hex_color": "#FF0000",
        "nozzle_temp": 210,
        "bed_temp": 65,
    })

    assert any(item["sku"] == "TEST-PLA-001" for item in list_products())
    assert find_product_by_sku("TEST-PLA-001")["brand"] == "Test Brand"
    assert delete_product("TEST-PLA-001")

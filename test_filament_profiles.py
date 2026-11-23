from filament_profiles import (
    OFFICIAL_MATERIAL_TYPES,
    get_cloud_filament_type,
    get_filament_profile,
    normalize_filament_material,
    resolve_filament_label_fields,
)


def test_official_material_types_are_canonicalized():
    cases = {
        "PLA+": "PLA",
        "Tough PLA": "PLA",
        "Silk PLA": "PLA Silk",
        "XPLA": "PLA Basic",
        "PLAPastel": "PLA Pastel",
        "PLA Palette": "PLA Palette",
        "PLA Tough+": "PLA Tough+",
        "PLA Matte": "PLA Matte",
        "PLA CF": "PLA-CF",
        "PETG CF": "PETG-CF",
        "TPE": "TPU",
    }
    for input_value, expected in cases.items():
        assert normalize_filament_material(input_value) == expected


def test_official_types_have_profiles():
    for material in OFFICIAL_MATERIAL_TYPES:
        profile = get_filament_profile(material)
        assert profile.parent_template
        assert profile.base_id
        assert profile.filament_id


def test_generic_pastel_uses_generic_pla_profile():
    profile = get_filament_profile("PLA Pastel")
    assert profile.parent_template == "Generic PLA"
    assert profile.base_id == "GFSL99_04"
    assert profile.filament_id == "GFL99"


def test_sku_is_not_treated_as_a_material():
    assert normalize_filament_material("PFRBIPLA1751KG") == "PLA"
    assert normalize_filament_material("PFEXPLA1SYH1751KG") == "PLA"


def test_resolve_separates_sku_and_material():
    material, sku = resolve_filament_label_fields(
        "PFEXPLA1SYH1751KG",
        None,
    )
    assert material == "PLA"
    assert sku == "PFEXPLA1SYH1751KG"


def test_cloud_filament_type_uses_bambu_material_category():
    assert get_cloud_filament_type("PLA Pastel") == "PLA"
    assert get_cloud_filament_type("PLA-CF") == "PLA-CF"
    assert get_cloud_filament_type("PETG-CF") == "PETG-CF"

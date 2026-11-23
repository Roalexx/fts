import re
from typing import Dict, NamedTuple, Optional, Tuple


class FilamentProfile(NamedTuple):
    parent_template: str
    base_id: str
    filament_id: str


OFFICIAL_MATERIAL_TYPES: Tuple[str, ...] = (
    "PLA",
    "PLA Basic",
    "PLA Dynamic",
    "PLA Tough",
    "PLA Tough+",
    "PLA Aero",
    "PLA Galaxy",
    "PLA Glow",
    "PLA Lite",
    "PLA Marble",
    "PLA Metal",
    "PLA Palette",
    "PLA Pastel",
    "PLA Pure",
    "PLA Sparkle",
    "PLA Translucent",
    "PLA Wood",
    "PLA Silk",
    "PLA Silk+",
    "PLA Matte",
    "PLA-CF",
    "PETG",
    "PETG-CF",
    "ABS",
    "ASA",
    "TPU",
)


_PLA = FilamentProfile("Generic PLA", "GFSL99_04", "GFL99")
_PLA_SILK = FilamentProfile("Generic PLA Silk", "GFSL96_01", "GFL96")
_PLA_MATTE = FilamentProfile("Bambu PLA Matte", "GFSA01_04", "GFA01")
_PLA_BASIC = FilamentProfile("Bambu PLA Basic", "GFSA00_04", "GFA00")
_PLA_DYNAMIC = FilamentProfile("Bambu PLA Dynamic", "GFSA13_05", "GFA13")
_PLA_TOUGH = FilamentProfile("Bambu PLA Tough", "GFSA09_05", "GFA09")
_PLA_TOUGH_PLUS = FilamentProfile("Bambu PLA Tough+", "GFSA10_01", "GFA10")
_PLA_AERO = FilamentProfile("Bambu PLA Aero", "GFSA11_04", "GFA11")
_PLA_GALAXY = FilamentProfile("Bambu PLA Galaxy", "GFSA15_05", "GFA15")
_PLA_GLOW = FilamentProfile("Bambu PLA Glow", "GFSA12_11", "GFA12")
_PLA_LITE = FilamentProfile("Bambu PLA Lite", "GFSA18_05", "GFA18")
_PLA_MARBLE = FilamentProfile("Bambu PLA Marble", "GFSA07_03", "GFA07")
_PLA_METAL = FilamentProfile("Bambu PLA Metal", "GFSA02_04", "GFA02")
_PLA_PALETTE = FilamentProfile("Bambu PLA Palette", "GFSA20_04", "GFA20")
_PLA_PURE = FilamentProfile("Bambu PLA Pure", "GFSA19_02", "GFA19")
_PLA_SPARKLE = FilamentProfile("Bambu PLA Sparkle", "GFSA08_03", "GFA08")
_PLA_TRANSLUCENT = FilamentProfile("Bambu PLA Translucent", "GFSA17_06", "GFA17")
_PLA_WOOD = FilamentProfile("Bambu PLA Wood", "GFSA16_04", "GFA16")
_PLA_SILK_PLUS = FilamentProfile("Bambu PLA Silk+", "GFSA06_05", "GFA06")
_PLA_CF = FilamentProfile("Generic PLA-CF", "GFSL98_01", "GFL98")
_PETG = FilamentProfile("Generic PETG", "GFSG99_03", "GFG99")
_PETG_CF = FilamentProfile("Generic PETG-CF", "GFSG98_01", "GFG98")
_ABS = FilamentProfile("Generic ABS", "GFSB99_05", "GFB99")
_ASA = FilamentProfile("Generic ASA", "GFSB98_04", "GFB98")
_TPU = FilamentProfile("Generic TPU", "GFSU99_01", "GFU99")

MATERIAL_PROFILE_MAP: Dict[str, FilamentProfile] = {
    "PLA": _PLA,
    "PLA+": _PLA,
    "PLA PRO": _PLA,
    "TOUGH PLA": _PLA,
    "PLA SILK": _PLA_SILK,
    "SILK PLA": _PLA_SILK,
    "PLA-MATTE": _PLA_MATTE,
    "MATTE PLA": _PLA_MATTE,
    "PLA MATTE": _PLA_MATTE,
    "PLA BASIC": _PLA_BASIC,
    "BAMBU PLA BASIC": _PLA_BASIC,
    "XPLA": _PLA_BASIC,
    "X PLA": _PLA_BASIC,
    "PLA DYNAMIC": _PLA_DYNAMIC,
    "PLA TOUGH": _PLA_TOUGH,
    "PLA TOUGH+": _PLA_TOUGH_PLUS,
    "PLA TOUGH PLUS": _PLA_TOUGH_PLUS,
    "TOUGH PLA+": _PLA_TOUGH_PLUS,
    "PLA AERO": _PLA_AERO,
    "PLA GALAXY": _PLA_GALAXY,
    "PLA GLOW": _PLA_GLOW,
    "PLA LITE": _PLA_LITE,
    "PLA MARBLE": _PLA_MARBLE,
    "PLA METAL": _PLA_METAL,
    "PLA PALETTE": _PLA_PALETTE,
    "PLA PASTEL": _PLA,
    "PLAPASTEL": _PLA,
    "PASTEL PLA": _PLA,
    "PLA PURE": _PLA_PURE,
    "PLA SPARKLE": _PLA_SPARKLE,
    "PLA TRANSLUCENT": _PLA_TRANSLUCENT,
    "PLA WOOD": _PLA_WOOD,
    "PLA SILK+": _PLA_SILK_PLUS,
    "PLA SILK PLUS": _PLA_SILK_PLUS,
    "PLA-CF": _PLA_CF,
    "PLAAF": _PLA_CF,
    "PLA CF": _PLA_CF,
    "CF PLA": _PLA_CF,
    "PETG": _PETG,
    "PETG-CF": _PETG_CF,
    "PETG CF": _PETG_CF,
    "CF PETG": _PETG_CF,
    "ABS": _ABS,
    "ASA": _ASA,
    "TPU": _TPU,
    "TPE": _TPU,
}


OFFICIAL_MATERIAL_ALIASES: Dict[str, str] = {
    "PLA": "PLA",
    "PLA BASIC": "PLA Basic",
    "BAMBU PLA BASIC": "PLA Basic",
    "XPLA": "PLA Basic",
    "X PLA": "PLA Basic",
    "PLA DYNAMIC": "PLA Dynamic",
    "PLA TOUGH": "PLA Tough",
    "PLA TOUGH+": "PLA Tough+",
    "PLA TOUGH PLUS": "PLA Tough+",
    "TOUGH PLA+": "PLA Tough+",
    "PLA AERO": "PLA Aero",
    "PLA GALAXY": "PLA Galaxy",
    "PLA GLOW": "PLA Glow",
    "PLA LITE": "PLA Lite",
    "PLA MARBLE": "PLA Marble",
    "PLA METAL": "PLA Metal",
    "PLA PALETTE": "PLA Palette",
    "PLA PASTEL": "PLA Pastel",
    "PLAPASTEL": "PLA Pastel",
    "PASTEL PLA": "PLA Pastel",
    "PLA PURE": "PLA Pure",
    "PLA SPARKLE": "PLA Sparkle",
    "PLA TRANSLUCENT": "PLA Translucent",
    "PLA WOOD": "PLA Wood",
    "PLA SILK+": "PLA Silk+",
    "PLA SILK PLUS": "PLA Silk+",
    "PLA+": "PLA",
    "PLA PLUS": "PLA",
    "PLA PRO": "PLA",
    "TOUGH PLA": "PLA",
    "PLA SILK": "PLA Silk",
    "SILK PLA": "PLA Silk",
    "PLA MATTE": "PLA Matte",
    "MATTE PLA": "PLA Matte",
    "PLA-CF": "PLA-CF",
    "PLA CF": "PLA-CF",
    "CF PLA": "PLA-CF",
    "PETG": "PETG",
    "PETG-CF": "PETG-CF",
    "PETG CF": "PETG-CF",
    "CF PETG": "PETG-CF",
    "ABS": "ABS",
    "ASA": "ASA",
    "TPU": "TPU",
    "TPE": "TPU",
}


def normalize_filament_material(material: Optional[str]) -> str:
    if not isinstance(material, str):
        raise ValueError("Malzeme türü metin olmalıdır.")

    compact = re.sub(r"[_]+", " ", material.strip().upper())
    compact = re.sub(r"\s+", " ", compact)
    compact = compact.replace("-", " ")
    compact = re.sub(r"\s+", " ", compact).strip()
    compact = compact.replace("PLA ", "PLA ")

    normalized_aliases = {
        re.sub(r"\s+", " ", key.replace("-", " ").strip()).upper(): value
        for key, value in OFFICIAL_MATERIAL_ALIASES.items()
    }
    canonical = normalized_aliases.get(compact)
    if canonical is not None:
        return canonical

    # Gemini veya OCR bazen SKU/paket kodunu material alanına yazabilir.
    # Bunlar malzeme kodu değildir; gömülü malzeme türü varsa onu çıkar.
    sku_text = re.sub(r"[^A-Z0-9+]", "", compact)
    if "PETGCF" in sku_text or ("PETG" in sku_text and "CF" in sku_text):
        return "PETG-CF"
    if "PLACF" in sku_text or ("PLA" in sku_text and "CF" in sku_text):
        return "PLA-CF"
    if "PASTEL" in sku_text:
        return "PLA Pastel"
    if "MATTE" in sku_text:
        return "PLA Matte"
    if "SILK" in sku_text:
        return "PLA Silk"
    if "PETG" in sku_text:
        return "PETG"
    if "ABS" in sku_text:
        return "ABS"
    if "ASA" in sku_text:
        return "ASA"
    if "TPU" in sku_text or "TPE" in sku_text:
        return "TPU"
    if "PLA" in sku_text or "XPLA" in sku_text:
        return "PLA"
    raise ValueError(
        f"Desteklenmeyen malzeme türü: {material.strip()}. "
        f"Resmi türlerden birini seçin: {', '.join(OFFICIAL_MATERIAL_TYPES)}"
    )


def get_cloud_filament_type(material: Optional[str]) -> str:
    """Return the Bambu Cloud material category for a canonical material name."""
    canonical = normalize_filament_material(material)
    if canonical == "PLA-CF":
        return "PLA-CF"
    if canonical == "PETG-CF":
        return "PETG-CF"
    if canonical.startswith("PLA"):
        return "PLA"
    if canonical.startswith("PETG"):
        return "PETG"
    return canonical


def resolve_filament_label_fields(
    material: Optional[str],
    sku: Optional[str],
) -> tuple[str, Optional[str]]:
    """Malzeme ve SKU alanlarını ayrı canonical değerlerle döndürür."""
    raw_material = material.strip() if isinstance(material, str) else ""
    normalized_sku = sku.strip() if isinstance(sku, str) and sku.strip() else None
    looks_like_sku = (
        len(raw_material) >= 8
        and any(char.isdigit() for char in raw_material)
    )
    if looks_like_sku and normalized_sku is None:
        normalized_sku = raw_material
    canonical_material = normalize_filament_material(raw_material)
    if any(char.isdigit() for char in canonical_material):
        raise ValueError("Malzeme alanına SKU/paket kodu bırakılmamalıdır.")
    return canonical_material, normalized_sku


def get_filament_profile(material: Optional[str]) -> FilamentProfile:
    normalized_material = normalize_filament_material(material)
    canonical_profiles = {
        "PLA Basic": _PLA_BASIC,
        "PLA Dynamic": _PLA_DYNAMIC,
        "PLA Tough": _PLA_TOUGH,
        "PLA Tough+": _PLA_TOUGH_PLUS,
        "PLA Aero": _PLA_AERO,
        "PLA Galaxy": _PLA_GALAXY,
        "PLA Glow": _PLA_GLOW,
        "PLA Lite": _PLA_LITE,
        "PLA Marble": _PLA_MARBLE,
        "PLA Metal": _PLA_METAL,
        "PLA Palette": _PLA_PALETTE,
        "PLA Pastel": _PLA,
        "PLA Pure": _PLA_PURE,
        "PLA Sparkle": _PLA_SPARKLE,
        "PLA Translucent": _PLA_TRANSLUCENT,
        "PLA Wood": _PLA_WOOD,
        "PLA Silk+": _PLA_SILK_PLUS,
    }
    if normalized_material in canonical_profiles:
        return canonical_profiles[normalized_material]
    if normalized_material == "PLA Silk":
        return _PLA_SILK
    if normalized_material == "PLA Matte":
        return _PLA_MATTE
    return MATERIAL_PROFILE_MAP[normalized_material]


def get_filament_id_map() -> Dict[str, str]:
    canonical_profiles = {
        "PLA": _PLA,
        "PLA Basic": _PLA_BASIC,
        "PLA Dynamic": _PLA_DYNAMIC,
        "PLA Tough": _PLA_TOUGH,
        "PLA Tough+": _PLA_TOUGH_PLUS,
        "PLA Aero": _PLA_AERO,
        "PLA Galaxy": _PLA_GALAXY,
        "PLA Glow": _PLA_GLOW,
        "PLA Lite": _PLA_LITE,
        "PLA Marble": _PLA_MARBLE,
        "PLA Metal": _PLA_METAL,
        "PLA Palette": _PLA_PALETTE,
        "PLA Pastel": _PLA,
        "PLA Pure": _PLA_PURE,
        "PLA Sparkle": _PLA_SPARKLE,
        "PLA Translucent": _PLA_TRANSLUCENT,
        "PLA Wood": _PLA_WOOD,
        "PLA Silk": _PLA_SILK,
        "PLA Silk+": _PLA_SILK_PLUS,
        "PLA Matte": _PLA_MATTE,
        "PLA-CF": _PLA_CF,
        "PETG": _PETG,
        "PETG-CF": _PETG_CF,
        "ABS": _ABS,
        "ASA": _ASA,
        "TPU": _TPU,
    }
    return {
        material: profile.filament_id
        for material, profile in canonical_profiles.items()
    }

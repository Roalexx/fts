from typing import Dict, NamedTuple, Optional


class FilamentProfile(NamedTuple):
    parent_template: str
    base_id: str
    filament_id: str


_PLA = FilamentProfile("Generic PLA", "GFSL99_04", "GFL99")
_PLA_SILK = FilamentProfile("Generic PLA Silk", "GFSL96_01", "GFL96")
_PLA_MATTE = FilamentProfile("Bambu PLA Matte", "GFSA01_04", "GFA01")
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
    "SILK PLA": _PLA_SILK,
    "PLA SILK": _PLA_SILK,
    "MATTE PLA": _PLA_MATTE,
    "PLA MATTE": _PLA_MATTE,
    "PLA-CF": _PLA_CF,
    "PETG": _PETG,
    "PETG-CF": _PETG_CF,
    "ABS": _ABS,
    "ASA": _ASA,
    "TPU": _TPU,
}


def get_filament_profile(material: Optional[str]) -> FilamentProfile:
    normalized_material = (material or "PLA").strip().upper()
    return MATERIAL_PROFILE_MAP.get(normalized_material, _PLA)


def get_filament_id_map() -> Dict[str, str]:
    return {
        material: profile.filament_id
        for material, profile in MATERIAL_PROFILE_MAP.items()
    }

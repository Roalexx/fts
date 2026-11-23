from pathlib import Path
from typing import Dict, Iterable, Optional

from openpyxl import Workbook, load_workbook


XLSX_PATH = Path(__file__).with_name("filament_catalog.xlsx")

COLUMNS = (
    "sku",
    "brand",
    "material",
    "filament_id",
    "parent_template",
    "base_id",
    "color",
    "hex_color",
    "nozzle_temp",
    "bed_temp",
)


def initialize_catalog() -> None:
    if XLSX_PATH.exists():
        load_workbook(XLSX_PATH, read_only=True).close()
        return
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Filaments"
    sheet.append(COLUMNS)
    for column in sheet.iter_cols(min_row=1, max_row=1):
        column[0].font = column[0].font.copy(bold=True)
    workbook.save(XLSX_PATH)


def normalize_sku(sku: Optional[str]) -> Optional[str]:
    if sku is None:
        return None
    normalized = sku.strip()
    return normalized or None


def upsert_product(product: Dict[str, object]) -> Dict[str, object]:
    sku = normalize_sku(product.get("sku") if isinstance(product.get("sku"), str) else None)
    fields = {
        "sku": sku,
        "brand": str(product.get("brand") or "Generic").strip(),
        "material": str(product.get("material") or "PLA").strip(),
        "filament_id": str(product.get("filament_id") or "").strip(),
        "parent_template": str(product.get("parent_template") or "").strip(),
        "base_id": str(product.get("base_id") or "").strip(),
        "color": str(product.get("color") or "").strip(),
        "hex_color": str(product.get("hex_color") or "").strip().upper(),
        "nozzle_temp": product.get("nozzle_temp"),
        "bed_temp": product.get("bed_temp"),
    }

    if not fields["brand"] or not fields["material"] or not fields["filament_id"]:
        raise ValueError("SKU kataloğu için marka, malzeme ve filament_id zorunludur.")

    initialize_catalog()
    workbook = load_workbook(XLSX_PATH)
    sheet = workbook["Filaments"]
    headers = [cell.value for cell in sheet[1]]
    updated_row = None
    for row_number in range(2, sheet.max_row + 1):
        existing = {
            headers[index]: sheet.cell(row_number, index + 1).value
            for index in range(len(headers))
        }
        if sku is not None and existing.get("sku") == sku:
            updated_row = row_number
            break
        if sku is None and all(
            existing.get(column) == fields.get(column)
            for column in ("brand", "material", "color", "hex_color")
        ):
            updated_row = row_number
            break
    if updated_row is None:
        updated_row = sheet.max_row + 1
    for index, column in enumerate(COLUMNS, start=1):
        sheet.cell(updated_row, index, fields[column])
    workbook.save(XLSX_PATH)
    workbook.close()
    return fields


def list_products() -> Iterable[Dict[str, object]]:
    initialize_catalog()
    workbook = load_workbook(XLSX_PATH, read_only=True)
    sheet = workbook["Filaments"]
    headers = [cell.value for cell in next(sheet.iter_rows(min_row=1, max_row=1))]
    products = [
        {
            headers[index]: row[index].value
            for index in range(len(headers))
        }
        for row in sheet.iter_rows(min_row=2)
        if any(cell.value is not None for cell in row)
    ]
    workbook.close()
    return list(reversed(products))


def find_product_by_sku(sku: Optional[str]) -> Optional[Dict[str, object]]:
    normalized_sku = normalize_sku(sku)
    if normalized_sku is None:
        return None
    for product in list_products():
        if normalize_sku(product.get("sku") if isinstance(product.get("sku"), str) else None) == normalized_sku:
            return product
    return None


def delete_product(identifier: object) -> bool:
    initialize_catalog()
    workbook = load_workbook(XLSX_PATH)
    sheet = workbook["Filaments"]
    headers = [cell.value for cell in sheet[1]]
    sku_index = headers.index("sku")
    for row_number in range(2, sheet.max_row + 1):
        sku = sheet.cell(row_number, sku_index + 1).value
        if sku == identifier:
            sheet.delete_rows(row_number, 1)
            workbook.save(XLSX_PATH)
            workbook.close()
            return True
    workbook.close()
    return False

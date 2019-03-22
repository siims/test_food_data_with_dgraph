from dataclasses import dataclass
from datetime import datetime
from typing import List, Dict


@dataclass
class DataSource:
    abbrivation: str


@dataclass
class Manufacturer:
    name: str


@dataclass
class Ingredient:
    name: str


@dataclass(eq=True, frozen=True)
class Nutrient:
    name: str
    code: str
    derivation_code: str


@dataclass
class Amount:
    scalar: str
    unit: str


@dataclass
class Product:
    usda_food_db_id: str
    name: str
    data_source: DataSource
    barcode: str
    manufacturer: Manufacturer
    date_modified: datetime
    date_available: datetime
    ingredients: List[Ingredient]
    nutrients: Dict[Nutrient, Amount]

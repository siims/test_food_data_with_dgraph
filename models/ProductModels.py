from dataclasses import dataclass
from datetime import datetime
from typing import List, Dict


@dataclass
class InformationSource:
    label = "information_source"
    abbrivation: str


@dataclass
class Manufacturer:
    label = "company"
    name: str


@dataclass
class Ingredient:
    label = "ingredient"
    name: str


@dataclass(eq=True, frozen=True)
class Nutrient:
    label = "nutrient"
    name: str
    code: str
    derivation_code: str


@dataclass
class Amount:
    label = "amount"
    scalar: str
    unit: str


@dataclass
class Product:
    label = "product"
    usda_food_db_id: str
    name: str
    information_source: InformationSource
    barcode: str
    manufactured_by: Manufacturer
    date_modified: datetime
    date_available: datetime
    ingredients: List[Ingredient]
    nutrients: Dict[Nutrient, Amount]

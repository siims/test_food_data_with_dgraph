import json
from dataclasses import dataclass
from datetime import datetime
from typing import List, Dict

from utils.json_encoder import JSONEncoderEnhancedWithDateSerialization
from utils.utils import with_label


@with_label("source")
@dataclass
class InformationSource:
    uid: str
    abbreviation: str


@with_label("company")
@dataclass
class Manufacturer:
    uid: str
    name: str


@with_label("ingredient")
@dataclass
class Ingredient:
    uid: str
    name: str


@with_label("nutrient")
@dataclass(eq=True, frozen=True)
class Nutrient:
    uid: str
    name: str
    code: str
    derivation_code: str


@with_label("amount")
@dataclass
class Amount:
    uid: str
    scalar: str
    unit: str


@with_label("product")
@dataclass
class FoodProduct:
    uid: str
    usda_food_db_id: str
    name: str
    source: InformationSource
    barcode: str
    manufactured_by: Manufacturer
    date_modified: datetime
    date_available: datetime
    ingredients: List[Ingredient]
    nutrients: Dict[Nutrient, Amount]


if __name__ == "__main__":
    ## Testing
    m = Manufacturer("ASD", "QWE")
    p = FoodProduct("1", "2", "3 name", InformationSource("id", "ASD"), "4 barcode", m, datetime.now(), datetime.now(),
                    [], {})
    print(json.dumps(m, cls=JSONEncoderEnhancedWithDateSerialization))
    print(json.dumps(p, cls=JSONEncoderEnhancedWithDateSerialization))

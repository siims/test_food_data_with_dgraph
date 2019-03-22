import csv
import logging
import traceback
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Optional

from models.ProductModels import Nutrient, Amount, Product, Manufacturer, Ingredient

CSV_FILE_RELATIVE_LOCATION = Path(__file__).parent.joinpath("../csv_data/usda_food_composition_database_2019_03_20")


class ProductParser:

    def parse(self):
        nutrients = self.get_nutrients()
        return self.get_products(nutrients)

    def get_products(
            self, nutrients: Tuple[List[Nutrient], Dict[str, List[Tuple[Nutrient, Amount]]]]
    ) -> Dict[str, Product]:
        product_csv_file_name = "Products.csv"

        all_nutrients, products_nutrients = nutrients
        products = {}
        with open(CSV_FILE_RELATIVE_LOCATION.joinpath(product_csv_file_name)) as csvfile:
            rows = csv.reader(csvfile, delimiter=',')
            for i, row in enumerate(rows):
                if i < 240:
                    continue
                if i > 245:
                    break

                logging.debug(f"###{i}### Started processing product {row}")

                product_usda_food_db_id = row[0]
                nutrient_amounts = self._calculate_product_nutrient_amounts(product_usda_food_db_id, products_nutrients)
                product_ingredients = self._process_product_memo(row[7])
                product = Product(
                    product_usda_food_db_id, row[1], row[2], row[3], Manufacturer(row[4]),
                    self._parse_datetime(row[5]), self._parse_datetime(row[6]),
                    product_ingredients, nutrient_amounts)
                products[product_usda_food_db_id] = product
                logging.debug(f"###{i}### Finished processing product {product}")

        return products

    def get_nutrients(self) -> Tuple[List[Nutrient], Dict[str, List[Tuple[Nutrient, Amount]]]]:
        nutrient_csv_file_name = "Nutrient.csv"

        nutrients = set()
        nutrient_amounts: Dict[str, List[Tuple[Nutrient, Amount]]] = {}
        with open(CSV_FILE_RELATIVE_LOCATION.joinpath(nutrient_csv_file_name)) as csvfile:
            rows = csv.reader(csvfile, delimiter=',')
            for i, row in enumerate(rows):
                if i > 100000:
                    break
                nutrient = Nutrient(row[2], row[1], row[3])
                amount = Amount(row[4], row[5])

                nutrients.add(nutrient)
                if nutrient_amounts.get(row[0], None) is None:
                    nutrient_amounts[row[0]] = [(nutrient, amount)]
                else:
                    nutrient_amounts[row[0]].append((nutrient, amount))

        return list(nutrients), nutrient_amounts

    def get_serving_sizes(self) -> Dict[str, List[str]]:
        serving_size_csv_file_name = "Serving_Size.csv"

        serving_sizes = {}
        with open(CSV_FILE_RELATIVE_LOCATION.joinpath(serving_size_csv_file_name)) as csvfile:
            rows = csv.reader(csvfile, delimiter=',')
            for i, row in enumerate(rows):
                if i > 50:
                    break
                if serving_sizes.get(row[0], None) is None:
                    serving_sizes[row[0]] = [row]
                else:
                    serving_sizes[row[0]].append(row)

        return serving_sizes

    def _process_product_memo(self, text: str) -> [Ingredient]:
        try:
            preprocessed = self._preprocess_product_memo(text)
            items = self._split_product_memo_to_items(preprocessed)
            return self._postprocess_product_memo(items)
        except Exception as e:
            logging.error(f"Failed to parse ingredients '{text}'", e)
            logging.debug(traceback.format_exc())
            return []

    def _preprocess_product_memo(self, text):

        def remove_stars(text):
            return text.replace("*", "")

        def remove_text_in_brackets(text):
            if text.find("(") == -1:
                return text

            def handle_unclosed_brackets(text):
                if text.count("(") != text.count(")"):
                    return text.replace("(", ",").replace(")", "")
                return text

            text = handle_unclosed_brackets(text)

            modified_memo = ""
            while text.find("(") != -1:
                next_bracket_open = text.find("(")
                modified_memo += text[0:next_bracket_open]
                text = text[text.find(")", next_bracket_open) + 1:]
            modified_memo += text
            return modified_memo

        text = remove_stars(text)
        text = remove_text_in_brackets(text)
        return text.lower()

    def _split_product_memo_to_items(self, text):
        return [self._format_ingredient(item) for item in text.split(",")]

    def _parse_datetime(self, text: str) -> Optional[datetime]:
        "Wed Nov 15 19:19:38 GMT 2017"
        return datetime.strptime(text, "%a %b %d %H:%M:%S %Z %Y")

    def _calculate_product_nutrient_amounts(
            self,
            product_id: str,
            all_product_nutrient_amount: Dict[str, List[Tuple[Nutrient, Amount]]]
    ) -> Dict[Nutrient, Amount]:
        if product_id not in all_product_nutrient_amount.keys():
            logging.warning(f"Product {product_id} does not have any nutrient amounts listed")
            return {}

        nutrient_amounts = all_product_nutrient_amount[product_id]

        product_nutrient_amounts: Dict[Nutrient, Amount] = {}
        for nutrient, amount in nutrient_amounts:
            product_nutrient_amounts[nutrient] = amount

        return product_nutrient_amounts

    def _postprocess_product_memo(self, items: List[str]) -> List[Ingredient]:
        items = self._ingredient_split_last_items_ending_with_keyword_other_than_comma(items)
        items = self._ingredient_remove_middle_captions(items)
        items = self._ingredient_remove_last_item_trailing_dot(items)
        items = self._ingredient_remove_invalid(items)
        return list(map(lambda item: Ingredient(item), items))

    def _ingredient_split_last_items_ending_with_keyword_other_than_comma(self, items: List[str]) -> List[str]:
        for separator in [" and ", " & "]:
            if separator in items[-1]:
                last_item = items.pop()
                split_last_item = last_item.split(separator)
                items += split_last_item
                return items

        return items

    def _ingredient_remove_last_item_trailing_dot(self, items: List[str]) -> List[str]:
        if items[-1][-1] == ".":
            last_item = items.pop()
            items.append(last_item[:-1])
            return items

        return items

    def _ingredient_remove_middle_captions(self, items: List[str]) -> List[str]:
        captions_indices = []

        for i, item in enumerate(items):
            if ":" in item:
                captions_indices.append(i)

        for captions_index in captions_indices[::-1]:  # reverse to be able to insert in right order
            item = items.pop(captions_index)
            if item[-1] == ".":  # remove trailing dot, eg for captions that have last element
                item = item[:-1]
            for item in item.split(".")[::-1]:  # reverse to be able to insert in right order
                if item.find(": ") != -1:
                    new_item = item[item.index(": ") + 2:]
                else:
                    new_item = item

                items.insert(captions_index, new_item)

        return items

    def _ingredient_remove_invalid(self, items):
        return filter(lambda item: len(item) != 0, items)

    def _format_ingredient(self, item):
        return item.strip()


if __name__ == "__main__":
    logging.basicConfig(level="DEBUG")
    products = ProductParser().parse()
    print(len(products))  # with nutrients: "45002000"

import unittest
from datetime import datetime

from parameterized import parameterized
from timeout_decorator import timeout_decorator

from csv_parser.product_parser import ProductParser
from models.product_models import Nutrient, Amount


class ProductParserTest(unittest.TestCase):

    def test_parse_string_to_datetime(self):
        input = "Wed Nov 15 19:19:38 GMT 2017"

        result = ProductParser()._parse_datetime(input)

        self.assertEquals(datetime(2017, 11, 15, 19, 19, 38), result)

    def test_calculate_product_nutrients(self):
        nutrient_1 = Nutrient("1", name='Protein', code='203', derivation_code='LCGA')
        nutrient_2 = Nutrient("2", name='Total lipid (fat)', code='204', derivation_code='LCGA')
        nutrient_3 = Nutrient("3", name='Carbohydrate', code='205', derivation_code='LCGA')

        product_id = '45128680'
        product_nutrient_amount = {product_id: [
            (nutrient_1, Amount("4", scalar='12.7', unit='g')),
            (nutrient_2, Amount("5", scalar='8.3', unit='g')),
            (nutrient_3, Amount("6", scalar='24.6', unit='g'))
        ]}

        result = ProductParser()._calculate_product_nutrient_amounts(product_id, product_nutrient_amount)

        self.assertEqual(3, len(result))
        self.assertEqual(Amount("4", scalar='12.7', unit='g'), result[nutrient_1])
        self.assertEqual(Amount("5", scalar='8.3', unit='g'), result[nutrient_2])
        self.assertEqual(Amount("6", scalar='24.6', unit='g'), result[nutrient_3])


class ProductMemoTest(unittest.TestCase):

    def test_process_product_memo(self):
        input = "ICE CREAM INGREDIENTS: MILK, CREAM, SUGAR, STRAWBERRIES (STRAWBERRIES, SUGAR), MONO & DIGLYCERIDES, BEET JUICE AND BEET POWDER (FOR COLOR), CELLULOSE GUM, LOCUST BEAN GUM, CARRAGEENAN. COATING INGREDIENTS: SUGAR, WATER, RICE FLOUR, TREHALOSE, EGG WHITES, BEET JUICE AND BEET POWDER (FOR COLOR), DUSTED WITH CORN & POTATO STARCH"
        result = ProductParser()._process_product_memo(input)
        self.assertEqual(["milk", "cream", "sugar", "strawberries", "mono & diglycerides", "beet juice and beet powder",
                          "cellulose gum", "locust bean gum", "carrageenan", "sugar", "water", "rice flour",
                          "trehalose", "egg whites", "beet juice and beet powder", "dusted with corn", "potato starch"],
                         list(map(lambda ingredient: ingredient.name, result)))

    def test_all_brackets_data_is_removed(self):
        result = ProductParser()._preprocess_product_memo(
            "item 1 (some), (anti) item 2, item 3 (hope, beauty, honor), item 4.")

        self.assertRegex(result, "item 1( ?)*,( ?)*item 2, item 3( ?)*, item 4.")

    def test_stars_removed(self):
        result = ProductParser()._preprocess_product_memo("*item 1**, **item 2****, item 3***")

        self.assertEqual("item 1, item 2, item 3", result)

    def test_last_item_is_split_to_two_for_and_keyword(self):
        result = ProductParser()._ingredient_split_last_items_ending_with_keyword_other_than_comma(
            ["item 0", "item 1 and item 2"])

        self.assertEqual(["item 0", "item 1", "item 2"], result)

    def test_last_item_is_split_to_two_for_ampersand_keyword(self):
        result = ProductParser()._ingredient_split_last_items_ending_with_keyword_other_than_comma(
            ["item 0", "item 1 & item 2"])

        self.assertEqual(["item 0", "item 1", "item 2"], result)

    def test_remove_middle_level_captions(self):
        result = ProductParser()._ingredient_remove_middle_captions(
            ["Caption 1: item 0", "item 1", "item 2. Caption 2: item 3", "item 4"])

        self.assertEqual(["item 0", "item 1", "item 2", "item 3", "item 4"], result)

    def test_remove_middle_level_captions_only_one_element_after_caption(self):
        result = ProductParser()._ingredient_remove_middle_captions(
            ["Caption 1: item 0."])

        self.assertEqual(["item 0"], result)

    def test_remove_trailing_dots(self):
        result = ProductParser()._ingredient_remove_last_item_trailing_dot(
            ["item 1", "item 2."])

        self.assertEqual(["item 1", "item 2"], result)

    def test_lowercase(self):
        result = ProductParser()._preprocess_product_memo("ITEM 1")

        self.assertEqual("item 1", result)

    def test_split_items(self):
        result = ProductParser()._split_product_memo_to_items("item 1, item 2, item 3")

        self.assertEqual(["item 1", "item 2", "item 3"], result)

    def test_empty_items_get_removed(self):
        result = ProductParser()._ingredient_remove_empty_strings(["item 1", "", "item 3"])

        self.assertEqual(["item 1", "item 3"], result)


class ProductMemoDataDrivenTest(unittest.TestCase):

    @parameterized.expand([
        ("unclosed single bracket", "item 1 (some text, item 2", ["item 1", "some text", "item 2"]),
        ("double comma", "item 1 ,, item 2", ["item 1", "item 2"]),
    ])
    @timeout_decorator.timeout(1)
    def test_all_cases(self, description, input, expected):
        result = ProductParser()._process_product_memo(input)

        self.assertEqual(expected, list(map(lambda i: i.name, result)), description)

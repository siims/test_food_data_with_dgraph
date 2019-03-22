import unittest
from datetime import datetime

from parameterized import parameterized
from timeout_decorator import timeout_decorator

from converter_csv_to_dgraph import converter
from models.Product import Nutrient, Amount


class ProductConvertingTest(unittest.TestCase):

    def test_convert_string_to_datetime(self):
        input = "Wed Nov 15 19:19:38 GMT 2017"

        result = converter.Converter()._parse_datetime(input)

        self.assertEquals(datetime(2017, 11, 15, 19, 19, 38), result)

    def test_calculate_product_nutrients(self):
        nutrient_1 = Nutrient(name='Protein', code='203', derivation_code='LCGA')
        nutrient_2 = Nutrient(name='Total lipid (fat)', code='204', derivation_code='LCGA')
        nutrient_3 = Nutrient(name='Carbohydrate', code='205', derivation_code='LCGA')

        product_id = '45128680'
        product_nutrient_amount = {product_id: [
            (nutrient_1, Amount(scalar='12.7', unit='g')),
            (nutrient_2, Amount(scalar='8.3', unit='g')),
            (nutrient_3, Amount(scalar='24.6', unit='g'))
        ]}

        result = converter.Converter()._calculate_product_nutrient_amounts(product_id, product_nutrient_amount)

        self.assertEqual(3, len(result))
        self.assertEqual(Amount(scalar='12.7', unit='g'), result[nutrient_1])
        self.assertEqual(Amount(scalar='8.3', unit='g'), result[nutrient_2])
        self.assertEqual(Amount(scalar='24.6', unit='g'), result[nutrient_3])


class ProductMemoTest(unittest.TestCase):
    raw_data_for_reference = [
        "TOMATO PUREE, ONION PUREE, SUGAR, MOLASSES, DISTILLED VINEGAR, HORSERADISH, SALT, SOYBEAN OIL, ORANGE JUICE CONCENTRATE, LEMON JUICE CONCENTRATE, ANCHOVY PASTE (ANCHOVY, OLIVE OIL, ACETIC ACID), ROASTED GARLIC PUREE (GARLIC, WATER, NATURAL FLAVOR, CITRIC ACID), NATURAL FLAVOR, JALAPENO PUREE (JALAPENO CHILE, DISTILLED VINEGAR, SALT), SOY SAUCE (WATER, WHEAT, SOYBEAN, SALT), CHILI POWDER, MUSTARD FLOUR, XANTHAN GUM, BLACK PEPPER, CARAMEL COLORING, CLOVE POWDER.",
        "EXTRA VIRGIN OLIVE OIL**, SOY LECITHIN, DIMETHYL SILICONE (FOR ANTI-FOAMING).",
        "CHICKPEAS, WATER, CANOLA/OLIVE OIL BLEND, SESAME TAHINI, SUNDRIED TOMATOES, LEMON JUICE CONCENTRATE, BASIL, GARLIC, SALT, SPICES, NATURAL FLAVOR, PAPRIKA EXTRACT (NATURAL FLAVORS, SOY LECITHIN), POTASSIUM SORBATE AND SODIUM BENZOATE (TO MAINTAIN FRESHNESS).",
        "WHOLE MILK, CREAM, SUGAR, BANANA PUREE, BROWN SUGAR, NONFAT MILK POWDER, BRANDY, CARRAGEENAN, MONO AND DI-GLYCERIDES, GUAR GUM, LOCUST BEAN GUM, SUCROSE, DEXTROSE, FRUCTOSE, BANANAS, NATURAL FLAVOR, TURMERIC EXTRACT, SOY LECITHIN.",
        "DURUM SEMOLINA, NIACIN, FERROUS SULFATE (IRON), THIAMIN MONONITRATE, RIBOFLAVIN, FOLIC ACID.",
        "PLUM TOMATOES, TOMATO PASTE, OLIVE OIL, BLACK OLIVES (BLACK OLIVES, WATER, SALT, FERROUS GLUCONATE), CAPERS (CAPERS, DISTILLED VINEGAR, SALT, WATER), KALAMATA OLIVES (KALAMATA OLIVES, WATER, SALT, RED WINE VINEGAR, EXTRA VIRGIN OLIVE OIL), GARLIC, ANCHOVY PASTE (ANCHOVIES, SALT, OLIVE OIL, ACETIC ACID), PARSLEY, BASIL, ONIONS, WHITE PEPPER, CRUSHED RED PEPPERS, OREGANO.",
        "ICE CREAM INGREDIENTS: MILK, CREAM, SUGAR, STRAWBERRIES (STRAWBERRIES, SUGAR), CORN SYRUP SOLIDS, SKIM MILK, WHEY, NATURAL FLAVOR, GUAR GUM, MONO & DIGLYCERIDES, BEET JUICE AND BEET POWDER (FOR COLOR), CELLULOSE GUM, LOCUST BEAN GUM, CARRAGEENAN. COATING INGREDIENTS: SUGAR, WATER, RICE FLOUR, TREHALOSE, EGG WHITES, BEET JUICE AND BEET POWDER (FOR COLOR), DUSTED WITH CORN & POTATO STARCH"
    ]

    def test_process_product_memo(self):
        input = "ICE CREAM INGREDIENTS: MILK, CREAM, SUGAR, STRAWBERRIES (STRAWBERRIES, SUGAR), MONO & DIGLYCERIDES, BEET JUICE AND BEET POWDER (FOR COLOR), CELLULOSE GUM, LOCUST BEAN GUM, CARRAGEENAN. COATING INGREDIENTS: SUGAR, WATER, RICE FLOUR, TREHALOSE, EGG WHITES, BEET JUICE AND BEET POWDER (FOR COLOR), DUSTED WITH CORN & POTATO STARCH"
        result = converter.Converter()._process_product_memo(input)
        self.assertEqual(["milk", "cream", "sugar", "strawberries", "mono & diglycerides", "beet juice and beet powder",
                          "cellulose gum", "locust bean gum", "carrageenan", "sugar", "water", "rice flour",
                          "trehalose", "egg whites", "beet juice and beet powder", "dusted with corn", "potato starch"],
                         list(map(lambda ingredient: ingredient.name, result)))

    def test_all_brackets_data_is_removed(self):
        result = converter.Converter()._preprocess_product_memo(
            "item 1 (some), (anti) item 2, item 3 (hope, beauty, honor), item 4.")

        self.assertRegex(result, "item 1( ?)*,( ?)*item 2, item 3( ?)*, item 4.")

    def test_stars_removed(self):
        result = converter.Converter()._preprocess_product_memo("*item 1**, **item 2****, item 3***")

        self.assertEqual("item 1, item 2, item 3", result)

    def test_last_item_is_split_to_two_for_and_keyword(self):
        result = converter.Converter()._ingredient_split_last_items_ending_with_keyword_other_than_comma(
            ["item 0", "item 1 and item 2"])

        self.assertEqual(["item 0", "item 1", "item 2"], result)

    def test_last_item_is_split_to_two_for_ampersand_keyword(self):
        result = converter.Converter()._ingredient_split_last_items_ending_with_keyword_other_than_comma(
            ["item 0", "item 1 & item 2"])

        self.assertEqual(["item 0", "item 1", "item 2"], result)

    def test_remove_middle_level_captions(self):
        result = converter.Converter()._ingredient_remove_middle_captions(
            ["Caption 1: item 0", "item 1", "item 2. Caption 2: item 3", "item 4"])

        self.assertEqual(["item 0", "item 1", "item 2", "item 3", "item 4"], result)

    def test_remove_middle_level_captions_only_one_element_after_caption(self):
        result = converter.Converter()._ingredient_remove_middle_captions(
            ["Caption 1: item 0."])

        self.assertEqual(["item 0"], result)

    def test_remove_trailing_dots(self):
        result = converter.Converter()._ingredient_remove_last_item_trailing_dot(
            ["item 1", "item 2."])

        self.assertEqual(["item 1", "item 2"], result)

    def test_lowercase(self):
        result = converter.Converter()._preprocess_product_memo("ITEM 1")

        self.assertEqual("item 1", result)

    def test_split_items(self):
        result = converter.Converter()._split_product_memo_to_items("item 1, item 2, item 3")

        self.assertEqual(["item 1", "item 2", "item 3"], result)


class ProductMemoDataDrivenTest(unittest.TestCase):

    @parameterized.expand([
        ("unclosed single bracket", "item 1 (some text, item 2", ["item 1", "some text", "item 2"]),
        ("double comma", "item 1 ,, item 2", ["item 1", "item 2"]),
    ])
    @timeout_decorator.timeout(1)
    def test_all_cases(self, description, input, expected):
        result = converter.Converter()._process_product_memo(input)

        self.assertEqual(expected, list(map(lambda i: i.name, result)), description)

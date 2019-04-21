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

    def test_trailing_comma_removed(self):
        result = ProductParser()._preprocess_product_memo(
            "PEANUTS, SALT,")

        self.assertEqual("peanuts, salt", result)

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


# failure cases atm:
# "CORN FLOUR, VEGETABLE OIL, SEA SALT, (IT MAY CONTAIN ONE OF THE FOLLOWING: CORN OIL PALMOLEIN, SOY)"
# "CORN FLOUR, VEGETABLE OIL, SEA SALT, (IT MAY CONTAIN ONE OF THE FOLLOWING: CORN OIL, PALMOLEIN, SOY)"

# ""
# "ENRICHED WHEAT FLOUR [WHEAT FLOUR, NIACIN, REDUCED IRON, THIAMIN MONONITRATE (VITAMIN B1), RIBOFLAVIN (VITAMIN B2), FOLIC ACID], SUGAR, HIGH FRUCTOSE CORN SYRUP, CORN SYRUP, PALM OIL, WHEY PERMEATE, COCOA PROCESSED WITH ALKALI, MODIFIED CORN STARCH, SALT, PRECOOKED YELLOW CORN MEAL, LEAVENING (BAKING SODA, SODIUM ALUMINIUM PHOSPHATE), COLOR ADDED (INCLUDES RED 40), SORBITOL, POTASSIUM SORBATE (A PRESERVATIVE), NATURAL AND ARTIFICIAL FLAVOR, GELATIN, YELLOW CORN FLOUR, MODIFIED SOY PROTEIN, VITAMIN A PALMITATE, REDUCED IRON, NIACINAMIDE, PYRIDOXINE HYDROCHLORIDE (VITAMIN B6), RIBOFLAVIN (VITAMIN B2), THIAMIN MONONITRATE (VITAMIN B1),"
# "SALT, SUGAR, MONOSODIUM GLUTAMATE, WHEAT SEMOLINA, CORNSTARCH, HYDROLYZED SOY PROTEIN, CANOLA OIL, SILICON DIOXIDE (ANTI-CAKING AGENT), HERBS & SPICES (TURMERIC, PAPRIKA), DEHYDRATED VEGETABLES (ONION, GARLIC), CITRIC ACID, FD&C YELLOW #5 LAKE,"
# "ALL FLAVORS CONTAIN: SUGAR, ADDITIONALLY: ORIGINAL: GUM BASE, GLUCOSE SYRUP, NATURAL &ARTIFICIAL FLAVORS, GLYCERINE CITRIC ACID, TITANIUM DIOXIDE, BHT (PRESERVATIVE), RED 40 LAKE, RED 40, BLUE RASPBERRY: GLUCOSE SYRUP, GUM BASE, ARTIFICIAL FLAVORS, CITRIC ACID, GLYCERINE, MALIC ACID, ASPARTAME, BLUE 1 LAKE, ACESULFAME POTASSIUM, TITANIUM DIOXIDE, BHT (PRESERVATIVE),"
# "MIXED FRUIT PUREE (APPLES, PLUMS, SOUR CHERRIES), SUGAR, CITRIC ACID, PECTIN, SULPHUR DIOXIDE,"
# "ORGANIC APPLE PUREE CONCENTRATE, ORGANIC APPLE JUICE CONCENTRATE, ORGANIC NATURAL FLAVORS, MALIC ACID, PECTIN, COLORED WITH FRUIT AND VEGETABLE JUICE, VITAMINS & MINERALS: ASCORBIC ACID (VIT. C), FERRIC ORTHOPHOSPHATE (IRON),"
# "MANZANILLA OLIVES, WATER, SALT, LACTIC ACID, CITRIC ACID, ASCORBIC ACID,"
# "CERTIFIED GLUTEN FREE OATS ,BROWN SUGAR ,DRIED CRANBERRIES ,(SUGAR ,GLYCERIN ,,CITRIC ACID ,SUNFLOWER OIL ,)CINNAMON ,GROUND FLAX ,SALT ,"
# "GREEN PIGEON PEAS, WATER AND SALT,"
# "PREPARED LIGHT RED KIDNEY BEANS, WATER, SUGAR, SALT, CALCIUM CHLORIDE AND DISODIUM EDTA (FOR COLOR RETENTION),"
# "WATER, TOMATO PUREE (WATER, TOMATO PASTE), CELERY, ENRICHED MACARONI (WHEAT FLOUR, EGG WHITES, NIACIN, FERROUS, SULFATE, THIAMIN MONONITRATE, RIBOFLAVIN AND FOLIC ACID), CARROTS, ONIONS, GREAT NORTHERN BEANS, KIDNEY BEANS, LIMA BEANS, CABBAGE, GREEN BEANS, POTATOES, PEAS, SOYBEAN OIL, SALT, BEEF FLAVOR (NATURAL BEEF FLAVOR, NATURAL FLAVOR), EXTRA VIRGIN OLIVE OIL, GARLIC POWDER, NATURAL FLAVOR,"
# "ORGANIC CUCUMBERS, WATER, ORGANIC DISTILLED VINEGAR, SALT, CALCIUM CHLORIDE, ORGANIC GARLIC CHIPS, ORGANIC DILLWEED OIL, ORGANIC GUM ARABIC, ORGANIC NATURAL SPICE FLAVORS. XANTHAN GUM,"
# "ORGANIC SEAWEED, ORGANIC EXTRA VIRGIN OLIVE OIL, SEA SALT,"
# "SPANISH RICE: COOKED RICE (WATER, RICE), WATER, TOMATOES (TOMATOES,TOMATO JUICE, CITRIC ACID, CALCIUM CHLORIDE), TOMATO PASTE, CORN, CONTAINS 2% OR LESS OF: GREEN BELL PEPPERS, RED BELL PEPPERS, CELERY, GREEN PEAS, MODIFIED FOOD STARCH, CHICKEN BROTH FLAVOR MIX (HYDROLYZED CORN GLUTEN, SOY PROTEIN AND WHEAT GLUTEN, SALT, SUGAR, AUTOLYZED YEAST EXTRACT, DRIED CHICKEN MEAT, TORULA YEAST, SOY FLOUR, PARTIALLY HYDROGENATED SOYBEAN & COTTONSEED OIL), FLAVORINGS INCLUDING PAPRIKA, VINEGAR, CILANTRO FLAVOR (DEXTROSE, MODIFIED CORN STARCH, EXTRACTIVES OF CILANTRO), SOYBEAN OIL, DEHYDRATED ONION, CILANTRO, YEAST EXTRACT, SALT. FILL: DARK MEAT CHICKEN, TOMATOES (TOMATOES, TOMATO JUICE, CITRIC ACID, CALCIUM CHLORIDE), WATER, CHIPOTLE CHILE BASE (CHILE PEPPERS , DRIED ONION AND GARLIC, SALT, YEAST EXTRACT, SPICES, PAPRIKA, CITRIC ACID, NATURAL SMOKE FLAVORING), ONIONS, CONTAINS 2% OR LESS OF: MODIFIED FOOD STARCH, CHIPOTLE PUREE (WATER, VINEGAR, CHIPOTLE JALAPENO, TOMATO PASTE, SALT, DRIED RED CHILE, SPICES, ONION POWDER, GARLIC POWDER), VINEGAR, CILATRO, FLAVORING, SUGAR, GUAR GUM, DISODIUM INOSINATE & DISODIUM GUANYLATE,"
# "ENRICHED BLEACHED FLOUR (WHEAT FLOUR, MALTED BARLEY FLOUR, NIACIN, REDUCED IRON, THIAMINE, MONONITRATE, RIBOFLAVIN AND FOLIC ACID), WATER, VEGETABLES SHORTENING (PARTIAL,LY HYDROGENATED SOYBEAN AND/OR COTTONSEED OILS OR PALM OIL OR CORN OIL), CONTAINS 2% OR LESS OF THE FOLLOWING: SLAT, BAKING POWDER, DISTILLED ,MONO AND DIGLYCERIDES, CALCIUM PROPIONATE, SORBIC ACID, GUM BLEND, FUMARIC ACID, SUGAR, DOUGH RELAXER (SODIUM METABISULFITE, CORN STARCH, MICROCRYSTALLINE CELLULOSE, DICALCIUM PHOSPHATE),"
# "WHEAT FLOUR, COCONUT OIL, VEGETABLE SHORTENING (PALM OIL) (CONTAINS ANTIOXIDANT (ASCORBYL PALMITATE, MIXED TOCOPHEROLS CONCENTRATE, SOY LECITHIN)), SESAME, SALT, CHIVES, SUGAR, SIMMED MILK POWER, GLUCOSE SYRUP, SPEING ONION, CORN STARCH, ANTIOXIDANT (SOY LECITHIN, ASCORBYL PALMITATE, LESSATHEN -TOCOPHEROL), FLOUR TRETMENT AGENT (AMYLASES, PROTEASES),"
# "WHOLE GRAIN ROLLED OATS (WITH OAT BRAN), SUGAR, FLAVORED FRUIT PIECES (DEHYDRATED APPLES [TREATED WITH SULFUR DIOXIDE AND SODIUM SULFITE TO PROMOTE COLOR RETENTION], ARTIFICIAL PEACH FLAVOR, CITRIC ACID, ANNATTO COLOR), CREAMING AGENT (CORN SYRUP SOLIDS, PARTIALLY HYDROGENATED SOYBEAN OI, WHEY, SODIUM CASEINATE, TITANIUM DIOXIDE), CALCIUM CARBONATE (A SOURCE OF CALCIUM), SALT, GUAR GUM, ARTIFICIAL FLAVOR, FERRIC ORTHOPHOSPHATE (A SOURCE OF IRON), NIACINAMIDE*, PYRIDOXINE HYDROCHLORIDE (VITAMIN B6)*, RIBOFLAVIN*, VITAMIN A PALMITATE, THIAMIN MONONITRATE*, FOLIC ACID*,"
# "ENRICHED WHEAT FLOUR (FLOUR, NIACIN [VITAMIN B3], REDUCED IRON, THIAMIN MONONITRATE [VITAMIN B1], RIBOFLAVIN [VITAMIN B2], FOLIC ACID [VITAMIN B9]), BUTTERMILK, WHEY, SUGAR, WHOLE EGGS, WATER, SOYBEAN OIL, CONTAINS 2% OR LESS OF; BAKING POWDER (SODIUM ALUMINUM PHOSPHATE, BAKING SODA), SALT, CORNSTARCH, VANILLA EXTRACT, SOY FLOUR, SOY LECITHIN,"
# "WHOLE GRAIN ROLLED OATS (WITH OAT BRAN), SUGAR, NATURAL AND ARTIFICIAL FLAVORS, SALT, CALCIUM CARBONATE (A SOURCE OF CALCIUM), GUAR GUM, CARAMEL COLOR, SUCRALOSE (SPLENDA BRAND), NIACINAMIDE*, REDUCED IRON, PYRIDOXINE HYDROCHLORIDE*, VITAMIN A PALMITATE, RIBOFLAVIN*, THIAMIN MONONITRATE*, FOLIC ACID*,"

# "*BROWN RICE, WILD CAUGHT** ALASKAN SALMON, *BROCCOLI, WATER, *JAPONIA RICE, *AGAVE SYRUP, *WALNUTS, *DRIED CRANBERRIES (*CRANBERRIES, *SUGAR, *SUNFLOWER OIL), *EXTRACT VIRGIN OLIVE OIL, *ORGANE JUICE CONCENTRATE, *RICE FLOUR, SEA SALT, *SPICES, ONION POWDER, XANTHAN GUM, *LEMON PEEL POWDER, ONION GRANULATED,"

# "MONTEREY JACK CHEESE (PASTEURIZED MILK, CHEESE CULTURE, SALT, ENZYMES), CHEDDAR CHEESE (PASTEURIZED MILK, CHEESE CULTURE, SALT, ENZYMES, ANNATTO [COLOR]), ASADERO CHEESE (PASTEURIZED MILK, CHEESE CULTURE, SALT AND ENZYMES), QUESO BLANCO CHEESE (PASTEURIZED MILK, CHEESE CULTURE, SALT AND ENZYMES), POTATO STARCH, CORN STARCH AND CALCIUM SULFATE ADDED TO PREVENT CAKING, NATAMYCIN, (A NATURAL MOLD INHIBITOR)"

# "CRUST: (WHEAT FLOUR, WATER, CORN OIL, YEAST, SALT), LOW MOISTURE PART SKIM MOZZARELLA CHEESE: (PASTEURIZED PART SKIM MILK, CHEESE CULTURES, SALT, ENZYMES), ASIAGO CHEESE: (PASTEURIZED PART SKIM MILK, CHEESE CULTURES, SALT, ENZYMES), SAUCE: (TOMATO PUREE, WATER, OREGANO, SALT, BLACK PEPPER)."

# "LOLLIPOP: (GLUCOSE, SUGAR, LACTIC ACID, ARTIFICIAL FLAVOR, POLYSORBATE 80, VEGETABLE OIL (SOY OIL), COLORS FD&C YELLOW NO. 6) POWDER: (IODIZED SALT, CITRIC ACID, SUGAR, CHILI POWDER, DEXTROSE, SILICON DIOXIDE, COLOR FD&C RED NO. 40 LAKE)."

# "RICE NOODLES (RICE FLOUR, WATER), SEASONING PACKET: (SUGAR, SALT, MALTODEXTRIN, SOY SAUCE POWDER [SOYBEAN, SALT, WHEAT], GARLIC POWDER, MUSHROOM POWDER, SPRING ONION FLAKES, ARTIFICIAL MUSHROOM FLAVOR, WHITE PEPPER, YEAST EXTRACT, CARAMEL COLOR), OIL PACKET: (RICE BRAN OIL), VEGETABLE PACKET: (DRIED MUSHROOM FLAKE)."


class ProductMemoDataDrivenTest(unittest.TestCase):

    @parameterized.expand([
        ("unclosed single bracket", "item 1 (some text, item 2", ["item 1", "some text", "item 2"]),
        ("double comma", "item 1 ,, item 2", ["item 1", "item 2"]),
        ("comma in the end", "NIACIN,", ["niacin"]),
        ("very faulty writing",
         "DRIED CRANBERRIES ,(SUGAR ,GLYCERIN ,,)CINNAMON ,GROUND FLAX ,SALT ,,",
         ["dried cranberries", "cinnamon", "ground flax", "salt"]),
    ])
    @timeout_decorator.timeout(1)
    def test_all_cases(self, description, input, expected):
        result = ProductParser()._process_product_memo(input)

        self.assertEqual(expected, list(map(lambda i: i.name, result)), description)

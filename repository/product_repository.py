import json

import pydgraph
from pydgraph import Operation

from models.product_models import FoodProduct
from utils.json_encoder import JSONEncoderEnhancedWithDateSerialization


class DataSource:
    def __init__(self) -> None:
        super().__init__()
        client_stub = pydgraph.DgraphClientStub('localhost:9080')
        self.client = pydgraph.DgraphClient(client_stub)


# TODO: highly experimental
class ProductRepository:

    def __init__(self, data_source: DataSource) -> None:
        self.db = data_source.client

    def addProducts(self, products: [FoodProduct]):
        txn = self.db.txn()
        try:

            product_dicts = []

            for product in products:
                product_dict = json.loads(json.dumps(product, cls=JSONEncoderEnhancedWithDateSerialization))
                product_dicts.append(product_dict)

            txn.mutate(set_obj=product_dicts)
            txn.commit()
            return product_dicts
        finally:
            txn.discard()

    def _addMissingInformationSources(self, txn, information_source):
        pass

    def _addMissingManufacturers(self, txn, manufacturer):
        pass

    def _addMissingIngredients(self, txn, ingredients):
        pass

    def _dropAll(self):
        return self.db.alter(Operation(drop_all=True))

    def _createSchema(self):
        schema = """
            <abbreviation>: string .
            <barcode>: string .
            <date_available>: string .
            <date_modified>: string .
            <ingredients>: uid @count @reverse .
            <label>: string @index(exact) .
            <manufactured_by>: uid @count @reverse .
            <name>: string .
            <source>: uid .
            <usda_food_db_id>: string .
        """
        return self.db.alter(Operation(schema=schema))


if __name__ == "__main__":
    repo = ProductRepository(DataSource())
    # Run query.
    query = """query someItems($findItemRegex: string) {
 someItems(func: eq(label, $findItemRegex)) {
  name
  uid
  usda_food_db_id
  manufactured_by {
    name
  }
 }
}"""
    variables = {'$findItemRegex': 'product'}

    res = repo.db.query(query, variables=variables)
    # If not doing a mutation in the same transaction, simply use:
    # res = client.query(query, variables=variables)

    ppl = json.loads(res.json)

    # Print results.
    print('Number of people named "Alice": {}'.format(len(ppl['someItems'])))
    for person in ppl['someItems']:
        print(person)

    repo._dropAll()
    repo._createSchema()

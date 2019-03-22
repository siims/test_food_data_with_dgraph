import json
from datetime import datetime
from typing import Optional

import pydgraph

from models.ProductModels import Product


class DataSource:
    def __init__(self) -> None:
        super().__init__()
        client_stub = pydgraph.DgraphClientStub('localhost:9080')
        self.client = pydgraph.DgraphClient(client_stub)


class ProductRepository:

    def __init__(self, data_source: DataSource) -> None:
        super().__init__()
        self.db = data_source.client

    def addProduct(self, product: Product) -> Optional[Product]:
        txn = self.db.txn()
        try:
            self._addMissingInformationSources(txn, product.information_source)
            self._addMissingManufacturers(txn, product.manufactured_by)
            self._addMissingIngredients(txn, product.ingredients)
            product_dict = product.__dict__
            product_dict["label"] = "product"
            product_dict.pop("information_source")
            product_dict["manufactured_by"] = product_dict["manufactured_by"].__dict__
            product_dict["manufactured_by"]["label"] = "company"
            product_dict.pop("ingredients")
            product_dict.pop("nutrients")
            product_dict["date_modified"] = product_dict["date_modified"].isoformat()
            product_dict["date_available"] = product_dict["date_available"].isoformat()
            # txn.mutate(set_obj=p)
            txn.mutate(set_obj=product_dict)
            txn.commit()
            return None
        finally:
            txn.discard()

    def _addMissingInformationSources(self, txn, information_source):
        pass

    def _addMissingManufacturers(self, txn, manufacturer):
        pass

    def _addMissingIngredients(self, txn, ingredients):
        pass


if __name__ == "__main__":
    repo = ProductRepository(DataSource())
    # Run query.
    query = """query someItems($findItemRegex: string) {
 someItems(func: regexp(name, $findItemRegex)) {
  name
  starring {
   name
  }
 }
}"""
    variables = {'$findItemRegex': '/^Star Wars.*/'}

    res = repo.db.query(query, variables=variables)
    # If not doing a mutation in the same transaction, simply use:
    # res = client.query(query, variables=variables)

    ppl = json.loads(res.json)

    # Print results.
    print('Number of people named "Alice": {}'.format(len(ppl['someItems'])))
    for person in ppl['someItems']:
        print(person)

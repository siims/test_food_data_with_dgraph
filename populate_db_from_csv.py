import logging

from csv_parser.product_parser import ProductParser
from repository.product_repository import DataSource, ProductRepository

if __name__ == "__main__":
    products = ProductParser().parse()
    repo = ProductRepository(DataSource())
    repo.addProducts(products)
    logging.info(f"Finished adding #{len(products)} products")

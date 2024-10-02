"""
@title : Order
@description : Class defining what is an order
"""

from utils.types import Location


class Order:
    """
        An order is representing a need of specific products at a given location.

        Class is defined by:
            - id
            - initial_amount
            - location
            - amount
            - products
        """

    """ Constructor """

    def __init__(self, order_id: int, location: Location, products: list[int]):
        self.id = order_id
        self.initial_amount = sum(products)
        self.location = location
        self.products = {product_type: products.count(product_type) for product_type in products}

    def is_completed(self) -> bool:
        """
            - Check if an order is completed or not
            :return:        True if the drone is completed, False if it is not
        """
        return all(q == 0 for q in self.products.values())

"""
@title : Drone
@description : Class defining what is a drone
"""

from utils.types import Action, Location
from utils.Order import Order
from utils.Warehouse import Warehouse


class Drone:
    """
        A drone is here to transit certain products between warehouses and orders.

        Class is defined by:
            - id
            - max_payload
            - location
            - current_load
            - available_turn
            - products
    """

    """ Constructor """

    def __init__(self, drone_id: int, max_payload: int, location: Location):
        self.id = drone_id
        self.max_payload = max_payload
        self.location = location
        self.current_load = 0
        self.available_turn = 0
        self.products = {}

    def can_load(self, product_type: int, quantity: int, product_weights: list[int]) -> bool:
        """
            - Check if a drone can load a specific quantity of a product
            :return:        True if the drone can load, False if it can't
        """
        incoming_weight = quantity * product_weights[product_type]
        return self.current_load + incoming_weight <= self.max_payload

    def has_remaining(self, order: Order) -> bool:
        """
            - Check for each product in an order if the drone has the required quantity of this product
            :return:        True if the drone has the required quantity of all the product of the order,
                            False if it has not
        """
        return all(self.has_product_asked(product, quantity) for product, quantity in order.products.items())

    def has_product_asked(self, product: int, quantity: int) -> bool:
        """
            - Check if a drone has the required quantity of a product
            :return:        True if the drone has the required quantity of a product, False if it has not
        """
        return product in self.products and self.products[product] >= quantity

    def load(self, warehouse: Warehouse, product_type: int, quantity: int, product_weights: list[int],
             history: list[Action]) -> None:
        """
            - Try to load a specific quantity of a product from a warehouse
            - Update the history with the appropriate command if the drone has loaded the product
        """
        total_weight = quantity * product_weights[product_type]
        # Updates the current weight of the drone
        self.current_load += total_weight
        # Adds the new instruction to the history
        history.append([self.id, 'L', warehouse.id, product_type, quantity])
        # Updates the current location
        self.location = warehouse.location
        # Adds the products to the stocks of the drone
        self.products[product_type] = self.products.get(product_type, 0) + quantity
        # Removes the products from the warehouse's stocks
        warehouse.products[product_type] -= quantity

    def deliver(self, order: Order, product_type: int, quantity: int, product_weights: list[int],
                history: list[Action]) -> None:
        """
            - Update the solution with the appropriate command after the drone has delivered the product
        """
        # Removes the products from the order list
        order.products[product_type] -= quantity
        # Lowers the drone current weight
        self.current_load -= quantity * product_weights[product_type]
        # Unload the drone
        self.products[product_type] -= quantity
        # Adds the new instruction to the history
        history.append([self.id, 'D', order.id, product_type, quantity])
        # Updates the current location
        self.location = order.location

"""
@title : Challenge
@description : Class defining what is a challenge
"""

from utils.Warehouse import Warehouse
from utils.Order import Order
from utils.Drone import Drone
from utils.types import Action, Location
from math import sqrt, ceil


class Challenge:
    """
        The Challenge class if here to store all the information given by the input files.
        It is mainly used to give and memorize this information in order to feed the algorithms with it.

        Class is defined by:
            - row_count
            - columns_count
            - deadline
            - max_payload
            - product_weights
            - warehouses
            - orders
            - drones
    """

    """ Constructor """

    def __init__(self, rows_count: int, columns_count: int, drone_count: int, deadline: int, max_payload: int,
                 product_weights: list[int], warehouses: list[Warehouse], orders: list[Order]):
        self.rows_count = rows_count
        self.columns_count = columns_count
        self.deadline = deadline
        self.max_payload = max_payload
        self.product_weights = product_weights
        self.warehouses = warehouses
        self.orders = orders
        self.drones = []

        # Generates the drones
        for i in range(drone_count):
            self.drones.append(Drone(i, self.max_payload, self.warehouses[0].location))

    def get_location(self, action: Action) -> Location:
        """
            - Get the location of the warehouse or the order
            :return:        The location of the warehouse if the action is 'L' or 'U',
                            the location of the order if the action is not 'L' or 'U'
        """
        if action[1] in {'L', 'U'}:
            return list(filter(lambda w: w.id == action[2], self.warehouses))[0].location
        else:
            return list(filter(lambda o: o.id == action[2], self.orders))[0].location

    """ Static Method """
    @staticmethod
    def calculate_distance(location1: Location, location2: Location):
        """
            - Calculate the distance between two location
            :return:        The distance
        """
        return ceil(sqrt((location1[0] - location2[0]) ** 2 + (location1[1] - location2[1]) ** 2))

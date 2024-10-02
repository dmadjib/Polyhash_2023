"""
@title : Parser
@description : Parses a given input file into a Challenge object
"""

from utils.Warehouse import Warehouse
from utils.Order import Order
from utils.Challenge import Challenge


def parse_challenge(filename: str) -> Challenge:
    """
        - Reads an input file and generates a Challenge object.
        :return:        A Challenge object fed with the information from the input file
    """

    with open(filename, 'r') as f:
        rows, columns, drone_count, deadline, max_load = [int(v) for v in f.readline().split()]

        # Useless number of products
        f.readline()

        product_weights = [int(weight) for weight in f.readline().split()]

        warehouse_count = int(f.readline())
        warehouse_list = []

        # Generates the warehouses
        for warehouse_id in range(warehouse_count):
            x, y = [int(v) for v in f.readline().split()]
            warehouse_products = [int(v) for v in f.readline().split()]
            warehouse_list.append(Warehouse(warehouse_id, (x, y), warehouse_products))

        order_count = int(f.readline())
        order_list = []

        # Generates the orders
        for order_id in range(order_count):
            x, y = [int(v) for v in f.readline().split()]
            # Useless count of products in order
            f.readline()
            order_product = [int(v) for v in f.readline().split()]
            order_list.append(Order(order_id, (x, y), order_product))

    return Challenge(rows, columns, drone_count, deadline, max_load, product_weights, warehouse_list, order_list)

"""
@title : Solver
@description : Solve in different way the Google Hash problem, as well as calculating the score
"""

from utils.Challenge import Challenge
from utils.Warehouse import Warehouse
from utils.Order import Order
from utils.Drone import Drone
from utils.types import Action
from utils.Segment import Segment
from math import sqrt, ceil
from copy import deepcopy


def save_solution(file_name: str, solution: list[Action]) -> None:
    """
        Saves the given list of actions in the given file location
    """
    with open(f'{file_name}.txt', 'w') as outfile:
        outfile.write(str(len(solution)) + '\n')
        for i in range(len(solution)):
            for j in range(len(solution[i])):
                outfile.write(str(solution[i][j]) + ' ')
            outfile.write('\n')


def score_solution(solution: list[Action], challenge: Challenge) -> int:
    """
        Calculates the score for a given solution
        :return:        The score of the solution
    """
    score = 0

    orders = {order.id:order for order in challenge.orders}

    # Saves the completed orders, so they don't count if there is a delivery afterward
    completed_orders = []

    # Saves the turns where there have been a delivery at a specific order
    order_turns = {}

    for drone in challenge.drones:
        # We are only looking at the moves of the given drone
        moves = list(filter(lambda move: move[0] == drone.id, solution))

        turns = 0

        # Initial position
        pos = challenge.warehouses[0].location

        # For every action
        for move in moves:
            # If the action is on a warehouse
            if move[1] in {'L', 'U'}:
                # If the next location is a warehouse
                next_pos = list(filter(lambda w: w.id == move[2], challenge.warehouses))[0].location
                # Distance flown plus 1 turn for the action itself
                turns += Challenge.calculate_distance(pos, next_pos) + 1

            # If the action is on an order
            elif move[1] == 'D':
                # If the action is on an order
                next_pos = orders[move[2]].location
                # Distance flown
                turns += Challenge.calculate_distance(pos, next_pos)

                # Insert the delivery action in the delivery turns
                if move[2] not in completed_orders:
                    if move[2] not in order_turns.keys():
                        order_turns[move[2]] = [turns]
                    else:
                        order_turns[move[2]].append(turns)

                # Removing the given products from the order list
                orders[move[2]].products[move[3]] -= move[4]

                # Adding the delivery turn
                turns += 1

                # If every product has been delivered
                if move[2] not in completed_orders and orders[move[2]].is_completed():
                    completed_orders.append(move[2])

            # If the action is just waiting
            elif move[1] == 'W':
                turns += move[2]
                continue

            # If there is a problem with the given action
            else:
                continue

            # Updating the new drone location
            pos = next_pos

    # Calculating the score for each completed order
    for order, turns in order_turns.items():
        if orders[order].is_completed():
            score += ceil(((challenge.deadline - max(turns)) / challenge.deadline) * 100)

    return score


def path_for_order(challenge: Challenge, warehouses: list[Warehouse], order: Order, drone: Drone) -> list[Action]:
    """
        Reused algorithm, used for calculating the most optimal path for a drone in order to deliver a given order
        depending on the challenge and the sorted list of warehouses
    """
    # The list of actions for this order
    actions = []

    # Iterator for the warehouses
    warehouse_count = 0

    while not order.is_completed():
        # While the drone is not full and has not everything needed
        # (If the iterator reaches the last warehouse, the drone stops looking for loading too)
        while drone.current_load < challenge.max_payload and not drone.has_remaining(order):
            warehouse = warehouses[warehouse_count]

            # For each needed product
            for product, amount in order.products.items():
                # If the drone needs it and the warehouse has some
                if not drone.has_product_asked(product, amount) and warehouse.products[product] > 0:
                    # How many items will be taken
                    to_load = min(warehouse.products[product], amount)

                    # Loads as much as possible the drone with the given product
                    for _ in range(to_load):
                        if drone.can_load(product, 1, challenge.product_weights):
                            drone.load(warehouse, product, 1, challenge.product_weights, actions)

            warehouse_count += 1

            # If there is no warehouse left to visit, then the drone starts goes deliver
            if warehouse_count == len(warehouses):
                warehouse_count = 0
                break

        # For each product the drone is carrying
        for product, quantity in drone.products.items():
            # If the order needs it
            if product in order.products and order.products[product] > 0 and quantity > 0:
                # Calculating the amount to deliver
                to_deliver = quantity if order.products[product] >= quantity else order.products[product]
                # Deliver action
                drone.deliver(order, product, to_deliver, challenge.product_weights, actions)

    # Returns the actions for a given order
    return actions


def naive(challenge: Challenge) -> list[Action]:
    """
        Naive algorithm. Every order has one drone, every drone is doing the same amount of order.
        For every order, the drone is taking as much as he can at the closest warehouses from the order.
        :return:        The solutions generated by the algorithm
    """
    solutions = []

    # For every order
    for count, order in enumerate(challenge.orders):
        # Choosing the drone for the order (id of the order % the number of drones)
        drone = challenge.drones[count % len(challenge.drones)]

        # The list of warehouses
        warehouses = sorted(
            challenge.warehouses,
            key=lambda w: Challenge.calculate_distance(w.location, drone.location)
        )

        # Gets the actions for this order
        order_actions = path_for_order(challenge, warehouses, order, drone)

        for action in order_actions:
            solutions.append(action)

    return solutions


def product_by_product(challenge: Challenge) -> list[Action]:
    """
        This algorithm is counting the amount of products needed for all orders in the challenge. Then, after sorting
        the products in order of the highest quantity, all the drones are loading and delivering one product at a time.
        :return:        The solutions generated by the algorithm
    """
    solutions = []

    # Counting the needed amount for each product
    total_quantity = {}

    for order in challenge.orders:
        for product, quantity in order.products.items():
            total_quantity[product] = total_quantity.get(product, 0) + quantity

    # Storing for each product the IDs of each warehouse that has this product in stock
    product_warehouses = {}

    for warehouse in challenge.warehouses:
        for product in range(len(warehouse.products)):
            if warehouse.products[product] > 0:
                if product in product_warehouses.keys():
                    product_warehouses[product].append(warehouse.id)
                else:
                    product_warehouses[product] = [warehouse.id]

    # Sorting the products by the amount present in the orders
    total_quantity_sorted = sorted(total_quantity.keys(), key=lambda p: total_quantity[p], reverse=True)

    # Saving the last drone used for the last product, so the algorithm can continue with the next drones for
    # new products deliveries, without always using the same drones over and over again
    last_drone = 0

    # For each product
    for product in total_quantity_sorted:
        # The maximum amount drones can carry for this specific product
        can_load = challenge.max_payload // int(challenge.product_weights[product])
        # While there are still some of this product to deliver
        while total_quantity[product] > 0:
            # If the last used drone was the last one, go back to the first one
            if last_drone >= len(challenge.drones):
                last_drone = 0

            drone = challenge.drones[last_drone]

            # Sorting the warehouses depending on the distance with the drone
            warehouses = sorted(
                product_warehouses[product],
                key=lambda w_id: Challenge.calculate_distance(drone.location, challenge.warehouses[w_id].location)
            )

            # Warehouse iterator
            warehouse_count = 0

            # While there are still products to deliver and the drone can load at least one product
            while total_quantity[product] > 0 and drone.can_load(product, 1, challenge.product_weights):
                # Will never get beyond the last warehouse by design
                warehouse = challenge.warehouses[warehouses[warehouse_count]]

                # Loading as many products as possible
                load = min(total_quantity[product], warehouse.products[product], can_load)

                # Removing the load from the products left to deliver
                total_quantity[product] -= load

                # Loading the products
                drone.load(warehouse, product, load, challenge.product_weights, solutions)

                # Removing the warehouse from the list of warehouses which have this product
                if warehouse.products[product] == 0:
                    product_warehouses[product].remove(warehouse.id)

                warehouse_count += 1

            # Fetching all the orders which needs this product
            orders = list(filter(lambda o: product in o.products.keys() and o.products[product] > 0, challenge.orders))

            # Sorting the orders depending on their distance with the drone
            orders = sorted(orders, key=lambda o: Challenge.calculate_distance(o.location, drone.location))

            # Order iterator
            order_count = 0

            # While the drone is not empty
            while drone.products[product] > 0:
                # Fetching the next order where there is a delivery to do
                order = challenge.orders[orders[order_count].id]

                # Taking the needed amount for this specific order
                deliver = min(drone.products[product], order.products[product])

                # Delivering the products
                drone.deliver(order, product, deliver, challenge.product_weights, solutions)

                # Next order to deliver
                order_count += 1

            # When the drone has finished palling his route for this iteration, next drone
            last_drone += 1

    return solutions


def stack_segments(challenge: Challenge) -> list[Action]:
    """
        Splitting in a smart way the orders among the drones.
        Every order is represented by a "segment", which the most optimised list of actions to unroll in order to
        deliver the order as soon as possible.
        Then, while there are still orders to process, the first drone which has nothing to do will choose the order
        which will take the less time to deliver.

        AT THIS DAY : One of the simplest algorithms, but the best one so far.

        :return:        The solutions generated by the algorithm
    """
    solutions = []

    # List of segments
    segments = []

    # Fake drone used for the generation of each segment
    drone = challenge.drones[0]

    # Generating a segment for each order
    for order in challenge.orders:
        # Sorted warehouses depending on their distance from the order
        warehouses = sorted(
            challenge.warehouses,
            key=lambda w: Challenge.calculate_distance(w.location, order.location)
        )

        # Gets the actions for this order
        actions = path_for_order(challenge, warehouses, order, drone)

        # When the order is completed, all its actions are added to the segment
        segments.append(Segment(challenge.get_location(actions[0]), order.location, challenge, actions, order.id))

    # Logs of every segment accomplished by each drone
    paths = {drone.id: [] for drone in challenge.drones}
    # Saving the amount of turns used for each drone
    # Can be calculated from 'paths', but this dict is here for saving time and memory
    length_paths = {drone.id: 0 for drone in challenge.drones}
    # Choosing the smallest segments for the first iteration of the drones
    simplest_segments = sorted(segments, key=lambda s: s.turns, reverse=True)

    # For each drone
    for i in range(len(challenge.drones)):
        # In case there are more drones than there are orders
        if len(simplest_segments) > 0:
            # Taking the simplest order
            segment = simplest_segments.pop()
            segments.remove(segment)
            # Adding it to the drone order list
            paths[i].append(segment)
            length_paths[i] += segment.turns

    # Where now need to split the segments among the drones
    while len(segments) > 0:
        # Selecting the drone which will finish his deliveries the earliest at this point
        drone_id = min(length_paths, key=length_paths.get)

        # Choosing the segment which is the smallest (the one taking the less time for delivery)
        segment = min(segments, key=lambda s: s.turns)
        # Removing the segment from the list
        segments.remove(segment)
        # Adding the segment to the drone order list
        paths[drone_id].append(segment)
        length_paths[drone_id] += segment.turns + Challenge.calculate_distance(segment.start, paths[drone_id][-1].end)

    # When all the segments are attributed to a drone
    # Adding all the actions to the final list

    for drone_id, segments in paths.items():
        for segment in segments:
            for action in segment.actions:
                # Adding the actions with the real drone ID
                solutions.append([drone_id, action[1], action[2], action[3], action[4]])

    return solutions


def split_orders(orders: list[Order], nb_zones: int) -> list[list[Order]]:
    """
        Splitting in N (nb_zones) lists the given list of orders.
        Used in the "layers" algorithm.
        :return:        A list of the lists of split orders
    """
    sub_list_length = len(orders) // nb_zones
    results = []

    # Divide the list in nb_zones lists
    for i in range(nb_zones):
        first = i * sub_list_length
        last = (i + 1) * sub_list_length

        # For the last list, just adding the remaining orders
        if i == nb_zones - 1:
            last = len(orders)

        results.append(orders[first:last])

    return results


def layers(challenge: Challenge) -> list[Action]:
    """
        Algorithm splitting the orders in a certain amount of zones, which are taking cared of one by one, with all
        the drones. The order of the zones is determined by the score each one of them is creating.
        It is using one of the other algorithms for completing a zone.
        :return:        The solutions generated by the algorithm
    """
    solutions = []

    NB_ZONES = 3

    # Sorting the orders depending on their distances from the center of the board
    sorted_orders = sorted(
        challenge.orders,
        key=lambda o: Challenge.calculate_distance(
            o.location,
            (challenge.rows_count // 2, challenge.columns_count // 2)
        )
    )

    # Splitting the orders
    order_zones = split_orders(sorted_orders, NB_ZONES)
    # Saving the challenge for later (the algorithm will empty the orders)
    future_order_zones = deepcopy(order_zones)

    zones_scores = []

    # For each zone
    for i, zone in enumerate(order_zones):
        # Saving a new instance of the challenge, so it won't be emptied for the next zones
        new_challenge = deepcopy(challenge)
        new_challenge.orders = zone
        # Also saving another instance of challenge for the scoring part
        score_challenge = deepcopy(new_challenge)
        # Associating the score of the zone with its id
        zones_scores.append((i, score_solution(workload_repartition(new_challenge), score_challenge)))

    # Sorting the zones depending on the score they are each returning
    sorted_zones_scores = sorted(zones_scores, key=lambda x: x[1], reverse=True)

    # Running the algorithm one more time with all the sorted zones together
    for zone_id, score in sorted_zones_scores:
        challenge.orders = future_order_zones[zone_id]
        local_solutions = workload_repartition(challenge)
        for solution in local_solutions:
            solutions.append(solution)

    return solutions


def workload_repartition(challenge: Challenge) -> list[Action]:
    """
        A new version of the stack segments algorithm. Here, it is not one segment per order, but one segment per
        delivery operation (one warehouse and one order to deliver). All these small operations are dispatched among
        the drones equally. A segment may go to multiple warehouses if they are not too far away.
        :return:        The solutions generated by the algorithm
    """
    solutions = []

    # Used to see if going to more warehouses is a big detour
    LONGER_THAN_ORDER_RATIO = 3
    # Percentage of the importance of "percentage of completion" against "length of the segment" while trying to choose
    # a new segment to complete
    RATIO_ORDER_COMPLETION = 0.76

    # List of segments
    segments = []

    # Fetches an order from its ID
    orders_by_id = {order.id: i for i, order in enumerate(challenge.orders)}

    # Generating a segment for each order
    for order in challenge.orders:
        # Sorting the warehouses depending on their distance with the order
        warehouses = sorted(
            challenge.warehouses,
            key=lambda w: Challenge.calculate_distance(w.location, order.location)
        )

        # Warehouse iterator
        warehouse_count = 0

        # Products available for the order in each warehouse
        workload = {}

        # Products to find for the order
        products_remaining = order.products

        # While there are some products missing
        while set(products_remaining.values()) != {0}:
            # Looping on the warehouses
            warehouse = warehouses[warehouse_count]

            # For each product
            for product, amount in order.products.items():
                # If the given products are still missing, and the warehouse has some
                if products_remaining[product] > 0 and warehouse.products[product] > 0:
                    # Choosing how many to pick up
                    load = min(warehouse.products[product], amount)

                    # Filling the list with products available in the warehouse
                    if warehouse not in workload.keys():
                        workload[warehouse] = {product: load}
                    else:
                        workload[warehouse][product] = load

                    # Updating the amount of products to find for the order
                    products_remaining[product] -= load

            # Next warehouse
            warehouse_count += 1

        # While there are things to load in the drones for the order
        while not all(all(q == 0 for q in w.values()) for w in workload.values()):
            # Listing the actions for a specific segment
            actions = []

            # Remaining load in the drone
            remaining_load = challenge.max_payload

            # For each warehouses
            for warehouse, products in workload.items():
                # By default, the drone won't visit the warehouse
                visit_warehouse = False

                # If the drone is empty, then it can visit the warehouse
                if len(actions) == 0:
                    visit_warehouse = True
                # If the drone is not empty (so it already went to a warehouse)
                elif len(actions) > 0:
                    # Calculating the distances between
                    # The warehouse where the drone may go and the order (a longer path than the one he is currently
                    # using from the last warehouse he visited)
                    d_warehouse = Challenge.calculate_distance(challenge.get_location(actions[-1]), warehouse.location)
                    d_warehouse_to_order = Challenge.calculate_distance(order.location, warehouse.location)
                    # And between its last warehouse and the order (the current planned path)
                    d_order_current = Challenge.calculate_distance(challenge.get_location(actions[-1]), order.location)

                    # If doing a detour at this new warehouse is less than RATIO times longer than the current path
                    if d_warehouse + d_warehouse_to_order <= d_order_current * LONGER_THAN_ORDER_RATIO:
                        # Then the drone may visit the warehouse
                        visit_warehouse = True

                # If the drone can visit the warehouse
                if visit_warehouse:
                    # For each product in the warehouse
                    for product, quantity in products.items():
                        # If the current product is not here, then continue
                        if quantity == 0:
                            continue

                        # Maximum possible load for the drone
                        can_load = (remaining_load // challenge.product_weights[product])

                        # If the product cannot be loaded at all
                        if can_load == 0:
                            continue

                        # Loading the minimum quantity between what the warehouse has and what the drone can load
                        load = min(quantity, can_load)

                        # Adding the action to the actions of this segment
                        # False drone ID, which will be changed at the end
                        actions.append([99999, 'L', warehouse.id, product, load])
                        # Removing the products from the needed workload
                        workload[warehouse][product] -= load
                        # Removing the products from the warehouse
                        warehouse.products[product] -= load
                        # Updating the remaining space in the drone
                        remaining_load -= challenge.product_weights[product] * load

            # When the drone loaded up himself with what he can, among one or more warehouses

            # Grouping together the products for a faster delivery
            product_list = {}

            for action in actions:
                product_list[action[3]] = product_list.get(action[3], 0) + action[4]

            # Adding the delivery actions
            for product, quantity in product_list.items():
                actions.append([99999, 'D', order.id, product, quantity])

            # When the delivery is completed, a new segment is created with the given actions
            segments.append(Segment(challenge.get_location(actions[0]), order.location, challenge, actions, order.id))

    # Logs of every segment accomplished by each drone
    paths = {drone.id: [] for drone in challenge.drones}
    # Saving the amount of turns used for each drone
    # Can be calculated from 'paths', but this dict is here for saving time and memory
    length_paths = {drone.id: 0 for drone in challenge.drones}

    # Counting the amount of segments per order (used to get the easiest orders to complete)
    segments_per_orders = {
        order_id: len(list(filter(lambda s: s.order_id == id, segments))) for order_id in orders_by_id.keys()
    }

    # Choosing the easiest segments for starting the drones
    simplest_segments = sorted(segments, key=lambda s: segments_per_orders[s.order_id], reverse=True)

    # For each drone
    for i in range(len(challenge.drones)):
        # Security in case there are fewer orders than drones
        if len(simplest_segments) > 0:
            # Removing the last (easiest) segment from the list
            segment = simplest_segments.pop()
            segments.remove(segment)
            # Adding it to the logs of the drones
            paths[i].append(segment)
            length_paths[i] += segment.turns

    # Longest segment + the longest possible travel distance (used for comparing the length of the segments)
    if len(segments) > 0:
        longest_time = (
                sorted(segments, key=lambda s: s.turns)[-1].turns +
                sqrt(challenge.rows_count ** 2 + challenge.columns_count ** 2)
        )

        # Where now need to split the segments among the drones
        while len(segments) > 0:
            # Selecting the drone which will finish his deliveries the earliest at this point
            drone_id = min(length_paths, key=length_paths.get)

            # Choosing the next segment depending on two factors
            # If the segment is in an order which will finish soon (high percentage of completion)
            # If the drone will take a lot of time to realise the segment
            # Scoring from 0 to 100
            # ID of the segment, score
            next_segment = (-1, 100)

            # For each segment
            for count, segment in enumerate(segments):
                # Fetching the linked order
                order = challenge.orders[orders_by_id[segment.order_id]]
                # Completion percentage
                order_completion = ((order.initial_amount - sum(order.products)) / order.initial_amount) * 100
                time_spent = segment.turns + Challenge.calculate_distance(segment.start, paths[drone_id][-1].end)
                # Percentage of maximal time used
                time_proportion = (time_spent / longest_time) * 100
                coefficient = RATIO_ORDER_COMPLETION * order_completion + (1 - RATIO_ORDER_COMPLETION) * time_proportion

                # Choosing the best segment depending on the coefficient
                if coefficient < next_segment[1]:
                    next_segment = (count, coefficient)

            # Fetching the best segment
            segment = segments[next_segment[0]]
            # Removing it from the segment list
            segments.remove(segment)
            # Adding the segment to the drone logs
            paths[drone_id].append(segment)
            length_paths[drone_id] += (
                    segment.turns +
                    Challenge.calculate_distance(segment.start, paths[drone_id][-1].end)
            )

    # When all the segments are attributed to a drone
    # Adding all the actions to the final list

    for drone_id, segments in paths.items():
        for segment in segments:
            for action in segment.actions:
                # Adding the action with the real drone ID
                solutions.append([drone_id, action[1], action[2], action[3], action[4]])

    return solutions


def solve(challenge):
    # Listing all the algorithms
    # As 'stack segment' is for now the best algorithm, the other ones are commented for speed concerns
    solvers = {
        # 'naive': naive(deepcopy(challenge)),
        'stack_segments': stack_segments(deepcopy(challenge)),
        # 'product_by_product': product_by_product(deepcopy(challenge)),
        # 'workload_repartition': workload_repartition(deepcopy(challenge)),
        # 'layers_workload_repartition': layers(deepcopy(challenge))
    }

    solutions = {}

    for algo, solution in solvers.items():
        solutions[algo] = score_solution(solvers[algo], deepcopy(challenge))
        print(f'Solution \'{algo}\' : {solutions[algo]}')

    best_solution = max(solutions.keys(), key=lambda a: solutions[a])

    print('The best solution is :', best_solution)

    return solvers[best_solution]

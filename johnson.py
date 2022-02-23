import operator
import random

from visualisation import plot_assigned_orders

from main import NB_COOKING_LINES, NB_PREP_LINES, Orders, generate_orders


def johnson_solver(number_of_orders: int, seed: float, plot: bool = True):
    random.seed(seed)
    orders = generate_orders(number_of_orders)
    orders = sorted(orders, key=lambda x: (x.vegetarian, min(x.prep_time, x.cooking_time)))
    first_list = list()
    second_list = list()

    for order in orders:
        if order.prep_time < order.cooking_time:
            first_list.append(order)
        else:
            second_list.insert(0, order)

    sorted_orders = tuple(first_list + second_list)
    sorted_orders = insert_prep_jobs_in_pair(NB_PREP_LINES, sorted_orders)
    sorted_orders = insert_cooking_jobs(NB_COOKING_LINES, sorted_orders)

    last_meal_cooking_end_time = max(
        order.cooking_start_time + order.cooking_time for order in sorted_orders
    )
    last_vegetarian_meal_cooking_end_time = max(
        order.cooking_start_time + order.cooking_time for order in sorted_orders if order.vegetarian
    )

    print("Last meal cooking end time: " + str(last_meal_cooking_end_time))
    print("Last vegetarian meal cooking end time: " + str(last_vegetarian_meal_cooking_end_time))
    if plot:
        plot_assigned_orders(sorted_orders)

    return last_meal_cooking_end_time


def insert_prep_jobs(nb_lines, sorted_orders: Orders):
    max_time = {nb: 0 for nb in range(1, nb_lines + 1)}
    orders_with_line = list()
    for order in sorted_orders:
        chosen_line = min(max_time.items(), key=operator.itemgetter(1))[0]
        order.prep_line = chosen_line
        order.prep_start_time = max_time[chosen_line]

        max_time[chosen_line] += order.prep_time
        orders_with_line.append(order)
    return tuple(orders_with_line)


def insert_prep_jobs_in_pair(nb_lines, sorted_orders: Orders):
    max_time = {nb: 0 for nb in range(1, nb_lines + 1)}
    orders_with_line = list()

    for order_1, order_2 in zip(sorted_orders[0::2], sorted_orders[1::2]):
        max_1 = max(max_time[1] + order_1.prep_time, max_time[2] + order_2.prep_time)
        max_2 = max(max_time[2] + order_1.prep_time, max_time[1] + order_2.prep_time)
        if max_1 < max_2:
            chosen_line_1 = 1
            chosen_line_2 = 2
        else:
            chosen_line_1 = 2
            chosen_line_2 = 1
        order_1.prep_line = chosen_line_1
        order_1.prep_start_time = max_time[chosen_line_1]
        order_2.prep_line = chosen_line_2
        order_2.prep_start_time = max_time[chosen_line_2]
        max_time[chosen_line_1] += order_1.prep_time
        max_time[chosen_line_2] += order_2.prep_time
        orders_with_line.append(order_1)
        orders_with_line.append(order_2)
    return tuple(orders_with_line)


def insert_cooking_jobs(nb_lines, sorted_orders: Orders):
    max_time = {nb: 0 for nb in range(1, nb_lines + 1)}
    orders_with_line = list()
    for order in sorted_orders:
        if order.prep_start_time + order.prep_time >= max(max_time.values()):
            chosen_line = max(max_time.items(), key=operator.itemgetter(1))[0]
            order.cooking_line = chosen_line
            order.cooking_start_time = order.prep_start_time + order.prep_time
        else:
            chosen_line = min(max_time.items(), key=operator.itemgetter(1))[0]
            order.cooking_line = chosen_line
            order.cooking_start_time = max(
                order.prep_start_time + order.prep_time, max_time[chosen_line]
            )

        max_time[chosen_line] = order.cooking_start_time + order.cooking_time
        orders_with_line.append(order)
    return tuple(orders_with_line)


def insert_cooking_jobs_in_pair(nb_lines, sorted_orders: Orders):
    max_time = {nb: 0 for nb in range(1, nb_lines + 1)}
    orders_with_line = list()
    for order_1, order_2 in zip(sorted_orders[0::2], sorted_orders[1::2]):
        end_prep_1 = order_1.prep_start_time + order_1.prep_time
        end_prep_2 = order_2.prep_start_time + order_2.prep_time
        max_time_1 = max(
            max(end_prep_1, max_time[1]) + order_1.prep_time,
            max(end_prep_2, max_time[2]) + order_2.prep_time,
        )
        max_time_2 = max(
            max(end_prep_1, max_time[2]) + order_1.prep_time,
            max(end_prep_2, max_time[1]) + order_2.prep_time,
        )
        if max_time_1 < max_time_2:
            chosen_line_1 = 1
            chosen_line_2 = 2
        else:
            chosen_line_1 = 2
            chosen_line_2 = 1

        order_1.cooking_line = chosen_line_1
        order_1.cooking_start_time = max(end_prep_1, max_time[chosen_line_1])
        order_2.cooking_line = chosen_line_2
        order_2.cooking_start_time = max(end_prep_2, max_time[chosen_line_2])

        max_time[chosen_line_1] = order_1.cooking_start_time + order_1.cooking_time
        max_time[chosen_line_2] = order_2.cooking_start_time + order_2.cooking_time

        orders_with_line.append(order_1)
        orders_with_line.append(order_2)

    return tuple(orders_with_line)

import operator
import random
from typing import Tuple

import gurobipy as grb
from visualisation import plot_assigned_orders

from main import (
    NB_COOKING_LINES,
    NB_PREP_LINES,
    STEP_SIZE,
    VEGETARIAN_IMPORTANCE_RATIO,
    Minutes,
    generate_orders,
)


def mip_solver(number_of_orders: int, seed: float, plot: bool = True):
    random.seed(seed)
    orders = generate_orders(number_of_orders)
    horizon = sum(order.prep_time + order.cooking_time for order in orders)
    time_steps = tuple(range(0, horizon + STEP_SIZE, STEP_SIZE))

    assignment_options = tuple((order, t_step) for order in orders for t_step in time_steps)
    with grb.Env() as env_grb, grb.Model(env=env_grb) as jsp_model:
        jsp_model.modelSense = grb.GRB.MINIMIZE
        var_max_end_time = jsp_model.addVar(
            vtype=grb.GRB.INTEGER,
            name="objective_function",
        )
        var_max_end_time_vegetarian = jsp_model.addVar(
            vtype=grb.GRB.INTEGER,
            name="objective_function",
        )
        var_prep_assignment = jsp_model.addVars(
            assignment_options, vtype=grb.GRB.BINARY, name="prep_assignment"
        )
        var_cooking_assignment = jsp_model.addVars(
            assignment_options,
            vtype=grb.GRB.BINARY,
            name="cooking_assignment",
        )

        jsp_model.addConstrs(var_prep_assignment.sum(order, "*") == 1 for order in orders)
        jsp_model.addConstrs(var_cooking_assignment.sum(order, "*") == 1 for order in orders)

        exp_prep_end_time = {
            order: grb.quicksum(
                (t_step + order.prep_time) * var_prep_assignment[order, t_step]
                for t_step in time_steps
            )
            for order in orders
        }
        exp_cooking_start_time = {
            order: grb.quicksum(
                t_step * var_cooking_assignment[order, t_step] for t_step in time_steps
            )
            for order in orders
        }
        # perp before cooking
        jsp_model.addConstrs(
            (exp_prep_end_time[order] <= exp_cooking_start_time[order] for order in orders),
            name="prep_before_cooking",
        )

        # overlap constraints
        jsp_model.addConstrs(
            grb.quicksum(
                grb.quicksum(
                    var_prep_assignment[order, t_step]
                    for t_step in covered_time_steps(t_step, order.prep_time)
                )
                for order in orders
            )
            <= NB_PREP_LINES
            for t_step in time_steps
        )

        jsp_model.addConstrs(
            grb.quicksum(
                grb.quicksum(
                    var_cooking_assignment[order, t_step]
                    for t_step in covered_time_steps(t_step, order.cooking_time)
                )
                for order in orders
            )
            <= NB_COOKING_LINES
            for t_step in time_steps
        )

        # objective function
        # main
        jsp_model.addConstrs(
            var_max_end_time
            >= grb.quicksum(
                (t_step + order.cooking_time) * var_cooking_assignment[order, t_step]
                for t_step in time_steps
            )
            for order in orders
        )
        # vegetarian objective function
        jsp_model.addConstrs(
            var_max_end_time_vegetarian
            >= grb.quicksum(
                (t_step + order.cooking_time) * var_cooking_assignment[order, t_step]
                for t_step in time_steps
            )
            for order in orders
            if order.vegetarian
        )
        # weighted sum
        jsp_model.setObjective(
            var_max_end_time + VEGETARIAN_IMPORTANCE_RATIO * var_max_end_time_vegetarian
        )

        jsp_model.optimize()

        for order in orders:
            order.prep_start_time = int(
                sum(t_step * var_prep_assignment[order, t_step].X for t_step in time_steps)
            )

            order.cooking_start_time = int(
                sum(t_step * var_cooking_assignment[order, t_step].X for t_step in time_steps)
            )

        orders = choose_line(NB_PREP_LINES, orders, "prep")
        orders = choose_line(NB_COOKING_LINES, orders, "cooking")

        last_meal_cooking_end_time = var_max_end_time.X
        last_vegetarian_meal_cooking_end_time = var_max_end_time_vegetarian.X

    print("Last meal cooking end time: " + str(last_meal_cooking_end_time))
    print("Last vegetarian meal cooking end time: " + str(last_vegetarian_meal_cooking_end_time))
    if plot:
        plot_assigned_orders(orders)

    return last_meal_cooking_end_time


def choose_line(nb_lines, orders, task_type):
    max_time = {nb: 0 for nb in range(1, nb_lines + 1)}
    orders_wiht_line = list()
    for order in sorted(orders, key=lambda x: getattr(x, task_type + "_start_time")):
        chosen_line = min(max_time.items(), key=operator.itemgetter(1))[0]
        setattr(order, task_type + "_line", chosen_line)
        max_time[chosen_line] = getattr(order, task_type + "_start_time") + getattr(
            order, task_type + "_time"
        )
        orders_wiht_line.append(order)
    return tuple(orders_wiht_line)


def covered_time_steps(time_step: int, duration: Minutes) -> Tuple[int, ...]:
    return tuple(range(max(0, time_step - duration + STEP_SIZE), time_step + STEP_SIZE, STEP_SIZE))

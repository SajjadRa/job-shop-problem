import operator
import random
from typing import Mapping, Sequence, Tuple

from visualisation import plot_assigned_orders

from main import (NB_COOKING_LINES, NB_PREP_LINES, STEP_SIZE,
                  VEGETARIAN_IMPORTANCE_RATIO, Minutes, Order, Orders,
                  generate_orders)

# import gurobipy as grb

TIME_STEPS = Sequence[Minutes]


class Variables:
    max_end_time: grb.Var
    max_end_time_vegetarian: grb.Var
    prep_assignment: Mapping[Tuple[Order, Minutes], grb.Var]
    cooking_assignment: Mapping[Tuple[Order, Minutes], grb.Var]

    def __init__(self, model, assignment_options):
        self.max_end_time = model.addVar(
            vtype=grb.GRB.INTEGER,
            name="objective_function",
        )
        self.max_end_time_vegetarian = model.addVar(
            vtype=grb.GRB.INTEGER,
            name="objective_function",
        )
        self.prep_assignment = model.addVars(
            assignment_options, vtype=grb.GRB.BINARY, name="prep_assignment"
        )
        self.cooking_assignment = model.addVars(
            assignment_options,
            vtype=grb.GRB.BINARY,
            name="cooking_assignment",
        )


def mip_solver(number_of_orders: int, seed: float, plot: bool = True):
    random.seed(seed)
    orders = generate_orders(number_of_orders)
    horizon = sum(order.prep_time + order.cooking_time for order in orders)
    time_steps = tuple(range(0, horizon + STEP_SIZE, STEP_SIZE))

    assignment_options = tuple((order, t_step) for order in orders for t_step in time_steps)
    with grb.Env() as env_grb, grb.Model(env=env_grb) as jsp_model:
        jsp_model.modelSense = grb.GRB.MINIMIZE
        variables = Variables(jsp_model, assignment_options)

        # Constraints
        jsp_model.addConstrs(variables.prep_assignment.sum(order, "*") == 1 for order in orders)
        jsp_model.addConstrs(variables.cooking_assignment.sum(order, "*") == 1 for order in orders)
        add_prep_before_cooking_constraint(jsp_model, variables, orders, time_steps)
        add_overlap_constrains(jsp_model, variables, orders, time_steps)

        add_objective_function(jsp_model, variables, orders, time_steps)

        jsp_model.optimize()

        set_optimal_start_times(variables, orders, time_steps)

        orders = choose_line(NB_PREP_LINES, orders, "prep")
        orders = choose_line(NB_COOKING_LINES, orders, "cooking")

        last_meal_cooking_end_time = variables.max_end_time.X
        last_vegetarian_meal_cooking_end_time = variables.max_end_time_vegetarian.X

    print("Last meal cooking end time: " + str(last_meal_cooking_end_time))
    print("Last vegetarian meal cooking end time: " + str(last_vegetarian_meal_cooking_end_time))
    if plot:
        plot_assigned_orders(orders)

    return last_meal_cooking_end_time


def set_optimal_start_times(variables: Variables, orders: Orders, time_steps: TIME_STEPS):
    for order in orders:
        order.prep_start_time = int(
            sum(t_step * variables.prep_assignment[order, t_step].X for t_step in time_steps)
        )

        order.cooking_start_time = int(
            sum(t_step * variables.cooking_assignment[order, t_step].X for t_step in time_steps)
        )


def add_objective_function(
    model: grb.Model, variables: Variables, orders: Orders, time_steps: TIME_STEPS
):
    # objective function
    # main
    model.addConstrs(
        variables.max_end_time
        >= grb.quicksum(
            (t_step + order.cooking_time) * variables.cooking_assignment[order, t_step]
            for t_step in time_steps
        )
        for order in orders
    )
    # vegetarian objective function
    model.addConstrs(
        variables.max_end_time_vegetarian
        >= grb.quicksum(
            (t_step + order.cooking_time) * variables.cooking_assignment[order, t_step]
            for t_step in time_steps
        )
        for order in orders
        if order.vegetarian
    )
    # weighted sum
    model.setObjective(
        variables.max_end_time + VEGETARIAN_IMPORTANCE_RATIO * variables.max_end_time_vegetarian
    )


def add_overlap_constrains(
    model: grb.Model, variables: Variables, orders: Orders, time_steps: TIME_STEPS
):
    # overlap constraints
    model.addConstrs(
        grb.quicksum(
            grb.quicksum(
                variables.prep_assignment[order, t_step]
                for t_step in covered_time_steps(t_step, order.prep_time)
            )
            for order in orders
        )
        <= NB_PREP_LINES
        for t_step in time_steps
    )
    model.addConstrs(
        grb.quicksum(
            grb.quicksum(
                variables.cooking_assignment[order, t_step]
                for t_step in covered_time_steps(t_step, order.cooking_time)
            )
            for order in orders
        )
        <= NB_COOKING_LINES
        for t_step in time_steps
    )


def add_prep_before_cooking_constraint(
    model: grb.Model, variables: Variables, orders: Orders, time_steps
):
    exp_prep_end_time = {
        order: grb.quicksum(
            (t_step + order.prep_time) * variables.prep_assignment[order, t_step]
            for t_step in time_steps
        )
        for order in orders
    }
    exp_cooking_start_time = {
        order: grb.quicksum(
            t_step * variables.cooking_assignment[order, t_step] for t_step in time_steps
        )
        for order in orders
    }
    # perp before cooking
    model.addConstrs(
        (exp_prep_end_time[order] <= exp_cooking_start_time[order] for order in orders),
        name="prep_before_cooking",
    )


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


def covered_time_steps(time_step: Minutes, duration: Minutes) -> TIME_STEPS:
    return tuple(range(max(0, time_step - duration + STEP_SIZE), time_step + STEP_SIZE, STEP_SIZE))

from random import choice, randint
from typing import NewType, Sequence
from dataclasses import dataclass

Minutes = NewType("Minutes", int)

STEP_SIZE = 5
DURATIONS = list(range(5, 65, STEP_SIZE))
NUMBER_OF_ORDERS = 30
NB_PREP_LINES = 2
NB_COOKING_LINES = 2

VEGETARIAN_IMPORTANCE_RATIO = 0


@dataclass(frozen=False, repr=False)
class Order:
    id: int
    vegetarian: bool
    prep_time: Minutes
    cooking_time: Minutes
    prep_start_time: int
    prep_line: int
    cooking_start_time: int
    cooking_line: int

    def as_dict(self, task_type):
        return {
            "id": self.id,
            "start_time": getattr(self, task_type + "_start_time"),
            "end_time": getattr(self, task_type + "_start_time")
            + getattr(self, task_type + "_time"),
            "line": task_type + "_" + str(getattr(self, task_type + "_line")),
            "duration": getattr(self, task_type + "_time"),
            "meal_type": "vegetarian" if self.vegetarian else "normal",
        }

    def __repr__(self):
        return str(self.id)

    def __hash__(self):
        return hash(self.id)


Orders = Sequence[Order]


def create_random_order(order_id: int) -> Order:
    return Order(
        id=order_id,
        vegetarian=bool(randint(0, 1)),
        prep_time=choice(DURATIONS),
        cooking_time=choice(DURATIONS),
        prep_start_time=0,
        cooking_start_time=0,
        prep_line=0,
        cooking_line=0,
    )


def generate_orders(number_of_orders):
    orders = tuple(
        create_random_order(order_id) for order_id in range(1, number_of_orders + 1)
    )
    return orders

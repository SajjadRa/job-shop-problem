import time

import pandas as pd
from johnson import johnson_solver
from mip import mip_solver


def run_series(number_of_orders: int):
    all_results = list()
    for i in range(100):
        result = dict()
        start_time = time.time()
        johnson_endtime = johnson_solver(number_of_orders, i, plot=False)
        result["johnson_time"] = time.time() - start_time
        start_time = time.time()
        optimal_endtime = mip_solver(number_of_orders, i, plot=False)
        result["mip_time"] = time.time() - start_time
        result["optimality_gap"] = 100 * (johnson_endtime - optimal_endtime) / optimal_endtime
        result["optimal_endtime"] = optimal_endtime
        result["johnson_endtime"] = johnson_endtime
        all_results.append(result)
        pd.DataFrame(all_results).to_csv("all_jsp_results.csv")


SOLVERS = {"johnson": johnson_solver, "mip": mip_solver}
TO_PLOT = True
NUMBER_OF_ORDERS = 50
SEED = 0
RUN_IN_SERIES = False
if __name__ == "__main__":
    solver = SOLVERS["johnson"]
    start_time = time.time()
    if RUN_IN_SERIES:
        run_series(NUMBER_OF_ORDERS)
    else:
        solver(NUMBER_OF_ORDERS, SEED, TO_PLOT)

    print(time.time() - start_time)

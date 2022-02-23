import datetime

import pandas as pd
from plotly import express as px
from plotly.io import to_html


def plot_assigned_orders(orders):
    orders_df = pd.DataFrame(
        [order.as_dict("prep") for order in orders]
        + [order.as_dict("cooking") for order in orders]
    )
    orders_df["start_time"] = datetime.datetime(
        year=2021, month=1, day=1, hour=0
    ) + pd.to_timedelta(orders_df["start_time"], "m")
    orders_df["end_time"] = datetime.datetime(
        year=2021, month=1, day=1, hour=0
    ) + pd.to_timedelta(orders_df["end_time"], "m")
    fig = px.timeline(
        orders_df,
        x_start="start_time",
        x_end="end_time",
        y="line",
        text="id",
        color="meal_type",
        opacity=1,
    )
    fig.update_layout(
        font=dict(family="Courier New, monospace", size=12, color="RebeccaPurple")
    )
    fig.update_xaxes(
        tickformat="%H:%M",
        # range is 1 hour to 24 hours
    )

    with open("orders" + ".html", "w") as f:
        f.write(to_html(fig))

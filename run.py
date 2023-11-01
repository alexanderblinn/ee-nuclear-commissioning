# -*- coding: utf-8 -*-
"""
Created on Fri Apr 21 21:16:19 2023
"""

import locale
import os

import pandas as pd
import numpy as np
from plotly.subplots import make_subplots
import plotly.graph_objects as go


locale.setlocale(locale.LC_TIME, "us_US.UTF-8")


def calc_closing_age(row):
    """Calculate the closing age."""
    never_started_operation = row["Abschaltung"] == row["Bau/Projekt eingestellt"]
    age = pd.Timedelta(0) if never_started_operation else row["Abschaltung"] - row["Kommerzieller Betrieb"]
    return age.total_seconds() / 86400 / 365.25


def calc_construction_time(row):
    """Calculate the construction time."""
    never_started_operation = row["Abschaltung"] == row["Bau/Projekt eingestellt"]
    time = row["Abschaltung"] - row["Baubeginn"] if never_started_operation else row["Kommerzieller Betrieb"] - row["Baubeginn"]
    return time.total_seconds() / 86400 / 365.25


def calc_construction_aborted_time(row):
    """Calculate the construction time for aborted reactors."""
    is_aborted = pd.isnull(row["Abschaltung"]) and not pd.isnull(row["Baubeginn"]) and not pd.isnull(row["Bau/Projekt eingestellt"])
    if is_aborted and pd.notnull(row["Bau/Projekt eingestellt"]) and pd.notnull(row["Baubeginn"]):
        time = row["Bau/Projekt eingestellt"] - row["Baubeginn"]
        return time.total_seconds() / 86400 / 365.25
    else:
        return None



def read_data(file_path: str) -> None:
    """Read the excel data file and preprocesses it."""
    return pd.read_excel(
        file_path,
        converters={
            "Baubeginn": pd.to_datetime,
            "erste Netzsynchronisation": pd.to_datetime,
            "Kommerzieller Betrieb": pd.to_datetime,
            "Abschaltung": pd.to_datetime,
            "Bau/Projekt eingestellt": pd.to_datetime
            }
        )


# File path
FILE_NAME = "nuclear_power_plants.xlsx"
FILE_PATH = os.path.join(os.path.dirname(__file__), "data", FILE_NAME)

# Read and preprocess the data
df = read_data(FILE_PATH)

df["closing_age"] = df.apply(calc_closing_age, axis=1)
df["construction_time"] = df.apply(calc_construction_time, axis=1)
df["construction_aborted_time"] = df.apply(calc_construction_aborted_time, axis=1)

data_to_plot = "construction_aborted_time"

CONFIG = {
    "closing_age": {
        "bins": [0, 11, 21, 31, 41, np.inf],
        "labels": ['0 – 10 Years', '11 – 20 Years', '21 – 30 Years', '31 – 40 Years', '41 Years and Over']
        },
    "construction_time": {
        "bins": [0, 6, 11, 16, 21, np.inf],
        "labels": ['0 – 5 Years', '6 – 10 Years', '11 – 15 Years', '16 – 20 Years', '21 Years and Over']
        },
    "construction_aborted_time": {
        "bins": [0, 3, 6, 9, np.inf],
        "labels": ['0 – 2 Year', '3 – 5 Years', '6 – 8 Years', '9 and Over']
        },
    }

# Cut the data into bins
df['age_group'] = pd.cut(
    df[data_to_plot].round(0),
    bins=CONFIG[data_to_plot]["bins"],
    labels=CONFIG[data_to_plot]["labels"],
    right=False
    )

# Count the number of reactors in each age group
age_counts = df['age_group'].value_counts().sort_index()


fig = go.Figure()

start_angle = 0
for interval, count in zip(CONFIG[data_to_plot]["labels"], age_counts):
    proportion = count / age_counts.sum() * 180
    fig.add_barpolar(
        r=[1],  # fixed radius
        theta=[start_angle + proportion/2],
        width=[proportion],
        name=str(interval),
        marker=dict(
            color=f"rgba({np.random.randint(0, 256)}, {np.random.randint(0, 256)}, {np.random.randint(0, 256)}, 0.6)",
            line=dict(width=0)
        ),
    )

    fig.add_annotation(
        text=f"{count}",
        x=-0.35 * np.cos(np.radians(start_angle + proportion/2)) + 0.5,
        y=0.7 * np.sin(np.radians(start_angle + proportion/2)),
        showarrow=False,
        font=dict(
            size=14,
            color="black"
        ),
        xref="paper",  # 'paper' reference frame
        yref="paper",  # 'paper' reference frame
        textangle=0
    )

    start_angle += proportion


fig.add_annotation(
    text=f"<b>{age_counts.sum()} Reactor Units</b><br>Mean Age<br><b>{df[data_to_plot].mean():.1f} Years</b>",
    x=0.5,
    y=0,
    xref="paper",
    yref="paper",
    xanchor="center",  # Anchor point for x (left, center, or right)
    yanchor="bottom",  # Anchor point for y (top, middle, or bottom)
    showarrow=False,
    align="center",
    font=dict(size=16),
)


fig.update_layout(
    title=f"Evolution of Nuclear Power Plants in Europe<br>{data_to_plot}",
    plot_bgcolor="rgba(0, 0, 0, 0)",
    paper_bgcolor="rgba(0, 0, 0, 0)",
    hoverlabel=dict(font=dict(size=12)),
    font=dict(family="sans-serif", color="black", size=12),  # global font settings
    width=997,
    height=580,
    polar=dict(
        hole=0.3,
        sector=[0, 180],
        radialaxis=dict(
            visible=False,
            range=[0, 1],
            showticklabels=False,  # remove radial axis labels
        ),
        angularaxis=dict(
            showgrid=False,
            direction="clockwise",
            rotation=180,
            showticklabels=False,  # remove angular axis labels
        ),
        bargap=0,
    ),
    showlegend=True,
    legend=dict(
        orientation="h",
        yanchor="top",
        y=-0.1,
        xanchor="center",
        x=0.5,
        traceorder="normal",
        tracegroupgap=20,
        # font=dict(size=10),
        itemwidth=60
    ),
)



# Save the plot as an HTML file
fig.write_html("index.html")

# Show the figure
fig.show()


# -*- coding: utf-8 -*-
"""
Created on Fri Apr 21 21:16:19 2023
"""
from datetime import datetime
import locale
import math
import os

import pandas as pd
import numpy as np
from numpy.typing import ArrayLike
import plotly.graph_objects as go

locale.setlocale(locale.LC_TIME, "us_US.UTF-8")

# Constants
YEAR_START = 1990
YEAR_END = 2023

# Define a dictionary of colors for each country
COUNTRY_COLORS = {
    "Belarus": "#0072b1",
    "Belgium": "#e6a000",
    "Bulgaria": "#009e73",
    "Czech Republic": "#c4022b",
    "Finland": "#9300d3",
    "France": "#000000",
    "Germany": "#d45e00",
    "Italy": "#2e4053",
    "Lithuania": "#FA8072",
    "Netherlands": "#9e9e00",
    "Romania": "#a65959",
    "Slovakia": "#36648B",
    "Spain": "#c0c0c0",
    "Sweden": "#2ca02c",
    "Switzerland": "#a172de",
    "Ukraine": "#800080",
    "United Kingdom": "#ff0000"
}


# Some helper functions.
def cal_operational_time(row):
    """Calculate the operational time."""
    if row["Status"] == "In Betrieb":
        return (
            datetime(2023, 4, 25) - row["Kommerzieller Betrieb"]
            ).total_seconds() / 86400 / 365.25
    if row["Status"] == "Stillgelegt":
        return (
            row["Abschaltung"] - row["Kommerzieller Betrieb"]
            ).total_seconds() / 86400 / 365.25


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


def process_data(df: pd.DataFrame) -> pd.DataFrame:
    """Compute additional values."""
    df["Bauzeit"] = (df["Kommerzieller Betrieb"] - df["Baubeginn"]).apply(
        lambda x: x.total_seconds()) / 86400 / 365.25
    df["Betriebszeit"] = df.apply(cal_operational_time, axis=1)
    return df


def select_data(df: pd.DataFrame, start: int, end: int) -> pd.DataFrame:
    """Select data within start and end year."""
    # Drop reactors that never operated.
    df = df[df["Status"].isin(["In Betrieb", "Stillgelegt"])].dropna(subset=["Betriebszeit"])
    return df.loc[
        (df["Status"] == "In Betrieb")
        &
        (df["Kommerzieller Betrieb"] >= datetime(YEAR_START, 1, 1))
        &
        (df["Kommerzieller Betrieb"] <= datetime(YEAR_END, 12, 31))
        |
        (df["Abschaltung"] >= datetime(YEAR_START, 1, 1))
        &
        (df["Abschaltung"] <= datetime(YEAR_END, 12, 31)), :].copy()


def calc_bubble_size(array: ArrayLike) -> ArrayLike:
    """Calculate the size of the bubbles."""
    array_log = np.log10(array)
    return (array_log - array_log.min()) / (array_log.max() - array_log.min())


# File path
FILE_NAME = "nuclear_power_plants.xlsx"
FILE_PATH = os.path.join(os.path.dirname(__file__), "data", FILE_NAME)

# Read and preprocess the data
df = read_data(FILE_PATH)
df = process_data(df)

# Select data within start and end year
data = select_data(df, YEAR_START, YEAR_END)

# Add color code for every country
data["color"] = data["Land"].map(COUNTRY_COLORS)

# Calculate and scale the size of the bubbles
data["size"] = 5 + calc_bubble_size(data["Leistung, Netto in MW"]) * (25 - 5)

# Create a Plotly Figure
fig = go.Figure()

# Add horizontal line
fig.add_trace(
    go.Scatter(
        x=[datetime(YEAR_START, 1, 1), datetime(YEAR_END, 12, 31)],
        y=[0, 0],
        mode="lines",
        line=dict(color="black", width=1),
        showlegend=False,
        stackgroup="below"
        )
    )

# Create a list of unique countries
countries = data["Land"].unique()

# Iterate through the countries, creating separate traces for each.
for country in countries:

    country_data = data.loc[
        (data["Status"] == "In Betrieb") & (data["Land"] == country)
        ]

    if not country_data.empty:

        x1 = country_data["Kommerzieller Betrieb"]
        y1 = country_data["Betriebszeit"]
        s1 = country_data["size"]
        c1 = country_data["color"]

        # Land
        t1 = country_data["Land"]
        t1 += "<br>"
        # Name und Block
        t1 += country_data["Name"]
        t1 += ", Unit "
        t1 += country_data["Block"].apply(str)
        t1 += "<br>"
        # Inbetriebnahme
        t1 += "Commissioning: "
        t1 += country_data["Kommerzieller Betrieb"].apply(lambda x: x.strftime("%B %Y"))
        t1 += "<br>"
        # Alter
        t1 += "Current Age: "
        t1 += country_data["Betriebszeit"].round(1).apply(str)
        t1 += " Years"
        t1 += "<br>"
        # Bauzeit
        t1 += "Construction Time: "
        t1 += country_data["Bauzeit"].round(1).apply(str)
        t1 += " Years"
        t1 += "<br>"
        # Leistung
        t1 += "Net Capacity: "
        t1 += country_data["Leistung, Netto in MW"].apply(str)
        t1 += " MW"

        fig.add_trace(
            go.Scatter(
                x=x1,
                y=y1,
                mode="markers",
                marker=dict(size=s1,
                            color=c1,
                            colorscale="Viridis",
                            showscale=False),
                text=t1,
                hovertemplate="%{text}<extra></extra>",
                name=country,
                legendgroup=country,
                showlegend=False
            )
        )

    country_data = data.loc[
        (data["Status"] == "Stillgelegt") & (data["Land"] == country)
        ]

    if not country_data.empty:

        x2 = country_data["Abschaltung"]
        y2 = country_data["Betriebszeit"]
        s2 = country_data["size"]
        c2 = country_data["color"]

        # Land
        t2 = country_data["Land"]
        t2 += "<br>"
        # Name und Block
        t2 += country_data["Name"]
        t2 += ", Unit "
        t2 += country_data["Block"].apply(str)
        t2 += "<br>"
        # Inbetriebnahme
        t2 += "Decommissioning: "
        t2 += country_data["Abschaltung"].apply(lambda x: x.strftime("%B %Y"))
        t2 += "<br>"
        # Alter
        t2 += "Age at Decommissioning: "
        t2 += country_data["Betriebszeit"].round(1).apply(str)
        t2 += " Years"
        t2 += "<br>"
        # Bauzeit
        t2 += "Construction Time: "
        t2 += country_data["Bauzeit"].round(1).apply(str)
        t2 += " Years"
        t2 += "<br>"
        # Leistung
        t2 += "Net Capacity: "
        t2 += country_data["Leistung, Netto in MW"].apply(str)
        t2 += " MW"

        fig.add_trace(
            go.Scatter(
                x=x2,
                y=-y2,
                mode="markers",
                marker=dict(size=s2,
                            color=c2,
                            colorscale="Viridis",
                            showscale=False),
                text=t2,
                hovertemplate="%{text}<extra></extra>",
                name=country,
                legendgroup=country,
                showlegend=False,
            )
        )

# Custom legend
for country, color in COUNTRY_COLORS.items():
    fig.add_trace(
        go.Scatter(
            x=[None, None],
            y=[None, None],
            mode="markers",
            marker=dict(size=12, color=color),
            name=country,
            legendgroup=country,
            showlegend=True,
            hoverinfo="none"
        )
    )

# Compute the regression line
x_values = [date.toordinal() for date in data.loc[data["Status"] == "Stillgelegt", "Abschaltung"]]
y_values = data.loc[data["Status"] == "Stillgelegt", "Betriebszeit"]
regress_coeffs = np.polyfit(x_values, -y_values, deg=1)

# Plot the regression line
regress_x = np.array([min(x_values), max(x_values)])
regress_y = np.polyval(regress_coeffs, regress_x)

# Add regression line for in-operation reactors
fig.add_trace(
    go.Scatter(
        x=[datetime.fromordinal(d) for d in regress_x],
        y=regress_y,
        mode="lines",
        line=dict(color="black", dash="dash", width=2),
        name="Regressionslinie",
        showlegend=False
        )
    )

# Determine the axis limits
x_min = datetime(YEAR_START - 1, 1, 1)
x_max = datetime(YEAR_END + 1, 12, 31)
y_min = -math.ceil(data.loc[data["Status"] == "Stillgelegt", "Betriebszeit"].max() / 10) * 10
y_max = math.ceil(data.loc[data["Status"] == "In Betrieb", "Betriebszeit"].max() / 10) * 10

# Apply the fixed axis ranges
fig.update_xaxes(range=[x_min, x_max])
fig.update_yaxes(range=[y_min, y_max])

fig.add_annotation(
    text="Commissioning<br>Decommissioning",
    x=datetime(YEAR_START, 1, 1),
    y=0,
    xref="x",
    yref="y",
    xanchor="left",  # Anchor point for x (left, center, or right)
    yanchor="middle",  # Anchor point for y (top, middle, or bottom)
    showarrow=False,
    align="left"
)


fig.add_annotation(
    go.layout.Annotation(
        text="The average age of nuclear reactors<br>at the time of decommissioning has<br>significantly increased.",
        xref="x",
        yref="y",
        x=datetime(2018, 6, 1),
        y=-40,
        font=dict(size=12, color="black"),
        bordercolor="black",
        borderwidth=1,
        bgcolor="white",
        opacity=0.8,
        align="center",
        showarrow=True,
        arrowhead=2,
        arrowsize=1,
        arrowwidth=2,
        arrowcolor="black",
        xanchor="center",  # x-anchor for the arrow
        yanchor="bottom",  # y-anchor for the arrow
        axref="x",
        ayref="y",
        ax=datetime(2020, 1, 1),  # x-offset for the arrow
        ay=-20  # y-offset for the arrow
    )
)


fig.update_layout(
    title="Evolution of Nuclear Power Plants in Europe since 1990:<br>Commissioning and Decommissioning of Reactors",
    xaxis_title="Year of Commissioning or Decommissioning",
    yaxis_title="Current Operational Age or Age at Decommissioning",
    xaxis=dict(showgrid=True, gridwidth=1, gridcolor="rgba(128, 128, 128, 0.1)"),
    yaxis=dict(showgrid=True, gridwidth=1, gridcolor="rgba(128, 128, 128, 0.1)"),
    plot_bgcolor="rgba(0, 0, 0, 0)",
    paper_bgcolor="rgba(0, 0, 0, 0)",
    # hovermode="x unified",
    hoverlabel=dict(font=dict(size=12)),
    font=dict(family="Roboto", color="black", size=12),  # global font settings
    width=997,
    height=580,
    legend=dict(tracegroupgap=4),
)


# Save the plot as an HTML file
fig.write_html("index.html")

# Display the plot
fig.show()

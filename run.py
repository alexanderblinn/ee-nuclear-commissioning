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
YEAR_START = 1968
YEAR_END = 2023

# Define a dictionary of colors for each country
COUNTRY_COLORS = {
    "Austria": "#FF00FF",
    "Belarus": "#0072b1",
    "Belgium": "#e6a000",
    "Bulgaria": "#009e73",
    "Czech Republic": "#c4022b",
    "Finland": "#9300d3",
    "France": "#000000",
    "Germany": "#d45e00",
    "Hungary": "#FFD700",
    "Italy": "#2e4053",
    "Lithuania": "#FA8072",
    "Netherlands": "#9e9e00",
    "Romania": "#a65959",
    "Slovakia": "#36648B",
    "Slovenia": "#7DF9FF",
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
    df.loc[
        (df["Status"] == "Stillgelegt") & (pd.isna(df["Kommerzieller Betrieb"])), "Betriebszeit"] = 0
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
data["size"] = 10 + calc_bubble_size(data["Leistung, Netto in MW"]) * 10

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

# Add rectangle
year_rec = 2007
num_up = data.loc[data["Kommerzieller Betrieb"] >= datetime(year_rec, 1, 1), :].shape[0]
num_down = data.loc[data["Abschaltung"] >= datetime(year_rec, 1, 1), :].shape[0]

msg = """
Over the course of the last 15 years, the<br>
European nuclear energy landscape underwent a<br>
significant transformation. During the years,<br>
a mere four new reactors commenced operation,<br>
while a striking number of 42 reactors were<br>
decommissioned across the continent.<br>
Meanwhile, the average age of decommissioned<br>
reactors has surpassed the global average of<br>
27 years, with a continuing upward trend.<br>
"""

fig.add_vrect(
    x0=datetime(2007, 1, 1),
    x1=datetime(YEAR_END, 12, 31),
    annotation_text=msg,
    annotation_position="top left",
    annotation_align="left",
    annotation={
        "font": {"size": 11}
        },
    fillcolor="black",
    opacity=0.1,
    line_width=0
    )

fig.add_vline(
    x=datetime(2007, 1, 1),
    line_width=1, line_dash="dash", line_color="black"
    )

# %%

# Define nuclear catastrophes.
NUCLEAR_CATASTROPHES = {
    "Windscale/Sellafield Accident": {
        "country": "United Kingdom",
        "INES": "4",
        "date": datetime(1973, 1, 1),
    },
    "Leningrad 1st Accident": {
        "country": "Soviet Union",
        "INES": "4-5",
        "date": datetime(1974, 4, 6),
    },
    "Leningrad 2nd Accident": {
        "country": "Soviet Union",
        "INES": "4-5",
        "date": datetime(1975, 10, 1),
    },
    "Beloyarsk 1st Accident": {
        "country": "Soviet Union",
        "INES": "5",
        "date": datetime(1977, 1, 1),
    },
    "Jaslovské Bohunice Accident": {
        "country": "Czechoslovakia",
        "INES": "4",
        "date": datetime(1977, 2, 1),
    },
    "Beloyarsk 2nd Accident": {
        "country": "Soviet Union",
        "INES": "3-4",
        "date": datetime(1978, 12, 31),
    },
    "Three Mile Island Accident": {
        "country": "United States",
        "INES": "5",
        "date": datetime(1979, 3, 28),
    },
    "Saint-Laurent Accident": {
        "country": "France",
        "INES": "4",
        "date": datetime(1980, 1, 1),
    },
    "Tschernobyl Accident": {
        "country": "Soviet Union",
        "INES": "5",
        "date": datetime(1982, 9, 1),
    },
    "Buenos Aires Accident": {
        "country": "Argentina",
        "INES": "4",
        "date": datetime(1983, 1, 1),
    },
    "Wladiwostok Accident": {
        "country": "Soviet Union",
        "INES": "5",
        "date": datetime(1985, 8, 10),
    },
    "Gore Accident": {
        "country": "United States",
        "INES": "2-4",
        "date": datetime(1986, 1, 6),
    },
    "Tschernobyl Disaster": {
        "country": "Soviet Union",
        "INES": "7",
        "date": datetime(1986, 4, 26),
    },
    "Sewersk Accident": {
        "country": "Russia",
        "INES": "2-4",
        "date": datetime(1993, 4, 6),
    },
    "Tōkai-mura Accident": {
        "country": "Japan",
        "INES": "4-5",
        "date": datetime(1999, 9, 30),
    },
    "Fleurus Accident": {
        "country": "Belgium",
        "INES": "4",
        "date": datetime(2006, 3, 11),
    },
    "Fukushima Disaster": {
        "country": "Japan",
        "INES": "7",
        "date": datetime(2011, 3, 11),
    },
}

# Loop through the NUCLEAR_CATASTROPHES dictionary
for catastrophe_name, catastrophe_data in NUCLEAR_CATASTROPHES.items():
    catastrophe_date = catastrophe_data["date"]
    catastrophe_country = catastrophe_data["country"]
    catastrophe_year = catastrophe_data["date"].year
    catastrophe_ines = catastrophe_data["INES"]

    catastrophe_text = f"{catastrophe_name}, {catastrophe_country} ({catastrophe_year}, INES: {catastrophe_ines})"

    # Add a vertical line
    fig.add_shape(
        type="line",
        x0=catastrophe_date,
        x1=catastrophe_date,
        y0=1,
        y1=-1,
        yref="y",
        xref="x",
        line=dict(color="black", width=1, dash="solid"),
    )

    # Add a hover text annotation
    fig.add_trace(
        go.Scatter(
            x=[catastrophe_date],
            y=[0],
            mode="markers",
            marker=dict(size=0, opacity=0, color="white"),
            text=[catastrophe_text],
            hovertemplate="%{text}<extra></extra>",
            showlegend=False,
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
        t1 += "Construction to Operation Time: "  # "Construction Time: "
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
        t2 += "Operating Time at Decommissioning: "
        t2 += country_data["Betriebszeit"].round(1).apply(str)
        t2 += " Years"
        t2 += "<br>"
        # Bauzeit
        t2 += "Construction to Operation Time: "  # "Construction Time: "
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

for country in countries:
    fig.add_trace(
        go.Scatter(
            x=[None, None],
            y=[None, None],
            mode="markers",
            marker=dict(size=12, color=COUNTRY_COLORS[country]),
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
    text=f"Commissioning{14*'<br>'}Decommissioning",
    x=datetime(YEAR_START+1, 1, 1),
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


oldest_year = min(
    df.loc[df["Status"]=="In Betrieb", "Kommerzieller Betrieb"].min().year,
    df.loc[df["Status"]=="Stillgelegt", "Abschaltung"].min().year
    )

add_txt = f" since {YEAR_START}" if YEAR_START > oldest_year else ""
fig.update_layout(
    title=f"Evolution of Nuclear Power Plants in Europe{add_txt}:<br>Commissioning and Decommissioning of Reactors",
    xaxis_title="Year of Commissioning or Decommissioning",
    yaxis_title="Current Operational Age or Age at Decommissioning",
    xaxis=dict(showgrid=True, gridwidth=1, gridcolor="rgba(128, 128, 128, 0.1)"),
    yaxis=dict(showgrid=True, gridwidth=1, gridcolor="rgba(128, 128, 128, 0.1)"),
    plot_bgcolor="rgba(0, 0, 0, 0)",
    paper_bgcolor="rgba(0, 0, 0, 0)",
    # hovermode="x unified",
    hoverlabel=dict(font=dict(size=12)),
    font=dict(family="Times New Roman", color="black", size=12),  # global font settings
    width=997,
    height=580,
    legend=dict(tracegroupgap=.5),
)


# %%

# # Add a slider
# slider_steps = []
# for i in range(YEAR_START, YEAR_END+1):
#     step = dict(
#         method="restyle",
#         args=[
#             {"x": [
#                 data.loc[(data["Status"]=="In Betrieb") & (data["Land"]==country) & (data["Kommerzieller Betrieb"] >= datetime(i, 1, 1)) & (data["Kommerzieller Betrieb"] <= datetime(YEAR_END, 12, 31)), "Kommerzieller Betrieb"]
#                 if country in countries else None
#                 for country in countries
#             ] + [
#                 data.loc[(data["Status"]=="Stillgelegt") & (data["Land"]==country) & (data["Abschaltung"] >= datetime(i, 1, 1)) & (data["Abschaltung"] <= datetime(YEAR_END, 12, 31)), "Abschaltung"]
#                 if country in countries else None
#                 for country in countries
#             ]}
#         ],
#         label=str(i),
#     )
#     slider_steps.append(step)
# sliders = [dict(
#     active=0,
#     currentvalue={"prefix": "Year: "},
#     pad={"t": 50},
#     steps=slider_steps
# )]
# fig.update_layout(sliders=sliders)




# %%




# Save the plot as an HTML file
fig.write_html("index.html")

# Display the plot
fig.show()

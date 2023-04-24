# -*- coding: utf-8 -*-
"""
Created on Sun Apr 23 15:34:10 2023

@author: Alexander Blinn
"""

import dash
from dash import dcc
from dash import html
from dash.dependencies import Input, Output

from datetime import datetime
import math
import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import plotly.graph_objects as go


ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), 'config'))
plt.style.use(os.path.join(ROOT, 'mplstyle-ibt'))

# %%

YEAR_START = 1980
YEAR_END = 2023

# %%

# Define a list of colors
COUNTRY_COLORS = {
    "Belarus": "#0072b1",
    "Belgien": "#e6a000",
    "Bulgarien": "#009e73",
    "Deutschland": "#d45e00",
    "Finnland": "#9300d3",
    "Frankreich": "#fac200",
    "Italien": "#5c5c5c",
    "Litauen": "#e63227",
    "Niederlande": "#9e9e00",
    "Österreich": "#00bcd4",
    "Polen": "#e68200",
    "Rumänien": "#6b6b6b",
    "Schweden": "#2ca02c",
    "Schweiz": "#a172de",
    "Slowakei": "#ff9900",
    "Slowenien": "#008080",
    "Spanien": "#c0c0c0",
    "Tschechien": "#c4022b",
    "Türkei": "#4b0082",
    "Ukraine": "#800080",
    "Ungarn": "#0000ff",
    "Verinigtes Königreich": "#ff0000"
}

def calculate_operational_time(row):
    if row["Status"] == "In Betrieb":
        return (datetime.now() - row["Kommerzieller Betrieb (geplant)"]).total_seconds() / 86400 / 365.25
    else:
        try:
            return (row["Abschaltung (geplant)"] - row["Kommerzieller Betrieb (geplant)"]).total_seconds() / 86400 / 365.25
        except:
            return None

# %%

df = pd.read_excel("nuclear_power_plants.xlsx")

df["Jahr_Baubeginn"] = df["Baubeginn"].apply(
    lambda x: x.year if isinstance(x, datetime) else None
    )

df["Jahr_Inbetriebnahme"] = df["Kommerzieller Betrieb (geplant)"].apply(
    lambda x: x.year if isinstance(x, datetime) else None
    )

df["Jahr_Abschaltung"] = df["Abschaltung (geplant)"].apply(
    lambda x: x.year if isinstance(x, datetime) else None
    )

df["Bauzeit"] = df["Jahr_Inbetriebnahme"] - df["Jahr_Baubeginn"]


df["Betriebszeit"] = df.apply(calculate_operational_time, axis=1)

# Apply the function to the 'Land' column and create a new 'color' column
df["color"] = df["Land"].apply(lambda country: COUNTRY_COLORS.get(country))


data = df.loc[
    (df["Status"] == "In Betrieb") & (df["Jahr_Inbetriebnahme"] >= YEAR_START) & (df["Jahr_Inbetriebnahme"] <= YEAR_END)
    |
    (df["Jahr_Abschaltung"] >= YEAR_START) & (df["Jahr_Abschaltung"] <= YEAR_END)
    , :]


#%%

fig = go.Figure()

# Add horizontal line
fig.add_shape(
    type='line',
    x0=datetime(YEAR_START, 1, 1),
    x1=datetime(YEAR_END, 12, 31),
    y0=0,
    y1=0,
    yref="y",
    xref="x",
    line=dict(color="black", width=1)
)

# %%


# Create a list of unique countries
countries = data["Land"].unique()

# Iterate through the countries, creating separate traces for each.
# Unforunaley that is necessary for the legend to work as expected.
for country in countries:
    # In-operation reactors for the current country
    country_data = data.loc[(data["Status"]=="In Betrieb") & (data["Land"]==country)]

    x1 = country_data["Kommerzieller Betrieb (geplant)"]
    y1 = country_data["Betriebszeit"]
    s1 = country_data["Leistung, Netto in MW"] / country_data["Leistung, Netto in MW"].max()
    c1 = country_data["color"]

    t1 = country_data["Land"]
    t1 += "<br>"
    t1 += country_data["Name"]
    t1 += ", Block "
    t1 += country_data["Block"].apply(str)

    fig.add_trace(
        go.Scatter(
            x=x1,
            y=y1,
            mode="markers",
            marker=dict(size=50 * s1,
                        color=c1,
                        colorscale="Viridis",
                        showscale=False),
            text=t1,
            hovertemplate="%{text}<br>Inbetriebnahme: %{x}<br>Alter: %{y:.2f} Jahre<extra></extra>",
            name=country,
            legendgroup=country,
            showlegend=True
        )
    )

    # Shut down reactors for the current country
    country_data = data.loc[(data["Status"]=="Stillgelegt") & (data["Land"]==country)]

    x2 = country_data["Abschaltung (geplant)"]
    y2 = country_data["Betriebszeit"]
    s2 = country_data["Leistung, Netto in MW"] / country_data["Leistung, Netto in MW"].max()
    c2 = country_data["color"]

    t2 = country_data["Land"]
    t2 += "<br>"
    t2 += country_data["Name"]
    t2 += ", Block "
    t2 += country_data["Block"].apply(str)

    # Check if there are no in-operation reactors for the current country
    no_in_operation_reactors = len(data.loc[(data["Status"]=="In Betrieb") & (data["Land"]==country)]) == 0

    fig.add_trace(
        go.Scatter(
            x=x2,
            y=-y2,
            mode="markers",
            marker=dict(size=50 * s2,
                        color=c2,
                        colorscale="Viridis",
                        showscale=False),
            text=t2,
            hovertemplate="%{text}<br>Abschaltung: %{x}<br>Alter: %{y:.2f} Jahre<extra></extra>",
            name=country,
            legendgroup=country,
            showlegend=no_in_operation_reactors  # Show legend if there are no in-operation reactors for the current country
        )
    )



# %%



# %%

fig.update_layout(
    title="Entwicklung der Atomkraftwerke in Europa seit 1990:<br>Inbetriebnahme und Stilllegung von Reaktoren",
    xaxis_title="Jahr der Inbetriebnahme bzw. der Abschaltung",
    yaxis_title="derzeitiges Betriebsalter bzw. Alter bei Abschaltung",
    xaxis=dict(showgrid=True, gridwidth=1, gridcolor='rgba(128, 128, 128, 0.1)'),
    yaxis=dict(showgrid=True, gridwidth=1, gridcolor='rgba(128, 128, 128, 0.1)'),
    plot_bgcolor='rgba(0, 0, 0, 0)',
    paper_bgcolor='rgba(0, 0, 0, 0)',
    # hovermode='x unified',
    hoverlabel=dict(font=dict(size=16)),
    font=dict(size=14),
    height=800,  # Set the height of the plot
    width=1500,  # Set the width of the plot
                  )



# %%

import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output

app = dash.Dash(__name__)

# Create the layout of the Dash application
app.layout = html.Div([
    dcc.Graph(id='graph'),
    html.Div([
        html.Label('Year Range:'),
        dcc.RangeSlider(
            id='year-slider',
            min=YEAR_START,
            max=YEAR_END,
            step=1,
            value=[YEAR_START, YEAR_END],
            marks={i: str(i) for i in range(YEAR_START, YEAR_END+1, 5)}
        ),
    ], style={'width': '90%', 'margin': 'auto'})
])

# Update the plot based on the slider input
@app.callback(
    Output('graph', 'figure'),
    [Input('year-slider', 'value')]
)
def update_figure(year_range):
    start_year, end_year = year_range

    # Filter the data based on the selected year range
    filtered_data = data.loc[
        (
            (data["Status"] == "In Betrieb") & (data["Jahr_Inbetriebnahme"] >= start_year) & (data["Jahr_Inbetriebnahme"] <= end_year)
        ) | (
            data["Status"] == "Stillgelegt") & (data["Jahr_Abschaltung"] >= start_year) & (data["Jahr_Abschaltung"] <= end_year)
    ]

    # Create an empty figure
    filtered_fig = go.Figure()

    # Iterate through the countries, creating separate traces for each.
    for country in countries:
        # In-operation reactors for the current country
        country_data = filtered_data.loc[(filtered_data["Status"]=="In Betrieb") & (filtered_data["Land"]==country)]

        x1 = country_data["Kommerzieller Betrieb (geplant)"]
        y1 = country_data["Betriebszeit"]
        s1 = country_data["Leistung, Netto in MW"] / country_data["Leistung, Netto in MW"].max()
        c1 = country_data["color"]

        t1 = country_data["Land"]
        t1 += "<br>"
        t1 += country_data["Name"]
        t1 += ", Block "
        t1 += country_data["Block"].apply(str)

        filtered_fig.add_trace(
            go.Scatter(
                x=x1,
                y=y1,
                mode="markers",
                marker=dict(size=50 * s1,
                            color=c1,
                            colorscale="Viridis",
                            showscale=False),
                text=t1,
                hovertemplate="%{text}<br>Inbetriebnahme: %{x}<br>Alter: %{y:.2f} Jahre<extra></extra>",
                name=country,
                legendgroup=country,
                showlegend=True
            )
        )

        # Shut down reactors for the current country
        country_data = filtered_data.loc[(filtered_data["Status"]=="Stillgelegt") & (filtered_data["Land"]==country)]

        x2 = country_data["Abschaltung (geplant)"]
        y2 = country_data["Betriebszeit"]
        s2 = country_data["Leistung, Netto in MW"] / country_data["Leistung, Netto in MW"].max()
        c2 = country_data["color"]

        t2 = country_data["Land"]
        t2 += "<br>"
        t2 += country_data["Name"]
        t2 += ", Block "
        t2 += country_data["Block"].apply(str)

        # Check if there are no in-operation reactors for the current country
        no_in_operation_reactors = len(filtered_data.loc[(filtered_data["Status"]=="In Betrieb") & (filtered_data["Land"]==country)]) == 0

        filtered_fig.add_trace(
            go.Scatter(
                x=x2,
                y=-y2,
                mode="markers",
                marker=dict(size=50 * s2,
                            color=c2,
                            colorscale="Viridis",
                            showscale=False),
                text=t2,
                hovertemplate="%{text}<br>Abschaltung: %{x}<br>Alter: %{y:.2f} Jahre<extra></extra>",
                name=country,
                legendgroup=country,
                showlegend=no_in_operation_reactors  # Show legend if there are no in-operation reactors for the current country
            )
        )

    # Apply the layout from the original figure
    filtered_fig.update_layout(fig.layout)

    # Update the x-axis range based on the selected year range
    x_min = datetime(start_year, 1, 1)
    x_max = datetime(end_year, 12, 31)
    filtered_fig.update_xaxes(range=[x_min, x_max])

    return filtered_fig



if __name__ == '__main__':
    app.run_server(debug=True)

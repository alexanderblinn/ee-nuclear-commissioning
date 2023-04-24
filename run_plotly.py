# -*- coding: utf-8 -*-
"""
Created on Fri Apr 21 21:16:19 2023

@author: Alexander Blinn
"""
from datetime import datetime
import math
import os
import locale
locale.setlocale(locale.LC_TIME, "de_DE.UTF-8")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import plotly.graph_objects as go

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), 'config'))
plt.style.use(os.path.join(ROOT, 'mplstyle-ibt'))

# %%

YEAR_START = 1990
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


data = df.loc[
    (df["Status"] == "In Betrieb") & (df["Jahr_Inbetriebnahme"] >= YEAR_START) & (df["Jahr_Inbetriebnahme"] <= YEAR_END)
    |
    (df["Jahr_Abschaltung"] >= YEAR_START) & (df["Jahr_Abschaltung"] <= YEAR_END)
    , :].copy()

# Colors
data["color"] = data["Land"].map(COUNTRY_COLORS)

# size

# Calculate the log values
_log_values = np.log10(data["Leistung, Netto in MW"])

# Normalize the log values to a range of 0 to 1
_log_values_norm = (_log_values - _log_values.min()) / (_log_values.max() - _log_values.min())

# Scale the normalized values to the desired range.
data["size"] = 10 + _log_values_norm * (50 - 10)

# data["size"].sort_values().reset_index(drop=True).plot(marker="o")

#%%

fig = go.Figure()

# Add horizontal line
fig.add_shape(
    type="line",
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

MAX_POWER = data["Leistung, Netto in MW"].max()

# Iterate through the countries, creating separate traces for each.
# Unforunaley that is necessary for the legend to work as expected.
for country in countries:
    # In-operation reactors for the current country
    country_data = data.loc[(data["Status"]=="In Betrieb") & (data["Land"]==country)]

    x1 = country_data["Kommerzieller Betrieb (geplant)"]
    y1 = country_data["Betriebszeit"]
    s1 = country_data["size"]
    c1 = country_data["color"]

    # Land
    t1 = country_data["Land"]
    t1 += "<br>"
    # Name und Block
    t1 += country_data["Name"]
    t1 += ", Block "
    t1 += country_data["Block"].apply(str)
    t1 += "<br>"
    # Inbetriebnahme
    t1 += "Inbetriebnahme: "
    t1 += country_data["Kommerzieller Betrieb (geplant)"].apply(lambda x: x.strftime("%B %Y"))
    t1 += "<br>"
    # Alter
    t1 += "derzeitiges Alter: "
    t1 += country_data["Betriebszeit"].round(2).apply(str)
    t1 += " Jahre"
    t1 += "<br>"
    # Leistung
    t1 += "Nettoleistung: "
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
            showlegend=True
        )
    )

    # Shut down reactors for the current country
    country_data = data.loc[(data["Status"]=="Stillgelegt") & (data["Land"]==country)]

    x2 = country_data["Abschaltung (geplant)"]
    y2 = country_data["Betriebszeit"]
    s2 = country_data["size"]
    c2 = country_data["color"]

    # Land
    t2 = country_data["Land"]
    t2 += "<br>"
    # Name und Block
    t2 += country_data["Name"]
    t2 += ", Block "
    t2 += country_data["Block"].apply(str)
    t2 += "<br>"
    # Inbetriebnahme
    t2 += "Abschaltung: "
    t2 += country_data["Abschaltung (geplant)"].apply(lambda x: x.strftime("%B %Y"))
    t2 += "<br>"
    # Alter
    t2 += "Alter bei Abschaltung: "
    t2 += country_data["Betriebszeit"].round(2).apply(str)
    t2 += " Jahre"
    t2 += "<br>"
    # Leistung
    t2 += "Nettoleistung: "
    t2 += country_data["Leistung, Netto in MW"].apply(str)
    t2 += " MW"

    # Check if there are no in-operation reactors for the current country
    no_in_operation_reactors = len(data.loc[(data["Status"]=="In Betrieb") & (data["Land"]==country)]) == 0

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
            showlegend=no_in_operation_reactors  # Show legend if there are no in-operation reactors for the current country
        )
    )



# %%

# Compute the regression line
x_values = [date.toordinal() for date in data.loc[data["Status"]=="Stillgelegt", "Abschaltung (geplant)"]]
y_values = data.loc[data["Status"]=="Stillgelegt", "Betriebszeit"]
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
    font=dict(size=14)
                  )


# %%

# Determine the axis limits
x_min = datetime(YEAR_START - 1, 1, 1)
x_max = datetime(YEAR_END + 1, 12, 31)
y_min = -math.ceil(data.loc[data["Status"]=="Stillgelegt", "Betriebszeit"].max() / 10) * 10
y_max = math.ceil(data.loc[data["Status"]=="In Betrieb", "Betriebszeit"].max() / 10) * 10

# Apply the fixed axis ranges
fig.update_xaxes(range=[x_min, x_max])
fig.update_yaxes(range=[y_min, y_max])


# Add rectangle
# fig.add_shape(
#     type="rect",
#     x0=data["Kommerzieller Betrieb (geplant)"].sort_values().iloc[len(data["Kommerzieller Betrieb (geplant)"]) -3],
#     x1=x_max,
#     y0=0,
#     y1=y_max,
#     yref="y",
#     xref="x",
#     line=dict(width=0),
#     fillcolor="lightgray", opacity=0.2
# )



fig.add_annotation(
    text="Inbetriebnahme<br>Abschaltung",
    x=datetime(YEAR_START, 1, 1),
    y=0,
    xref="x",
    yref="y",
    xanchor="left",  # Anchor point for x (left, center, or right)
    yanchor="middle",  # Anchor point for y (top, middle, or bottom)
    showarrow=False,
    font=dict(size=14, color="black"),
    align="left"
)


fig.add_annotation(
    go.layout.Annotation(
        text="durchschnittliches Alter bei<br>Abschaltung deutlich gestiegen",
        xref="x",
        yref="y",
        x=datetime(2018, 6, 1),
        y=-40,
        font=dict(size=14, color="black"),
        bordercolor="black",
        borderwidth=1,
        bgcolor="white",
        opacity=0.8,
        align="center",
        showarrow=True,
        arrowhead=2,
        arrowsize=1,
        arrowwidth=2,
        arrowcolor='black',
        xanchor="center",  # x-anchor for the arrow
        yanchor="bottom",  # y-anchor for the arrow
        axref="x", ayref="y",
        ax=datetime(2020, 1, 1),  # x-offset for the arrow
        ay=-20    # y-offset for the arrow
    )
)







# %%
# # Add a slider
# slider_steps = []
# for i in range(YEAR_START, YEAR_END+1):
#     step = dict(
#         method="restyle",
#         args=[
#             {"x": [
#                 data.loc[(data["Status"]=="In Betrieb") & (data["Land"]==country) & (data["Jahr_Inbetriebnahme"] <= i), "Kommerzieller Betrieb (geplant)"]
#                 if country in countries else None
#                 for country in countries
#             ] + [
#                 data.loc[(data["Status"]=="Stillgelegt") & (data["Land"]==country) & (data["Jahr_Abschaltung"] <= i), "Abschaltung (geplant)"]
#                 if country in countries else None
#                 for country in countries
#             ]}
#         ],
#         label=str(i),
#     )
#     slider_steps.append(step)

# sliders = [dict(
#     active=len(slider_steps)-1,
#     currentvalue={"prefix": "Year: "},
#     pad={"t": 50},
#     steps=slider_steps
# )]

# fig.update_layout(sliders=sliders)



#%%



# Save the plot as an HTML file
fig.write_html("index.html")

# Display the plot
fig.show()

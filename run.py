# -*- coding: utf-8 -*-
"""
Created on Thu Apr 20 16:18:48 2023

@author: Alexander Blinn
"""

from datetime import datetime
import os

from matplotlib.lines import Line2D
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


# %%

YEAR = 1990

# %%

from matplotlib.colors import LinearSegmentedColormap

# Define a list of colors
colors = [
    (0.000, 0.000, 0.000),  # black
    (0.000, 0.447, 0.698),  # blue
    (0.902, 0.624, 0.000),  # orange
    (0.000, 0.620, 0.451),  # green
    (0.835, 0.369, 0.000),  # red
    (0.580, 0.000, 0.827),  # purple
    (0.980, 0.741, 0.000),  # yellow
    (0.361, 0.361, 0.361),  # gray
    (0.902, 0.196, 0.157),  # dark red
    (0.620, 0.620, 0.000),  # olive
    (0.000, 0.737, 0.831),  # turquoise
    (0.902, 0.510, 0.000),  # dark orange
    (0.420, 0.420, 0.420),  # dark gray
    (0.173, 0.627, 0.173),  # dark green
    (0.631, 0.447, 0.871),  # violet
    (1.000, 0.600, 0.000),  # bright orange
    (0.000, 0.502, 0.502),  # cyan
    (0.753, 0.753, 0.753),  # light gray
    (0.769, 0.008, 0.165),  # pink
    (0.294, 0.000, 0.510),  # dark purple
    (0.502, 0.000, 0.502),  # magenta
    (0.000, 0.000, 1.000),  # pure blue
    (1.000, 0.000, 0.000),  # pure red
    (0.000, 1.000, 0.000),  # pure green
]

# Create the colormap
cmap = LinearSegmentedColormap.from_list('my_colormap', colors, N=len(colors))


# %%

df = pd.read_excel("nuclear_power_plants.xlsx")

# Convert the "Land" column to a categorical column
df["Land_Kategorie"] = pd.Categorical(df["Land"])

# Create a color dictionary for each category code
unique_categories = df["Land_Kategorie"].cat.codes.unique()
colors = cmap(np.linspace(0, 1, len(unique_categories)))
color_dict = {category_code: color for category_code, color in zip(unique_categories, colors)}

# Map category codes to corresponding colors
df["Farbe_Kategorie"] = df["Land_Kategorie"].cat.codes.map(color_dict)



# df["Jahr_Baubeginn"] = df["Baubeginn"].apply(
#     lambda x: x.year if isinstance(x, datetime) else None
#     )

df["Jahr_Inbetriebnahme"] = df["Kommerzieller Betrieb (geplant)"].apply(
    lambda x: x.year if isinstance(x, datetime) else None
    )

df["Jahr_Abschaltung"] = df["Abschaltung (geplant)"].apply(
    lambda x: x.year if isinstance(x, datetime) else None
    )

# df["Bauzeit"] = df["Jahr_Inbetriebnahme"] - df["Jahr_Baubeginn"]

def calculate_operational_time(row):
    if row["Status"] == "In Betrieb":
        return (datetime.now() - row["Kommerzieller Betrieb (geplant)"]).total_seconds() / 86400 / 365.25
    else:
        try:
            return (row["Abschaltung (geplant)"] - row["Kommerzieller Betrieb (geplant)"]).total_seconds() / 86400 / 365.25
        except:
            return None

df["Betriebszeit"] = df.apply(calculate_operational_time, axis=1)

on = df.loc[
    (df["Status"] == "In Betrieb") & (df["Jahr_Inbetriebnahme"] >= YEAR), :
        ]

off = df.loc[df["Jahr_Abschaltung"] >= YEAR, :]

# %%

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), 'config'))
plt.style.use(os.path.join(ROOT, 'mplstyle-ibt'))

# Create the plot
fig, ax = plt.subplots()

# Create the bar plot
# bars = ax.bar(mpg['Year'], mpg['Average MPG'], color=cmap(norm(mpg['Average MPG'].values)))
ax.scatter(on["Kommerzieller Betrieb (geplant)"], on["Betriebszeit"],
           color=on["Farbe_Kategorie"],
           alpha=0.7,
           s=200 * on["Leistung, Netto in MW"] / on["Leistung, Netto in MW"].max()
           )

# Plot the line through the two points
# ax.plot(
#         [
#             on["Kommerzieller Betrieb (geplant)"].min(),
#             on["Kommerzieller Betrieb (geplant)"].max()
#             ],
#         [
#             on["Betriebszeit"].max(),
#             on["Betriebszeit"].min()
#             ], color="k", linestyle="--", linewidth=0.5)

ax.scatter(off["Abschaltung (geplant)"], -off["Betriebszeit"],
           color=off["Farbe_Kategorie"],
           alpha=0.7,
           s=200 * off["Leistung, Netto in MW"] / off["Leistung, Netto in MW"].max()
           )

#%%
# Compute the regression line
x = [date.toordinal() for date in off["Abschaltung (geplant)"]]
y = -off["Betriebszeit"]
regress_coeffs = np.polyfit(x, y, deg=1)

# Plot the regression line
regress_x = np.array([min(x), max(x)])
regress_y = np.polyval(regress_coeffs, regress_x)
ax.plot([datetime.fromordinal(d) for d in regress_x], regress_y,
        color="k", linestyle="--", linewidth=1)

#%%

# Add the average line
# ax.axhline(y=-off["Betriebszeit"].mean(), linestyle="--", color="k", linewidth=1)
ax.axhline(y=0, linestyle='-', color='black', zorder=0)

# Add the highlight box
ymin, ymax = ax.get_ylim()
y_rel_0 = (0 - ymin) / (ymax - ymin)
ax.axvspan(on["Kommerzieller Betrieb (geplant)"].sort_values().iloc[len(on["Kommerzieller Betrieb (geplant)"]) -3], datetime.now(), alpha=0.3, ymin=y_rel_0, ymax=1, color='lightgray', zorder=0)

# Set title and axis labels
ax.set_title("Entwicklung der Atomkraftwerke in Europa seit 1990:\nInbetriebnahme und Stilllegung von Reaktoren", loc="left", fontsize=16)
ax.set_xlabel("Jahr der Inbetriebnahme bzw. der Abschaltung")
ax.set_ylabel("derzeitiges Betriebsalter bzw. Alter bei Abschaltung")

# Customize the x-axis ticks
# ax.xaxis.set_ticks(np.arange(mpg['Year'].min(), mpg['Year'].max() + 1, 1))

# Add annotations
msg = "Die Stromerzeugung aus Kernenergie verliert in Europa zunehmend\n"
msg += "an Bedeutung. Seit 1990 ist der Anteil der Kernenergie am \n"
msg += "elektrischen Verbrauch sowohl auf europäischer als auch globaler\n"
msg += "Ebene im langfristigen Trend rückläufig. Innerhalb der letzten\n"
msg += "15 Jahre wurden lediglich drei neue Reaktoren in Europa errichtet,\n"
msg += "während zwischen 1990 und 2023 insgesamt 23 Reaktoren gebaut und\n"
msg += "90 stillgelegt wurden. Stand April 2023 sind in Europa 128 Reaktoren\n"
msg += "aktiv, deren durchschnittliches Alter mehr als 36 Jahre beträgt, und\n"
msg += "somit das globale durchschnittliche Alter (rund 27 Jahre) für die\n"
msg += "Stilllegung von Kernreaktoren signifikant überschreitet."

ax.annotate(msg,
            xy=(0.56, 0.97), xycoords="axes fraction",
            fontsize=6.5, horizontalalignment="left", verticalalignment="top")

ax.annotate(
    "durchschnittliches Alter bei\nAbschaltung deutlich gestiegen",
    xy=(0.83, 0.14), xytext=(0.7, 0.3), xycoords="axes fraction",
    arrowprops=dict(facecolor="black", shrink=0.01, width=0.1, headwidth=7),
    bbox=dict(facecolor="white", edgecolor="black", boxstyle="round,pad=0.3"),
    fontsize=10, horizontalalignment="left", verticalalignment="bottom")

ax.annotate("Erstellt mit frei verfügbaren Daten\nPunktgröße gibt die Nettoleistung an\n$\copyright$ AB (2023)",
            xy=(1.02, 1.14), xycoords='axes fraction', fontsize=8, fontstyle='italic', color='#a6aeba',
            horizontalalignment="right", verticalalignment="top")


ax.annotate(
    "Olkiluoto (Finnland),\nZubau Block 3, \n17 Jahre Bauzeit",
    xy=(0.95, 0.55), xytext=(0.87, 0.52), xycoords="axes fraction",
    arrowprops=dict(facecolor="black", shrink=0, width=0, headwidth=0),
    bbox=dict(facecolor="white", edgecolor="None", boxstyle="round,pad=0.3"),
    fontsize=7, horizontalalignment="left", verticalalignment="top")

ax.annotate(
    "Belarus baut ersten Reaktorblock,\n10 Jahre Bauzeit,\nzweiter Block für 2023 geplant",
    xy=(0.891, 0.6), xytext=(0.66, 0.63), xycoords="axes fraction",
    arrowprops=dict(facecolor="black", shrink=0, width=0, headwidth=0),
    bbox=dict(facecolor="white", edgecolor="None", boxstyle="round,pad=0.3"),
    fontsize=7, horizontalalignment="left", verticalalignment="top")

ax.annotate("Inbetriebnahme", xy=(0.01, 0.595), xycoords="axes fraction", fontsize=7, horizontalalignment="left", verticalalignment="bottom")
ax.annotate("Abschaltung", xy=(0.01, 0.54), xycoords="axes fraction", fontsize=7, horizontalalignment="left", verticalalignment="bottom")


# %%

# Get the unique countries in the 'on' and 'off' data subsets
unique_on_countries = on["Land_Kategorie"].unique()
unique_off_countries = off["Land_Kategorie"].unique()
unique_on_off_countries = np.unique(np.concatenate((unique_on_countries, unique_off_countries)))

# Create legend proxies for each unique country in the 'on' and 'off' data subsets
legend_elements = [
    Line2D([0], [0], marker="o", color="w", label=country, markerfacecolor=color_dict[df["Land_Kategorie"].cat.categories.get_loc(country)], markersize=8)
    for country in unique_on_off_countries
]

# Add the legend to the plot
legend = ax.legend(handles=legend_elements, loc="lower center", ncol=8, fontsize=8, bbox_to_anchor=(0.5, -0.35))
legend.get_frame().set_linewidth(0.0)
legend._legend_box.align = "left"  # Change alignment of the legend items


# %%

# %% plot output and saving

# plt.savefig('nuc_eu.png', bbox_inches='tight')

plt.show()

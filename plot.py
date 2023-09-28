import numpy as np
import pandas

import networkx

from bokeh.io import save
from bokeh.models import Range1d, Circle, MultiLine
from bokeh.models.glyphs import Text
from bokeh.plotting import figure
from bokeh.plotting import from_networkx
from networkx.drawing.nx_agraph import pygraphviz_layout
from networkx import nx_agraph


def get_data():
    data = pandas.read_csv("rms_ti.csv", index_col=0)

    value = "MSKRMS-12808 TI"

    subset = data[(data[value] >= 0.5)]

    drugs_to_drop = np.unique(
        np.concatenate(
            [
                subset[subset["Drug 1 TI"] < 0.15].drug1,
                subset[subset["Drug 2 TI"] < 0.15].drug2,
            ]
        )
    )

    subset2 = subset[
        ~subset.drug1.isin(drugs_to_drop) | ~subset.drug2.isin(drugs_to_drop)
    ]

    max_per_group_indices = (
        subset2.groupby(["drug1", "drug2"])[value].transform("max") == subset2[value]
    )

    # normalize ['MSKRMS-12808 TI'] to [0, 1]
    subset2["weight"] = 1 + (
        19
        * (
            (subset2[value] - subset2[value].min())
            / (subset2[value].max() - subset2[value].min())
        )
    )

    return subset2[max_per_group_indices].copy()


def shorten_drug_name(drug):
    drug = drug.split(" (")[0]

    return drug.replace(" hydrochloride", "")


def create_network():
    df = get_data()

    G = networkx.Graph()

    for drug1, drug2, weight in df[["drug1", "drug2", "weight"]].itertuples(
        index=False, name=None
    ):
        drug2 = shorten_drug_name(drug2)
        drug1 = shorten_drug_name(drug1)

        G.add_node(drug1, display_name=drug2)

        G.add_node(
            drug2,
            display_name=drug2,
        )

        G.add_edge(drug1, drug2, weight=weight, line_color="black")

    return G


def plot_network_matplotlib():
    G = create_network()

    A = nx_agraph.to_agraph(G)

    A.node_attr["fixedsize"] = "true"
    A.node_attr["fontsize"] = "22"
    A.node_attr["fontname"] = "Arial Bold"
    A.node_attr["style"] = "filled"
    A.node_attr["fillcolor"] = "skyblue"
    A.graph_attr["outputorder"] = "edgesfirst"
    A.graph_attr["ratio"] = "0.61"

    A.layout(prog="circo", args="-Gmindist=1")

    for n in A.nodes():
        n.attr["width"] = 2
        n.attr["height"] = 1

    # set edge widths to be weight attribute
    for e in A.edges():
        e.attr["penwidth"] = e.attr["weight"]
        # set line color

        e.attr["color"] = "#00000098"
        e.attr["headclip"] = "false"
        e.attr["tailclip"] = "false"

    A.draw("/tmp/test.png")


def plot_network():
    G = create_network()

    z = networkx.convert_node_labels_to_integers(G, label_attribute="old_name")

    layout = pygraphviz_layout(z, prog="circo")
    # layout = circular_layout
    network_graph = from_networkx(z, layout, scale=300, center=(0, 0))
    network_text_graph = from_networkx(z, layout, scale=300, center=(0, 0))
    network_graph.node_renderer.glyph = Circle(
        size=100, fill_color="skyblue", line_alpha=0.2, line_width=0.5
    )

    network_graph.edge_renderer.glyph = MultiLine(
        line_color="line_color", line_alpha=0.2, line_width="weight"
    )

    network_text_graph.node_renderer.glyph = Text(
        text="old_name", text_font_size="10pt", text_align="center"
    )

    network_text_graph.edge_renderer.glyph = MultiLine(line_width=0, line_alpha=0)
    # Choose a title!
    title = "Drug Network"

    # Establish which categories will appear when hovering over each node
    HOVER_TOOLTIPS = [
        ("display_name", "@display_name"),
    ]
    plot = figure(
        tooltips=HOVER_TOOLTIPS,
        tools="pan,wheel_zoom,save,reset",
        active_scroll="wheel_zoom",
        x_range=Range1d(-10.1, 10.1),
        y_range=Range1d(-10.1, 10.1),
        title=title,
        width=1500,
        height=1000,
    )

    # remove gridlines
    plot.xgrid.grid_line_color = None
    plot.ygrid.grid_line_color = None

    plot.renderers.append(network_graph)
    plot.renderers.append(network_text_graph)

    save(plot, "/tmp/drug_graph.html")

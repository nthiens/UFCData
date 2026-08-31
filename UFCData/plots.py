from .fighter import get_fighter_history
import pandas as pd
from pyvis.network import Network
import requests
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

## Plot graph

def fighter_graph(fighter_link, degree):
    """
    Create a list of fights involving fighters within a specified graph degree.

    Starting from the specified fighter, this function traverses the fighter's
    fight history for the requested number of degrees. It then retrieves the
    fights associated with the fighters reached at the final degree, merges
    the fight data with fighter biography data, and converts fighter links
    into fighter names.

    Fight outcomes are normalized so that the first fighter in each tuple is
    always the winner when the fight has a decisive result.

    Parameters
    ----------
    fighter_link : str
        UFCStats URL identifying the starting fighter.
    degree : int
        Number of degrees to traverse through the fighter network. A degree
        of 1 includes the starting fighter's opponents, while larger values
        expand the network further.

    Returns
    -------
    list of tuple
        A list of tuples containing:

        - Fighter 1 name
        - Fighter 2 name
        - Fighter 1 outcome

        Each tuple has the form ``(fighter_1, fighter_2, outcome)``.
    """
    current_fighters = {fighter_link}
    fights = set()

    for _ in range(degree):
        future_fighters = set()
        for fighter in current_fighters:
            temp = get_fighter_history(fighter)
            future_fighters.update(temp["Fighter 2 Link"].tolist())
        fights = current_fighters.copy()
        current_fighters = future_fighters

    ## Get fights
    new_fights = set()

    for fight in fights:
      temp = get_fighter_history(fight)
      new_fights.update(temp["Fight Link"].tolist())

    ## Turn fights into tuples
    past_fights = (
        f"https://huggingface.co/datasets/JunoML/MMA/resolve/main/"
        f"past_fights.csv"
    )
    past_fights = pd.read_csv(past_fights)

    fighter_bio = (
        f"https://huggingface.co/datasets/JunoML/MMA/resolve/main/"
        f"fighter_bio.csv"
    )
    fighter_bio = pd.read_csv(fighter_bio)

    tuple_fights = pd.DataFrame(list(new_fights), columns=["Fight Link"])
    tuple_fights = pd.merge(tuple_fights, past_fights,
                            on="Fight Link", how="left")
    tuple_fights = tuple_fights[["Fighter 1 Link", "Fighter 2 Link",
                                 "Fighter 1 Outcome"]]
    ## Convert fighter links to names
    fighter_lookup = fighter_bio.set_index("Fighter Link")["Name"]

    tuple_fights["Fighter 1"] = tuple_fights["Fighter 1 Link"].map(fighter_lookup)
    tuple_fights["Fighter 2"] = tuple_fights["Fighter 2 Link"].map(fighter_lookup)
    tuple_fights = tuple_fights[["Fighter 1", "Fighter 2", "Fighter 1 Outcome"]]
    ## If outcome is L, make it W then switch fighters
    mask = tuple_fights["Fighter 1 Outcome"] == "L"
    tuple_fights.loc[mask, ["Fighter 1", "Fighter 2"]] = (
    tuple_fights.loc[mask, ["Fighter 2", "Fighter 1"]].values
    )
    tuple_fights.loc[mask, "Fighter 1 Outcome"] = "W"
    tuple_fights = list(tuple_fights.itertuples(index=False, name=None))

    return tuple_fights

def add_fight(fighter1, fighter2, outcome, net):
    """
    Add a fight between two fighters to a PyVis network.

    Fighters are automatically added as nodes if they do not already exist.
    The edge style is determined by the fight outcome: wins are represented
    by directed arrows, while draws and no contests use different dashed
    edge styles.

    Parameters
    ----------
    fighter1 : str
        Name of the first fighter.
    fighter2 : str
        Name of the second fighter.
    outcome : str
        Outcome of the fight from the perspective of ``fighter1``.
        Expected values are ``"W"``, ``"L"``, ``"D"``, or ``"NC"``.
    net : pyvis.network.Network
        PyVis network object to which the fighters and fight edge will
        be added.

    Returns
    -------
    None
        The supplied network is modified in place.
    """
    # Add fighters automatically if they don't already exist
    existing_nodes = net.get_nodes()

    for fighter in (fighter1, fighter2):

        if fighter not in existing_nodes:
            net.add_node(
                fighter,
                label=fighter,
                shape="box",
                color={
                    "background": "white",
                    "border": "black",
                    "highlight": {
                        "background": "white",
                        "border": "black"
                    }
                },
                borderWidth=2,
                font={
                    "color": "black",
                    "size": 20
                }
            )

            existing_nodes.append(fighter)

    ## Edge style

    color = "black"

    if outcome == "W":
        dashes = False
        label = ""
        arrows = "to"

    elif outcome == "D":
        dashes = [2, 5]
        label = "DRAW"
        arrows = ""

    else:  # NC
        dashes = [10, 5]
        label = "NC"
        arrows = ""

    net.add_edge(
        fighter1,
        fighter2,
        label=label,
        color=color,
        dashes=dashes,
        arrows=arrows
    )

def plot_fight_graph(fighter_link, degree, notebook=False):
    """
    Generate and display an interactive directed fight graph.

    The graph is constructed by traversing the fight history of a starting
    fighter to the specified degree. Fighters are represented as nodes and
    fights as directed edges. The starting fighter is highlighted in red.

    The resulting interactive graph is saved as ``graph.html`` in the
    current working directory and displayed using PyVis.

    Parameters
    ----------
    fighter_link : str
        UFCStats URL identifying the starting fighter.
    degree : int
        Number of degrees to traverse through the fighter network.
    notebook : bool, default=False
        If False, display the graph using PyVis's standard ``show()``
        method. If True, display the graph directly inside a Jupyter
        notebook or Google Colab.

    Returns
    -------
    None
        The graph is saved to ``graph.html`` and displayed in the browser.
    """
    fighter_bio = (
        f"https://huggingface.co/datasets/JunoML/MMA/resolve/main/"
        f"fighter_bio.csv"
    )
    fighter_bio = pd.read_csv(fighter_bio)

    fighter_name = fighter_bio.loc[
        fighter_bio["Fighter Link"] == fighter_link,"Name" ].iloc[0]

    net = Network(
    height="800px",
    width="100%",
    directed=True,
    bgcolor="white",
    font_color="black"
    )

    net.force_atlas_2based(
        central_gravity=0.01
    )

    graph = fighter_graph(fighter_link, degree)
    for node in graph:
        add_fight(node[0], node[1], node[2], net)

    net.get_node(fighter_name)["font"] = {
    "color": "black",
    "size": 20,
    "bold": True
    }

    net.get_node(fighter_name)["color"] = {
        "background": "#cf0f00",
        "border": "#cf0f00",
        "highlight": {
            "background": "#cf0f00",
            "border": "#cf0f00"
        }
    }
    if notebook is False:
        net.show("graph.html", notebook=False)
    else:
        from IPython.display import display, HTML
        html = net.generate_html(
            name="graph.html",
            notebook=False
        )

        display(
            HTML(
                f"""
                <iframe
                    srcdoc='{html.replace("'", "&#39;")}'
                    width="100%"
                    height="800"
                    frameborder="0">
                </iframe>
                """
            )
        )


## Plot body 

def get_gradient_color(value, start, end, color_start, color_end):
    """
    Calculate an interpolated RGBA color for a value within a range.

    The value is normalized between ``start`` and ``end`` and then used
    to linearly interpolate between the two supplied RGBA colors. Values
    outside the range are clamped to the nearest endpoint.

    Parameters
    ----------
    value : float
        Value for which to calculate the interpolated color.
    start : float
        Minimum value of the range.
    end : float
        Maximum value of the range.
    color_start : tuple of int
        Starting RGBA color represented as a four-element tuple.
    color_end : tuple of int
        Ending RGBA color represented as a four-element tuple.

    Returns
    -------
    tuple of int
        Interpolated RGBA color represented as a four-element tuple.
    """
    # Convert value to 0-1
    t = (value - start) / (end - start)

    # Clamp between 0 and 1
    t = max(0.0, min(1.0, t))

    # Interpolate each RGBA channel
    return tuple(
        round(a + (b - a) * t)
        for a, b in zip(color_start, color_end)
    )

def draw_legend(draw, start, end, color_start, color_end):
    """
    Draw a vertical color-gradient legend on a PIL image.

    The legend is drawn at a fixed position in the top-right portion of
    the image and includes the minimum and maximum values of the supplied
    range.

    Parameters
    ----------
    draw : PIL.ImageDraw.ImageDraw
        PIL drawing object used to draw the legend.
    start : float
        Minimum value represented by the color gradient.
    end : float
        Maximum value represented by the color gradient.
    color_start : tuple of int
        RGBA color corresponding to the minimum value.
    color_end : tuple of int
        RGBA color corresponding to the maximum value.

    Returns
    -------
    None
        The supplied drawing object is modified in place.
    """
    x1 = 1566
    y1 = 260

    x2 = 1670
    y2 = 620

    gradient_height = y2 - y1

    for y in range(y1, y2):

        # Convert Y position into the value range
        value = start + (
            (y - y1) / (gradient_height - 1)
        ) * (end - start)

        # Get the corresponding color
        color = get_gradient_color(
            value,
            start,
            end,
            color_start,
            color_end
        )

        # Draw horizontal line
        draw.line(
            [(x1, y), (x2, y)],
            fill=color
        )
    # Draw black border around gradient
    draw.rectangle(
        (x1 - 2, y1 - 2, x2 + 2, y2 + 2),
        outline=(0, 0, 0, 255),
        width=7
    )

    # Draw text on legend
    font = ImageFont.truetype("impact.ttf", 50)
    draw.text(
        (x1, y1-68),
        str(end),
        fill=(0, 0, 0, 255),
        font=font
    )
    draw.text(
        (x1, y2-5),
        str(start),
        fill=(0, 0, 0, 255),
        font=font
    )

def plot_body(minimum, maximum, title, head, body, leg,
              head_label, body_label, leg_label, suffix):
    """
    Generate and display a color-coded fighter body visualization.

    A fighter silhouette is loaded from an external image and the head,
    body, and leg regions are filled with colors according to their
    corresponding values.

    The required fonts are downloaded automatically if they are not
    already present in the current working directory. The downloaded
    fonts are always used instead of system-installed fonts.

    Parameters
    ----------
    minimum : float
        Minimum value of the scale used for the color gradient.
    maximum : float
        Maximum value of the scale used for the color gradient.
    title : str
        Title displayed on the image and used as the output filename.
    head : float
        Value associated with the fighter's head region.
    body : float
        Value associated with the fighter's body region.
    leg : float
        Value associated with the fighter's leg region.
    head_label : str
        Label displayed next to the head region.
    body_label : str
        Label displayed next to the body region.
    leg_label : str
        Label displayed next to the leg region.
    suffix : str
        Text appended to the numerical values displayed inside each
        body region.

    Returns
    -------
    None
        The generated image is saved as ``<title>.png`` and displayed.
    """

    # Colors
    white = (255, 255, 255, 255)
    red = (204, 0, 0, 255)

    # Download fonts if they don't already exist

    font_urls = {
        "impact.ttf":
            "https://raw.githubusercontent.com/sophilabs/macgifer/"
            "master/static/font/impact.ttf",

        "arial.ttf":
            "https://raw.githubusercontent.com/root-project/root/"
            "master/fonts/arial.ttf",

        "ariblk.ttf":
            "https://raw.githubusercontent.com/root-project/root/"
            "master/fonts/ariblk.ttf",
    }

    font_paths = {}

    for font_name, url in font_urls.items():

        font_path = Path(font_name)

        if not font_path.exists():
            response = requests.get(url)
            response.raise_for_status()

            font_path.write_bytes(response.content)

        font_paths[font_name] = font_path

    # Load downloaded fonts
    title_font = ImageFont.truetype(
        str(font_paths["impact.ttf"]),
        80
    )

    label_font = ImageFont.truetype(
        str(font_paths["arial.ttf"]),
        80
    )

    inner_font = ImageFont.truetype(
        str(font_paths["ariblk.ttf"]),
        80
    )

    # Download fighter image
    ## Sebastian Wallroth, CC0, via Wikimedia Commons
    url = "https://i.imgur.com/2EfCyJB.png"

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    head_original = head
    body_original = body
    leg_original = leg

    response = requests.get(url, headers=headers)

    response.raise_for_status()

    img = Image.open(
        BytesIO(response.content)
    ).convert("RGBA")

    # Create drawing object
    draw = ImageDraw.Draw(img)

    # Background

    ImageDraw.floodfill(
        img,
        (559, 100),
        white
    )

    # Head
    head = abs(head - maximum)
    ImageDraw.floodfill(img, (559, 400),
        get_gradient_color(head, minimum, maximum, red, white))

    # Body
    body = abs(body - maximum)

    ImageDraw.floodfill(img,(559, 800),
        get_gradient_color(body, minimum, maximum, red, white))

    # Leg
    leg = abs(leg - maximum)
    ImageDraw.floodfill(img, (559, 1400),
        get_gradient_color(leg, minimum, maximum, red, white))

    # Legend
    draw_legend(draw, start=minimum, end=maximum,
        color_start=red, color_end=white)

    # Title
    draw.text((80, 50), str(title), 
        fill=(0, 0, 0, 255), font=title_font)

    # Head label
    draw.text((864, 338), str(head_label),
        fill=(0, 0, 0, 255), font=label_font)

    # Head value
    draw.text((80, 330), str(head_original) + suffix,
        fill=(0, 0, 0, 255), font=inner_font)

    # Body label
    draw.text((1127, 925), str(body_label),
        fill=(0, 0, 0, 255), font=label_font)

    # Body value
    draw.text((40, 925), str(body_original) + suffix,
        fill=(0, 0, 0, 255), font=inner_font)

    # Leg label
    draw.text((969, 1870), str(leg_label),
        fill=(0, 0, 0, 255), font=label_font)

    # Leg value
    draw.text((70, 1860), str(leg_original) + suffix,
        fill=(0, 0, 0, 255), font=inner_font)

    # Save
    filename = f"{title}.png"
    img.save(filename)

## Matplotlib graphs in UFC styling

def plot_line_graph(title, x_label, x_values, y_label, y_values, average=True):
    """
    Plot a line graph using UFC-inspired styling.

    The function plots the supplied x and y values and optionally adds a
    horizontal line representing the mean of the y-values.

    Parameters
    ----------
    title : str
        Title displayed above the graph.
    x_label : str
        Label for the x-axis.
    x_values : array-like
        Values plotted along the x-axis.
    y_label : str
        Label for the y-axis and the graph legend.
    y_values : array-like
        Values plotted along the y-axis.
    average : bool, default=True
        Whether to display a horizontal line representing the mean of
        ``y_values``.

    Returns
    -------
    None
        The graph is displayed using Matplotlib.
    """
    plt.figure(figsize=(10, 5))

    # Plot data
    plt.plot(
        x_values,
        y_values,
        color="#666666",
        linestyle="-",
        linewidth=2,
        marker="o",
        markersize=7,
        markerfacecolor="#D20A0A",
        markeredgecolor="#FFFFFF",
        markeredgewidth=1.5,
        label=y_label
    )

    # Draw average line
    if average:
        mean_value = np.mean(y_values)

        plt.axhline(
            mean_value,
            color="#D20A0A",
            linestyle="--",
            linewidth=2,
            label=f"Mean: {mean_value:.2f}"
        )

    # Labels and title
    plt.xlabel(x_label, fontsize=16)
    plt.ylabel(y_label, fontsize=16)
    plt.title(title, fontsize=20)

    # Formatting
    plt.xticks(x_values, fontsize=16)
    plt.yticks(fontsize=16)

    plt.legend(fontsize=13)

    plt.tight_layout()
    plt.show()

def plot_bar_graph(title, x_label, x_values, y_label, y_values, average=True):
    """
    Plot a bar graph using UFC-inspired styling.

    The function plots the supplied x and y values as bars and optionally
    adds a horizontal line representing the mean of the y-values.

    Parameters
    ----------
    title : str
        Title displayed above the graph.
    x_label : str
        Label for the x-axis.
    x_values : array-like
        Values plotted along the x-axis.
    y_label : str
        Label for the y-axis and the graph legend.
    y_values : array-like
        Values represented by the bars.
    average : bool, default=True
        Whether to display a horizontal line representing the mean of
        ``y_values``.

    Returns
    -------
    None
        The graph is displayed using Matplotlib.
    """
    plt.figure(figsize=(10, 5))

    # Plot bars
    plt.bar(
        x_values,
        y_values,
        color="#D20A0A",
        edgecolor="#666666",
        linewidth=1.5,
        label=y_label
    )

    # Draw average line
    if average:
        mean_value = np.mean(y_values)

        plt.axhline(
            mean_value,
            color="#666666",
            linestyle="--",
            linewidth=2,
            label=f"Mean: {mean_value:.2f}"
        )

    # Labels and title
    plt.xlabel(x_label, fontsize=16)
    plt.ylabel(y_label, fontsize=16)
    plt.title(title, fontsize=20)

    # Formatting
    plt.xticks(x_values, fontsize=16)
    plt.yticks(fontsize=16)

    plt.legend(fontsize=13)

    plt.tight_layout()
    plt.show()

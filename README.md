# UFCData

An open-source Python package for accessing, manipulating, analyzing, and visualizing UFC data.

[![PyPI](https://img.shields.io/pypi/v/UFCData)](https://pypi.org/project/UFCData/)
[![Python](https://img.shields.io/badge/python-3.x-blue)](https://www.python.org/)

UFCData provides regularly updated UFC data together with tools for fighter analysis, Elo ratings, data transformation, visualization, and temporal machine learning evaluation. The package is designed for analysts, coaches, researchers, and anyone working with quantitative MMA data.

## Table of Contents

* [Installation](#installation)
* [Getting Started](#getting-started)
* [Available Data](#available-data)
* [Functions](#functions)

  * [Data Access](#data-access)

    * [`get_data()`](#get_data)
  * [Search](#search)

    * [`search(data, column, query, matches=1)`](#searchdata-column-query-matches1)
  * [Ratings](#ratings)

    * [`get_elo(r=1500, k=30, s=400)`](#get_elor1500-k30-s400)
  * [Fighter Analysis](#fighter-analysis)

    * [`get_fighter_history(fighter_link)`](#get_fighter_historyfighter_link)
    * [`get_fighter_statistic(fighter_link, r=1500, k=30, s=400)`](#get_fighter_statisticfighter_link-r1500-k30-s400)
  * [Helper Functions](#helper-functions)

    * [`convert_odds(odds)`](#convert_oddsodds)
    * [`convert_gender(gender)`](#convert_gendergender)
    * [`convert_weight(weight)`](#convert_weightweight)
    * [`mirror(df, cols_1, cols_2, in_order=True)`](#mirrordf-cols_1-cols_2-in_ordertrue)
  * [Model Evaluation](#model-evaluation)

    * [`train_test_split(fights_df, test_size=0.2)`](#train_test_splitfights_df-test_size02)
    * [`get_expanding_window(fights_df, folds, test_size)`](#get_expanding_windowfights_df-folds-test_size)
  * [Plotting](#plotting)

    * [`plot_fight_graph(fighter_link, degree, notebook=False)`](#plot_fight_graphfighter_link-degree-notebookfalse)
    * [`plot_body(...)`](#plot_bodyminimum-maximum-title-head-body-leg-head_label-body_label-leg_label-suffix)
    * [`plot_line_graph(...)`](#plot_line_graphtitle-x_label-x_values-y_label-y_values-averagetrue)
    * [`plot_bar_graph(...)`](#plot_bar_graphtitle-x_label-x_values-y_label-y_values-averagetrue)
* [Example: Temporal Model Evaluation](#example-temporal-model-evaluation)
* [Data Collection](#data-collection)
* [Data and Temporal Leakage](#data-and-temporal-leakage)


## Installation

Install UFCData from PyPI:

```bash
pip install UFCData
```

To update an existing installation:

```bash
pip install --upgrade UFCData
```

## Getting Started

```python
import ufcdata as ufc

data = ufc.get_data()

past_fights = data["past_fights"]
past_fights.head()
```

`get_data()` downloads the current UFC dataset and returns the available datasets as a dictionary of pandas DataFrames. Because the dataframes are downloaded when `get_data()` is called, it is recommended to call the function once and reuse the returned object rather than repeatedly downloading the dataset.

The dataset contains information at several levels of granularity, including events, fights, fighters, and rounds. It also includes upcoming events and scheduled fights.

## Available Data

The dictionary returned by `get_data()` contains the following datasets:

| Key | Description |
|---|---|
| `last_updated` | Date and time indicating when the dataset was last updated |
| `past_events` | Historical UFC events |
| `future_events` | Upcoming UFC events |
| `fighter_bio` | Fighter biographical and physical information |
| `past_fights` | Historical fight level information |
| `future_fights` | Upcoming scheduled fights |
| `past_rounds` | Historical round level statistics |

Column names containing `X` in documentation represent paired variables for Fighter 1 and Fighter 2. For example, Fighter X Link refers to the corresponding Fighter 1 Link and Fighter 2 Link columns.

Links are used as identifiers where possible because fighter names are not guaranteed to be unique.

## Functions

The following are the public functions exported by the `UFCData` package. The list intentionally excludes internal functions that are not part of the package's public interface.

### Data Access

#### `get_data()`

Downloads the current UFC dataset and returns it as a dictionary of pandas DataFrames.

```python
data = ufc.get_data()

past_fights = data["past_fights"]
fighter_bio = data["fighter_bio"]
```

---

### Search

#### `search(data, column, query, matches=1)`

Performs fuzzy string matching against a selected DataFrame column.

This is useful when searching for fighters, events, or other records where exact spelling or naming conventions may vary.

```python
results = ufc.search(
    fighter_bio,
    "Name",
    "Jon Jones",
    matches=3
)
```

**Parameters**

- `data` — DataFrame to search.
- `column` — Column containing the values to search.
- `query` — Text to search for.
- `matches` — Number of closest matches to return. Defaults to `1`.

The closest matches are returned as a DataFrame, ordered by match quality.

---

### Ratings

#### `get_elo(r=1500, k=30, s=400)`

Calculates Elo ratings for UFC fighters.

Fights are processed chronologically. Each fighter's rating is recorded immediately before their fight and then updated using the fight outcome. This makes the resulting historical Elo ratings suitable for predictive modelling without using information from the fight being predicted.

```python
current_elo, past_elo = ufc.get_elo(
    r=1500,
    k=30,
    s=400
)
```

**Parameters**

- `r` — Initial rating for each fighter. Defaults to `1500`.
- `k` — K-factor controlling how strongly ratings change after each fight. Defaults to `30`.
- `s` — Elo scaling factor used when calculating expected scores. Defaults to `400`.

**Returns**

- `current_elo` — Dictionary containing each fighter's current Elo rating.
- `past_elo` — Fight-level DataFrame containing the pre-fight Elo rating for each fighter.

---

### Fighter Analysis

#### `get_fighter_history(fighter_link)`

Retrieves the UFC fight history for a fighter.

```python
fighter = "http://ufcstats.com/fighter-details/54f64b5e283b0ce7"

history = ufc.get_fighter_history(fighter)
history.head()
```

The returned data are represented from the requested fighter's perspective. The function includes the fighter's UFC fight history together with relevant opponent and fight information.

---

#### `get_fighter_statistic(fighter_link, r=1500, k=30, s=400)`

Generates current and historical cumulative statistics for a UFC fighter.

```python
fighter = "http://ufcstats.com/fighter-details/150ff4cc642270b9"

current_stats, past_stats = ufc.get_fighter_statistic(
    fighter,
    r=1500,
    k=30,
    s=400
)
```

The function calculates statistics from information available before each fight, making the historical results suitable for predictive modelling.

The statistics include:

- UFC fight number
- UFC wins, losses, draws, and no contests
- UFC win rate
- Elo rating
- Cumulative fight time
- Significant strikes landed per minute (`SLpM`)
- Significant strike accuracy (`Str Acc`)
- Significant strikes absorbed per minute (`SApM`)
- Significant strike defense (`Str Def`)
- Takedown average (`TD Avg`)
- Takedown accuracy (`TD Acc`)
- Takedown defense (`TD Def`)
- Submission attempts per 15 minutes (`Sub Avg`)

**Returns**

- `current_stats` — A one-row DataFrame containing the fighter's current statistics.
- `past_stats` — A historical DataFrame containing statistics as they were known before each fight.

This temporal construction prevents future fight information from being used to describe a fighter's past performance.

---

### Helper Functions

#### `convert_odds(odds)`

Converts American betting odds to implied probability.

```python
ufc.convert_odds("+120")
# 0.454545...

ufc.convert_odds("-400")
# 0.8
```

For positive odds:

```text
Probability = 100 / (odds + 100)
```

For negative odds:

```text
Probability = -odds / (-odds + 100)
```

Missing values return `None`.

---

#### `convert_gender(gender)`

Converts the package's gender labels into binary numeric values.

```python
ufc.convert_gender("Male")
# 1

ufc.convert_gender("Female")
# 0
```

`Male` is mapped to `1`, `Female` to `0`, and unrecognized or missing values return `None`.

---

#### `convert_weight(weight)`

Converts UFC weight-class labels into their corresponding weight limits in pounds.

```python
ufc.convert_weight("Lightweight")
# 155
```

Recognized classes include:

| Weight class | Limit (lb) |
|---|---:|
| Strawweight | 115 |
| Flyweight | 125 |
| Bantamweight | 135 |
| Featherweight | 145 |
| Lightweight | 155 |
| Welterweight | 170 |
| Middleweight | 185 |
| Light Heavyweight | 205 |
| Heavyweight | 265 |
| Super Heavyweight | 265 |

Catch Weight, Open Weight, unrecognized classes, and missing values return `NaN`.

---

#### `mirror(df, cols_1, cols_2, in_order=True)`

Creates mirrored versions of a DataFrame by swapping corresponding pairs of columns.

This is useful for converting fight-level data into fighter-level data where each fight is represented from both fighters' perspectives.

```python
cols_1 = ["Fighter 1", "Fighter 1 Odds"]
cols_2 = ["Fighter 2", "Fighter 2 Odds"]

mirrored = ufc.mirror(
    past_fights,
    cols_1,
    cols_2
)
```

With `in_order=True`, each original row is immediately followed by its mirrored row. With `in_order=False`, all original rows are followed by all mirrored rows.

---

### Model Evaluation

UFC fight data are inherently temporal. Randomly shuffling fights before creating training and test sets can allow information from future fights to influence model training. UFCData therefore provides chronological splitting and expanding-window cross validation.

#### `train_test_split(fights_df, test_size=0.2)`

Creates chronological training and test sets.

The input DataFrame should be ordered from newest to oldest. The most recent fights are assigned to the test set, while older fights are assigned to the training set. Both returned DataFrames are then ordered from oldest to newest.

```python
train, test = ufc.train_test_split(
    past_fights,
    test_size=0.2
)
```

**Parameters**

- `fights_df` — UFC fight DataFrame ordered from newest to oldest.
- `test_size` — If less than `1`, interpreted as a proportion of the data. If greater than or equal to `1`, interpreted as the number of fights in the test set. Defaults to `0.2`.

**Returns**

- `train` — Older fights, ordered from oldest to newest.
- `test` — Most recent fights, ordered from oldest to newest.

---

#### `get_expanding_window(fights_df, folds, test_size)`

Creates expanding-window training and fixed-size test sets for time-series cross validation.

The input DataFrame should be ordered from oldest to newest. For each fold, the training set contains all historical observations available up to that point, while the test set contains the next fixed number of fights.

```python
folds = ufc.get_expanding_window(
    train,
    folds=10,
    test_size=500
)

fold_1_test = folds["Fold 1"]["test"]
```

**Parameters**

- `fights_df` — UFC fight DataFrame ordered from oldest to newest.
- `folds` — Number of cross-validation folds.
- `test_size` — Number of fights in each test set.

**Returns**

A dictionary containing a `train` and `test` DataFrame for each fold:

```python
{
    "Fold 1": {
        "train": train_dataframe,
        "test": test_dataframe
    },
    "Fold 2": {
        "train": train_dataframe,
        "test": test_dataframe
    }
}
```

This approach avoids the temporal leakage that can occur when conventional random K-fold cross validation is applied to time-dependent fight data.

---

### Plotting

#### `plot_fight_graph(fighter_link, degree, notebook=False)`

Generates an interactive directed graph of a fighter's network of opponents.

```python
fighter = "http://ufcstats.com/fighter-details/e5549c82bfb5582d"

ufc.plot_fight_graph(
    fighter,
    degree=2
)
```

Fighters are represented as nodes and fights as directed edges. The graph can be used to explore opponent networks, rivalries, and the concept of "MMA Math," where fans informally attempt to infer outcomes through chains of previous results.

Set `notebook=True` when displaying the graph in a Jupyter environment.

---

#### `plot_body(minimum, maximum, title, head, body, leg, head_label, body_label, leg_label, suffix)`

Generates a color-coded fighter body visualization for displaying values associated with different body regions.

```python
ufc.plot_body(
    0,
    100,
    "Strike Accuracy",
    49.5,
    88,
    93.1,
    "49.5",
    "88",
    "93.1",
    "%"
)
```

The function provides a standardized body template with color gradients that can be used to visualize offensive or defensive statistics by body location.

---

#### `plot_line_graph(title, x_label, x_values, y_label, y_values, average=True)`

Creates a line graph using UFC-inspired styling.

```python
ufc.plot_line_graph(
    title="Baseline Fold Accuracies",
    x_label="Fold",
    x_values=["1", "2", "3"],
    y_label="Accuracy",
    y_values=[0.62, 0.65, 0.64]
)
```

When `average=True`, the graph also displays a horizontal line representing the mean of the supplied y-values.

---

#### `plot_bar_graph(title, x_label, x_values, y_label, y_values, average=True)`

Creates a bar graph using UFC-inspired styling.

```python
ufc.plot_bar_graph(
    title="Fight Accuracy",
    x_label="Model",
    x_values=["Baseline", "Model"],
    y_label="Accuracy",
    y_values=[0.61, 0.67]
)
```

When `average=True`, the graph also displays a horizontal line representing the mean of the supplied y-values.

## Example: Temporal Model Evaluation

The following example demonstrates a simple betting-odds baseline using a chronological train/test split and expanding-window cross validation.

```python
import numpy as np
import ufcdata as ufc

data = ufc.get_data()

fights = data["past_fights"].copy()

# Remove draws and no contests
fights = fights[
    ~fights["Fighter 1 Outcome"].isin(["NC", "D"])
]

# Keep fights where both fighters have betting odds
fights = fights.dropna(
    subset=["Fighter 1 Odds", "Fighter 2 Odds"]
)

# Convert American odds to implied probabilities
fights["Fighter 1 Prob"] = fights["Fighter 1 Odds"].apply(
    ufc.convert_odds
)
fights["Fighter 2 Prob"] = fights["Fighter 2 Odds"].apply(
    ufc.convert_odds
)

# Identify the actual winner
fights["Winner"] = np.where(
    fights["Fighter 1 Outcome"] == "W",
    fights["Fighter 1 Link"],
    fights["Fighter 2 Link"]
)

# Chronological train/test split
train, test = ufc.train_test_split(
    fights,
    test_size=0.2
)

# Expanding-window cross validation
cv = ufc.get_expanding_window(
    train,
    folds=10,
    test_size=500
)

fold_accuracy = []

for i in range(1, 11):
    fold = cv[f"Fold {i}"]["test"].copy()

    fold["Predicted Winner"] = np.where(
        fold["Fighter 1 Prob"] > fold["Fighter 2 Prob"],
        fold["Fighter 1 Link"],
        fold["Fighter 2 Link"]
    )

    accuracy = (
        fold["Predicted Winner"] == fold["Winner"]
    ).mean()

    fold_accuracy.append(accuracy)

ufc.plot_line_graph(
    title="Baseline Fold Accuracies",
    x_label="Fold",
    x_values=[str(i) for i in range(1, 11)],
    y_label="Accuracy",
    y_values=fold_accuracy
)
```

The key distinction is that the final test set represents later fights that are not used during model development, while each cross-validation fold uses only fights that occurred before its corresponding test period.

## Data Collection

UFCData is supported by an automated data collection pipeline that combines information from multiple publicly available sources, including UFCStats, Wikipedia, and Tapology.

The initial scraping process collects the historical dataset. Subsequent updates are automated around upcoming UFC events. The system identifies the next event, updates the dataset shortly before the event begins to capture scheduled information, and performs another update after the event to capture newly available results and statistics.

The scraper is designed to minimize unnecessary requests to source websites. The initial collection can take several hours, while subsequent updates typically take only a few minutes.

Users generally do not need to run the scrapers themselves because the dataset is maintained automatically.

The scraping infrastructure is available in the repository for transparency and reproducibility:

https://github.com/nthiens/UFCData/tree/main/scraper


## Data and Temporal Leakage

UFCData is designed with the temporal nature of fight data in mind.

Functions such as `get_elo()` and `get_fighter_statistic()` calculate historical information using only data available before the corresponding fight. Similarly, `train_test_split()` creates chronological training and test sets, while `get_expanding_window()` creates expanding training windows for time-series cross validation.

These approaches are intended to prevent future observations from influencing historical features or model training.

Standard random K-fold cross validation is generally inappropriate for this type of data because it can place observations from future fights in a model's training data while evaluating it on earlier fights.

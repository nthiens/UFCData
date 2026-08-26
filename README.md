# UFCData


An open-source Python package for accessing, manipulating, and analyzing UFC data.

https://pypi.org/project/UFCData/

## Table of Contents



- [Installation](#installation)
- [Updating the Package](#updating-the-package)

Accessing Data
  - [Loading Data](#loading-data)
  - [Search](#search)

Rating Function
  - [Elo](#elo)

Fighter Functions
- [Fighter History](#fighter-history)
- [Fighter Statistic](#fighter-statistic)

Helper Functions
  - [Odds Convert](#odds-convert)
  - [Weight Convert](#weight-convert)
  - [Gender Convert](#gender-convert)
  - [Mirror](#mirror)

Model Evaluation
- [Train Test Split](#train-test-split)
- [Get Expanding Window](#get-expanding-window)
- [Plotting Accuracy](#plotting-accuracy)
- [Expanding Window Baseline Example](#expanding-window-baseline-example)


Data Sources
  - [Online Sources](#online-sources)
  - [Discrepancies in Data](#discrepancies-in-data)
  - [Update Frequency](#update-frequency)

<br>

---

<br>

## Installation

```bash
pip install ufcdata
```

## Updating the Package

```bash
pip install --no-cache-dir --upgrade ufcdata
```

---

<br>

##  Loading Data

```python
import ufcdata as ufc
data = ufc.get_data()

fighter_bio = data["fighter_bio"].copy()
```

Note that data in here and other functions below reference data that is available prior to the data.

<br>

## Search

Due to various event naming conventions and fighters sharing the same name, the primary keys for the dataframes are links, which can be difficult for humans to interpret. The `search()` function uses fuzzy string matching to make it easier to find fighters, events, and other records.

```python
search(data, column, query, matches=1)
```

### Parameters

* `data` — The dataframe you are searching.
* `column` — The name of the column to search.
* `query` — The name or text you are searching for.
* `matches` — The number of closest matches to return. Defaults to `1`.

### Returns
The results are returned as a dataframe, with the closest match appearing first.

### Example

```python
john_jones = ufc.search(fighter_bio, "Name", "Jon Jones", 3)
```


---

<br>

## Elo

UFCData provides an Elo rating system for calculating fighter ratings based on their previous fight results. Ratings are calculated chronologically, with each fighter's rating recorded immediately before each fight.

This allows Elo ratings to be used as features for predictive modeling without incorporating information from the fight being predicted.


```python
ufc.get_elo(fight_df, fighter_df, r=1500, k=30, s=400)
```

### Parameters

* `fight_df` — The UFC fight dataframe, sorted from most recent to least recent.
* `fighter_df` — The fighter information dataframe containing a `"Fighter Link"` column.
* `r` — Initial Elo rating for each fighter. Defaults to `1500`.
* `k` — K-factor controlling how much ratings change after each fight. Defaults to `30`.
* `s` — Scaling factor used when calculating expected scores. Defaults to `400`.

### Returns

The function returns a tuple containing:

1. `current_elo` — A dictionary mapping each fighter's UFCStats link to their final Elo rating.
2. `past_elo` — The original `fights_df` dataframe with `"Fighter 1 Elo"` and `"Fighter 2 Elo"` columns added. These columns contain each fighter's Elo rating immediately prior to the corresponding fight.


### Example

```python
import ufcdata as ufc

data = ufc.get_data()

past_fights = data["past_fights"].copy()
fighter_bio = data["fighter_bio"].copy()

current_elo, past_elo = ufc.get_elo(
    past_fights,
    fighter_bio
)
```


### Important

`fight_df` should be sorted from most recent to least recent before being passed to `get_elo()`. The function reverses the dataframe internally to process fights chronologically and returns the resulting data in the original order.

<br>

---

<br>

## Fighter History

The function `get_fighter_history()` retrieves all UFC fights for a specific fighter and formats the results from the fighter's perspective. The requested fighter is always represented as `"Fighter 1"`, regardless of which side of the original fight dataframe they appeared on.

The function also calculates the age of both fighters at the time of each fight and assigns a `"UFC Fight"` number to each fight.


```python
ufc.get_fighter_history(fighter_link, fighter_bio, fights_df)
```

### Parameters

* `fighter_link` — The UFCStats link identifying the fighter.
* `fighter_bio` — The fighter information dataframe returned by `get_data()`.
* `fights_df` — The fight dataframe containing UFC fight history.

### Returns

A dataframe containing the fighter's fight history from most recent to least recent. The requested fighter is always `"Fighter 1"`, with fighter ages and `"UFC Fight"` numbers included.



### Example

```python
import ufcdata as ufc

data = ufc.get_data()

fighter_bio = data["fighter_bio"].copy()
fights_df = data["past_fights"].copy()

jon_jones = ufc.search(
    fighter_bio,
    "Name",
    "Jon Jones"
).iloc[0]["Fighter Link"]

jon_jones_history = ufc.get_fighter_history(
    jon_jones,
    fighter_bio,
    fights_df
)
```

This function is useful for analyzing an individual fighter's career, constructing fighter-level features, or preparing historical data for predictive modeling.

<br>

## Fighter Statistic


The function `get_fighter_statistic()`, transforms a fighter's UFC fight history into a time-series dataset where each row represents the fighter's statistics as they were known before a particular fight.

This is designed for machine-learning applications where using information from the future would cause data leakage.


```python
get_fighter_statistic(
    fighter_link,
    fighter_bio,
    fights_df,
    rounds_df,
    r=1500,
    k=30,
    s=400
)
```



### Parameters

| Parameter      | Type                    | Description                                                                                        |
| -------------- | ----------------------- | -------------------------------------------------------------------------------------------------- |
| `fighter_link` | `str`                   | UFCStats link or identifier for the fighter.                                                       |
| `fighter_bio`  | `pd.DataFrame`          | Fighter biography DataFrame containing fighter names and links.                                    |
| `fights_df`    | `pd.DataFrame`          | Fight-level UFC data containing fight results and metadata.                                        |
| `rounds_df`    | `pd.DataFrame`          | Round-level UFC statistics.                                                                        |
| `future_df`    | `pd.DataFrame`          | DataFrame containing the upcoming fight. The first row is used to determine the future fight date. |
| `r`            | `float`, default `1500` | Initial Elo rating.                                                                                |
| `k`            | `float`, default `30`   | Elo K-factor controlling the magnitude of rating updates.                                          |
| `s`            | `float`, default `400`  | Elo scaling factor used when calculating expected scores.                                          |

### Returns

The function returns a tuple containing:

#### `current_statistic`

A one-row DataFrame containing the fighter's current statistic.

This includes:

* UFC fight number
* UFC record
* UFC win rate
* Elo rating
* Cumulative fight time
* Significant strikes landed per minute (`SLpM`)
* Significant strike accuracy (`Str Acc`)
* Significant strikes absorbed per minute (`SApM`)
* Significant strike defense (`Str Def`)
* Takedown average (`TD Avg`)
* Takedown accuracy (`TD Acc`)
* Takedown defense (`TD Def`)
* Submission attempts per 15 minutes (`Sub Avg`)

#### `past_statistic`

A DataFrame containing the same types of statistics for each previous UFC fight.

Each row represents the fighter's information immediately before that fight.

For example:

```text
Fight 1 → statistics before Fight 1
Fight 2 → statistics before Fight 2
Fight 3 → statistics before Fight 3
...
```

This makes the data suitable for constructing historical features for a predictive model.


### Example

```python
import ufcdata as ufc

data = ufc.get_data()

fighter_bio = data["fighter_bio"].copy()
fights_df = data["past_fights"].copy()
rounds_df = data['past_rounds'].copy()
future_df = data['future_fights']

jon_jones = ufc.search(
    fighter_bio,
    "Name",
    "Jon Jones"
).iloc[0]["Fighter Link"]

jon_jones_current, jon_jones_past = ufc.get_fighter_statistic(
    jon_jones,
    fighter_bio,
    fights_df,
    rounds_df
)
```


---

<br>

## Odds Convert

The function `convert_odds()` converts American betting odds from strings into integers or floating point numbers.

```python
convert_odds(odds)
```

### Parameters

* `odds` — American betting odds as a string, integer, float or None.

### Returns

Returns a `float` representing the implied probability of the betting odds.

For positive American odds:

```text
Probability = 100 / (odds + 100)
```

For negative American odds:

```text
Probability = -odds / (-odds + 100)
```

### Example

```python
import ufcdata as ufc

data = ufc.get_data()

fights_df = data["past_fights"].copy()

fights_df["Fighter 1 Probability"] = fights_df["Fighter 1 Odds"].apply(
    ufc.convert_odds,
)
```

<br>

## Gender Convert

The function `convert_gender()` converts gender labels into binary numeric values, with `"Male"` represented as `1` and `"Female"` represented as `0`.

```python
convert_gender(gender)
```

### Parameters

* `gender` — Gender label as a string.

### Returns

Returns `1` for `"Male"` and `0` for `"Female"`.

If the gender is missing or does not match either `"Male"` or `"Female"`, it returns `None`.

### Example

```python
import ufcdata as ufc

data = ufc.get_data()

fights_df = data["past_fights"].copy()
fights_df["Gender"] = fights_df["Gender"].apply(ufc.convert_gender)
```

<br>

## Weight Convert

The function `convert_weight()` converts UFC weight class labels into their corresponding weight limits in pounds.

```python
convert_weight(weight)
```

### Parameters

* `weight` — Weight class as a string.

### Returns

Returns the weight limit in pounds for recognized weight classes.

| Weight Class      | Weight (lb) |
| ----------------- | ----------: |
| Strawweight       |         115 |
| Flyweight         |         125 |
| Bantamweight      |         135 |
| Featherweight     |         145 |
| Lightweight       |         155 |
| Welterweight      |         170 |
| Middleweight      |         185 |
| Light Heavyweight |         205 |
| Heavyweight       |         265 |
| Super Heavyweight |         265 |

For `"Catch Weight"` and `"Open Weight"`, as well as unrecognized or missing values, the function returns `NaN`.

### Example

```python
import ufcdata as ufc

data = ufc.get_data()

past_fights = data["past_fights"].copy()
past_fights["Weight Class"] = past_fights["Weight Class"].apply(ufc.convert_weight)
```

<br>

## Mirror

The function `mirror()` creates mirrored versions of a DataFrame by swapping corresponding pairs of columns. This is useful when analyzing UFC fights from both fighters' perspectives.

```python
mirror(df, cols_1, cols_2, in_order=True)
```

### Parameters

* `df` — The DataFrame to mirror.
* `cols_1` — List of column names representing the first fighter or side.
* `cols_2` — List of column names representing the second fighter or side. Each column is swapped with the corresponding column in `cols_1`.
* `in_order` — Determines the order of the returned rows. Defaults to `True`.

If `in_order=True`, each original row is immediately followed by its mirrored row.

If `in_order=False`, all original rows are followed by all mirrored rows.

### Returns

Returns a DataFrame containing both the original and mirrored versions of each row.

### Example

```python
import ufcdata as ufc

data = ufc.get_data()

fights_df = data["past_fights"].copy()
fights_df = fights_df[
    [
        "Date",
        "Event Link",
        "Fighter 1",
        "Fighter 1 Odds",
        "Fighter 2",
        "Fighter 2 Odds",
    ]
]

cols_1 = [
    "Fighter 1",
    "Fighter 1 Odds",
]

cols_2 = [
    "Fighter 2",
    "Fighter 2 Odds",
]

mirrored_fights = ufc.mirror(
    fights_df,
    cols_1,
    cols_2
)
```

Using `in_order=True` produces rows in the following order:

```text
Original Fight 1
Mirrored Fight 1
Original Fight 2
Mirrored Fight 2
...
```
Using `in_order=False` produces rows in the following order:
```text
Original Fight 1
Original Fight 2
Mirrored Fight 1
Mirrored Fight 2
...
```

This is useful when creating fighter-level datasets where each fight should be represented from both fighters' perspectives.

<br>

---

<br>

## Train Test Split
The function `train_test_split()` splits a UFC fight DataFrame into training and test sets while preserving the chronological order of the data. Unlike `sklearn.model_selection.train_test_split()`, this function does not randomly shuffle the data.

The input `fights_df` should be ordered from newest to oldest. The most recent fights are assigned to the test set, while the older fights are assigned to the training set. Both returned DataFrames are then reordered from oldest to newest.

```python
train_test_split(fights_df, test_size=0.2)
```
### Parameters

* `fights_df` — UFC fight DataFrame ordered from newest to oldest.
* `test_size` — Determines the size of the test set. If less than 1, it is interpreted as a proportion of the total number of fights. If greater than or equal to 1, it is interpreted as the exact number of fights to include in the test set. Defaults to 0.2.
### Returns
The function returns two dataFrames. The first is a dataFrame containing the older fights used for training, ordered from oldest to newest. The second is a dataFrame containing the most recent fights used for testing, ordered from oldest to newest.

### Example

```python
import ufcdata as ufc

data = ufc.get_data()

past_fights = data["past_fights"].copy()
train, test = ufc.train_test_split(past_fights, 0.2)
```

<br>

## Get Expanding Window
The function `get_expanding_window()` creates multiple training and test sets for time-series cross-validation using an expanding training window.

The input `fights_df` should be ordered from oldest to newest. With each fold, the training set expands to include more historical fights, while the test set remains a fixed size.

```python
fold_results = ufc.get_expanding_window(
    fights_df,
    folds=5,
    test_size=500
)
```
### Parameters

* `fights_df` — UFC fight DataFrame ordered from oldest to newest.
* `folds` — The number of train/test folds to create.
* `test_size` — The number of fights included in each test set.

### Returns
The function returns a dictionary containing the training and test DataFrames for each fold.
```python
{
    "Fold 1": {
        "train": train_dataframe,
        "test": test_dataframe
    },
    "Fold 2": {
        "train": train_dataframe,
        "test": test_dataframe
    },
    ...
}
```
### Example

```python
import ufcdata as ufc

data = ufc.get_data()

past_fights = data["past_fights"].copy()
train, test = ufc.train_test_split(past_fights, 0.2)

folds = ufc.get_expanding_window(train, 10, 500)
folds['Fold 2']['test']
```
<br>

## Plotting Accuracy

The function `plot_cv` plots out a line graph showing the accuracy of each fold along with a line showing the mean.

```python
plot_cv(cv_labels, cv_accuracies, title="Cross Validation Accuracy")
```

### Parameters

* `cv_labels` — The list of fold names.
* `cv_accuracies` — The list of accuracies.
* `title` — The title of the plot.

The function `plot_test` plots out a single bar graph showing the accuracy of a single test.

```python
plot_test(accuracy, title="Test Accuracy")
```

### Parameters

* `accuracy` — The accuracy.
* `title` — The title of the plot.

<br>

## Expanding Window Baseline Example

In this example, we split the data into 80% for cross-validation and 20% for final testing. The cross-validation set is evaluated using a 15-fold expanding window approach. Using only betting odds, we convert the odds into implied probabilities and predict the fighter with the higher probability as the winner. The example also demonstrates how the model can be deployed.

<br>

```python
import ufcdata as ufc
import numpy as np

data = ufc.get_data()

## Select rows where outcome is W or L and both fighters have odds associated with the fights.
past_fights = data["past_fights"].copy()
past_fights = past_fights[~past_fights["Fighter 1 Outcome"].isin(["NC", "D"])]
past_fights = past_fights[past_fights[["Fighter 1 Odds", "Fighter 2 Odds"]].notna().all(axis=1)]

## Convert odds to probabilities
past_fights["Fighter 1 Probability"] = (
    past_fights["Fighter 1 Odds"]
    .apply(ufc.convert_odds, probability=True)
)

past_fights["Fighter 2 Probability"] = (
    past_fights["Fighter 2 Odds"]
    .apply(ufc.convert_odds, probability=True)
)

## Create the data for cross validation and final testing
folds = 15
fold_names = [f"Fold {i}" for i in range(1, folds + 1)]
cross_validation, final_test = ufc.train_test_split(past_fights, 0.2)
fifteen_fold_cv = ufc.get_expanding_window(cross_validation, folds, 500)

fold_accuracy = []
## Loop through each fold to get the accuracy
for fold in fold_names:
  test = fifteen_fold_cv[fold]['test']
  test["Predicted Winner"] = np.where(
    test["Fighter 1 Probability"] > test["Fighter 2 Probability"],
    test["Fighter 1 Link"],
    test["Fighter 2 Link"])
  accuracy = float((test["Predicted Winner"] == test["Winner"]).mean())
  fold_accuracy.append(accuracy)

## Plot cross validation accuracy
ufc.plot_cv(fold_names, fold_accuracy)
```
<br>

![Cross Validation Plot](https://i.imgur.com/sjCpnRE.png)

<br>

```python
## Evaluate on final test set
final_test["Predicted Winner"] = np.where(
    final_test["Fighter 1 Probability"] > final_test["Fighter 2 Probability"],
    final_test["Fighter 1 Link"],
    final_test["Fighter 2 Link"])
test_accuracy = float((final_test["Predicted Winner"] == final_test["Winner"]).mean())
ufc.plot_test(test_accuracy)
```

<br>

![Test Plot](https://i.imgur.com/5dHR59X.png)

<br>

```python
## Deploy the model
future_fights = data["future_fights"].copy()

future_fights["Fighter 1 Probability"] = (
    future_fights["Fighter 1 Odds"]
    .apply(ufc.convert_odds, probability=True)
)

future_fights["Fighter 2 Probability"] = (
    future_fights["Fighter 2 Odds"]
    .apply(ufc.convert_odds, probability=True)
)

future_fights["Predicted Winner"] = np.where(
    future_fights["Fighter 1 Probability"] > future_fights["Fighter 2 Probability"],
    future_fights["Fighter 1 Link"],
    future_fights["Fighter 2 Link"])

future_fights["Predicted Winner"] = np.where(
    future_fights["Predicted Winner"] == future_fights["Fighter 1 Link"],
    future_fights["Fighter 1"],
    future_fights["Fighter 2"]
)

future_fights = future_fights[
    [
        "Date",
        "Event Link",
        "Fight Link",
        "Fighter 1",
        "Fighter 2",
        "Predicted Winner"
    ]
]

future_fights

```
<br>

![Deployed Predictions](https://i.imgur.com/jgZzNOV.png)

<br>

---

<br>

## Online Sources

Odds and birthplace data was obtained from https://www.tapology.com
 
Venue and attendance data was obtained from https://en.wikipedia.org/wiki/List_of_UFC_events

All other data was obtained from http://ufcstats.com

<br>

## Discrepancies in Data

UFCStats is treated as the authoritative source for UFCData. When discrepancies exist between UFCStats and other sources, such as Wikipedia or Tapology, the UFCStats data is used.

The UFCStats completed events page serves as the authoritative source for event, fight, and round data. Individual fighter profiles may contain fights from organizations or events that are not included in the completed events database, including WEC, Strikeforce, and PRIDE. These events are therefore excluded from UFCData.

<br>

## Update Frequency

The dataset is updated at the start of the scheduled broadcast time for each event. This update captures changes to betting odds, as well as any cancelled, postponed, or otherwise modified fights.

A second update occurs 24 hours after the start of the broadcast. This update captures the finalized event, fight, and round data, as well as information on upcoming events and fights.

Changes occurring between these scheduled updates are not automatically captured. Users are responsible for manually updating the dataset if they require the most current data for analysis or prediction.

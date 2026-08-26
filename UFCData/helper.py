import re
import pandas as pd
import numpy as np

def convert_odds(odds):
    """
    Convert American betting odds to implied probability.

    Parameters
    ----------
    odds : str, int, float, or None
        American betting odds. The function extracts the first signed or
        unsigned integer from the input. Missing values return None.

    Returns
    -------
    float or None
        The implied probability as a decimal. Returns None for missing values.

    Examples
    --------
    >>> convert_odds("+120")
    0.45454545454545453
    >>> convert_odds("-400")
    0.8
    """
    if pd.isna(odds):
        return None

    odds = int(re.search(r'[+-]?\d+', str(odds)).group())

    if odds < 0:
        return -odds / (-odds + 100)
    else:
        return 100 / (odds + 100)

def convert_gender(gender):
    """
    Convert a gender label to a binary numeric value.

    Parameters
    ----------
    gender : str
        Gender label. "Male" is mapped to 1 and "Female" is mapped to 0.

    Returns
    -------
    int or None
        1 for "Male", 0 for "Female", and None for unrecognized or missing values.
    """
    if gender == "Male":
        return 1
    elif gender == "Female":
        return 0
    else:
        return None


def convert_weight(weight):
    """
    Convert a weight class label to its corresponding weight limit in pounds.

    Parameters
    ----------
    weight : str
        Weight class label to convert.

    Returns
    -------
    float
        Weight limit in pounds for recognized weight classes. Returns NaN for
        catch weight, open weight, unrecognized weight classes, or missing values.
    """
    weight_map = {
        "Strawweight": 115,
        "Flyweight": 125,
        "Bantamweight": 135,
        "Featherweight": 145,
        "Lightweight": 155,
        "Welterweight": 170,
        "Middleweight": 185,
        "Light Heavyweight": 205,
        "Heavyweight": 265,
        "Super Heavyweight": 265,
        "Catch Weight": np.nan,
        "Open Weight": np.nan,
    }
    return weight_map.get(weight.strip(), np.nan)


def mirror(df, cols_1, cols_2, in_order=True):
    """
    Create mirrored versions of a DataFrame by swapping paired columns.

    Parameters
    ----------
    df : pandas.DataFrame
        Input DataFrame to mirror.
    cols_1 : list-like
        Column names representing the first side of each pair.
    cols_2 : list-like
        Column names representing the second side of each pair. Each column
        is swapped with the corresponding column in `cols_1`.
    in_order : bool, default=True
        Determines the order of rows in the returned DataFrame. If True,
        each original row is immediately followed by its mirrored row.
        If False, all original rows are followed by all mirrored rows.

    Returns
    -------
    pandas.DataFrame
        DataFrame containing the original and mirrored rows.

    Notes
    -----
    The input DataFrame is copied and is not modified in place.
    """
    df = df.copy()
    df_original = df.copy()

    # Swap each pair of columns
    for c1, c2 in zip(cols_1, cols_2):
        temp = df[c1].copy()
        df[c1] = df[c2]
        df[c2] = temp

    if not in_order:
        return pd.concat([df_original, df], ignore_index=True)

    rows = []
    for r1, r2 in zip(df_original.itertuples(index=False), df.itertuples(index=False)):
        rows.append(r1)
        rows.append(r2)

    return pd.DataFrame(rows, columns=df.columns)

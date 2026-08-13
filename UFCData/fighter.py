import pandas as pd
import numpy as np
from datetime import date
from .ratings import get_elo, expected_score, update_rating

def _mirror_helper(df, cols_1, cols_2, in_order=True):
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


def get_fighter_history(fighter_link, fighter_bio, fights_df):
  """
    Retrieves the fight history of a UFC fighter.

    The returned DataFrame contains all fights involving the specified
    fighter, with the fighter consistently represented as "Fighter 1".
    The function also calculates the age of both fighters at the time
    of each fight and assigns a chronological UFC fight number.

    Parameters
    ----------
    fighter_link : str
        UFCStats link identifying the fighter whose history is being
        retrieved.
    fighter_bio : pandas.DataFrame
        DataFrame containing fighter information. Must contain
        "Fighter Link" and "DOB" columns.
    fights_df : pandas.DataFrame
        DataFrame containing UFC fight data. Must contain fighter links,
        fight dates, outcomes, and the other fight information required
        by the function.

    Returns
    -------
    pandas.DataFrame
        DataFrame containing the fighter's complete fight history.
        The requested fighter is represented as "Fighter 1" in every
        row. The DataFrame includes the ages of both fighters at the
        time of each fight and a "UFC Fight" column numbering the
        fighter's fights chronologically.

    Notes
    -----
    Fighter ages are calculated using 365.25 days per year. The
    "UFC Fight" column counts fights from the most recent fight
    backwards, with the most recent fight numbered 1.

    Examples
    --------
    >>> fighter_history = get_fighter_history(
    ...     fighter_link,
    ...     fighter_bio,
    ...     fights_df
    ... )
    >>> fighter_history[["Date", "UFC Fight", "Fighter 1",
    ...                   "Fighter 1 Age"]].head()

  """

  fighter_history = fights_df[
    (fights_df["Fighter 1 Link"] == fighter_link) |
    (fights_df["Fighter 2 Link"] == fighter_link)]

  fighter_history = _mirror_helper(fighter_history, ['Fighter 1', 'Fighter 1 Odds', 'Fighter 1 Link',
       'Fighter 1 Outcome', 'Fighter 1 Bonus'],['Fighter 2', 'Fighter 2 Odds',
       'Fighter 2 Link', 'Fighter 2 Outcome', 'Fighter 2 Bonus'])

  fighter_history = fighter_history[
    (fighter_history["Fighter 1 Link"] == fighter_link)]

  fighter_history = fighter_history.merge(
    fighter_bio[["Fighter Link", "DOB"]],
    left_on="Fighter 1 Link",
    right_on="Fighter Link",
    how="left")
  fighter_history = fighter_history.rename(columns={"DOB": "Fighter 1 Age"})
  fighter_history = fighter_history.drop(columns=["Fighter Link"])
  fighter_history["Fighter 1 Age"] = (pd.to_datetime(fighter_history["Date"]) - pd.to_datetime(fighter_history["Fighter 1 Age"])).dt.days / 365.25

  fighter_history = fighter_history.merge(
    fighter_bio[["Fighter Link", "DOB"]],
    left_on="Fighter 2 Link",
    right_on="Fighter Link",
    how="left")
  fighter_history = fighter_history.rename(columns={"DOB": "Fighter 2 Age"})
  fighter_history = fighter_history.drop(columns=["Fighter Link"])
  fighter_history["Fighter 2 Age"] = (pd.to_datetime(fighter_history["Date"]) - pd.to_datetime(fighter_history["Fighter 2 Age"])).dt.days / 365.25
  fighter_history["UFC Fight"] = range(len(fighter_history), 0, -1)
  fighter_history = fighter_history[['Date', "UFC Fight", 'Event Link', 'Fight Link', 'Weight Class',
       'Gender', 'Title', 'Fighter 1', 'Fighter 1 Odds', 'Fighter 1 Age', 'Fighter 1 Link',
       'Fighter 1 Outcome', 'Fighter 1 Bonus', 'Fighter 2', 'Fighter 2 Odds','Fighter 2 Age',
       'Fighter 2 Link', 'Fighter 2 Outcome', 'Fighter 2 Bonus', 'Method',
       'Round', 'Time', 'Time Format', 'Referee', 'Details']]

  return fighter_history



def get_fighter_statistic(fighter_link, fighter_bio, fights_df, rounds_df,
                          r=1500, k=30, s=400):
    
    """
    Generate historical and current statistics for a UFC fighter.

    The function retrieves the fighter's UFC fight history and constructs
    fight-level statistics from the fighter's perspective. It calculates
    the fighter's UFC record, win rate, Elo rating, cumulative fight time,
    striking statistics, takedown statistics, and submission averages using
    only information available before each fight.

    For fighters with no previous UFC fights, a baseline row is returned
    with an initial Elo rating and zero UFC wins, losses, draws, and
    no-contests. Historical performance statistics are left as NaN because
    no prior fight data is available.

    Parameters
    ----------
    fighter_link : str
        URL or unique identifier for the fighter.
    fighter_bio : pandas.DataFrame
        DataFrame containing fighter biographical information, including
        fighter names and links.
    fights_df : pandas.DataFrame
        DataFrame containing UFC fight-level results.
    rounds_df : pandas.DataFrame
        DataFrame containing round-level UFC statistics.
    r : float, default=1500
        Initial Elo rating assigned to fighters with no previous Elo history.
    k : float, default=30
        Elo update factor.
    s : float, default=400
        Elo scaling factor used when calculating expected scores.

    Returns
    -------
    current_statistic : pandas.DataFrame
        One-row DataFrame containing the fighter's statistics immediately
        before the upcoming fight. Historical statistics are calculated
        using only fights occurring before the upcoming fight date.

    past_statistic : pandas.DataFrame
        DataFrame containing the fighter's historical statistics for each
        previous UFC fight, with statistics calculated using only fights
        occurring before each respective fight.

    Notes
    -----
    The function calculates cumulative statistics rather than statistics
    from a single fight. This prevents information from a future fight from
    being used when generating features for an earlier fight.

    Historical statistics include:
        - UFC record and win rate
        - Elo rating
        - Total fight time
        - Significant strikes landed per minute (SLpM)
        - Significant strike accuracy and defense
        - Significant strikes absorbed per minute (SApM)
        - Takedown average, accuracy, and defense
        - Submission attempts per 15 minutes

    Fighters with no previous UFC fights receive an initial Elo rating of
    `r`, while statistics requiring historical fight data are set to NaN.
    """

    record = get_fighter_history(fighter_link, fighter_bio, fights_df)

    date = ("2201-01-01")

    if len(record) == 0:
        columns = [
            'Date', 'UFC Fight', 'Weight Class', 'Gender', 'Title', 'Fighter',
            'Fighter Link', 'Fighter Outcome', 'UFC W', 'UFC L', 'UFC D', 'UFC NC',
            'UFC Win Rate', 'Fighter Elo',
            'Fight Time', 'SLpM', 'Str Acc', 'SApM',
            'Str Def', 'TD Avg', 'TD Acc', 'TD Def', 'Sub Avg'
        ]

        fighter_name = fighter_bio.loc[
            fighter_bio["Fighter Link"] == fighter_link,
            "Name"
        ].iloc[0]

        df = pd.DataFrame([{
            "Date": date,
            "UFC Fight": 1,
            "Weight Class": None,
            "Gender": None,
            "Title": None,
            "Fighter": fighter_name,
            "Fighter Link": fighter_link,
            "Fighter Outcome": None,
            "UFC W": 0,
            "UFC L": 0,
            "UFC D": 0,
            "UFC NC": 0,
            "UFC Win Rate": None,
            "Fighter Elo": r,
            "Fight Time": None,
            "SLpM": None,
            "Str Acc": None,
            "SApM": None,
            "Str Def": None,
            "TD Avg": None,
            "TD Acc": None,
            "TD Def": None,
            "Sub Avg": None
        }], columns=columns)

        df = df.astype(object).where(pd.notna(df), np.nan)

        df["UFC Fight"] = df["UFC Fight"].astype("Int64")
        df[["UFC W", "UFC L", "UFC D", "UFC NC"]] = (
            df[["UFC W", "UFC L", "UFC D", "UFC NC"]].astype("Int64")
        )
        df.iloc[0, 0] = np.nan

        return (df, df)

    statistic = record[
        ['Date', 'UFC Fight', 'Weight Class',
         'Gender', 'Title', 'Fighter 1',
         'Fighter 1 Link', 'Fighter 1 Outcome']
    ].copy()

    cols = [
        "Date", "UFC Fight", "Weight Class", "Gender",
        "Title", "Fighter 1", "Fighter 1 Link",
        "Fighter 1 Outcome"
    ]

    statistic[cols] = statistic[cols].iloc[::-1].to_numpy()

    last = statistic.iloc[-1]
    new_row = last.copy()
    new_row[:] = pd.NA

    new_row["Date"] = date
    new_row["UFC Fight"] = last["UFC Fight"] + 1
    new_row["Gender"] = last["Gender"]
    new_row["Fighter 1"] = last["Fighter 1"]
    new_row["Fighter 1 Link"] = last["Fighter 1 Link"]

    statistic = pd.concat(
        [statistic, new_row.to_frame().T],
        ignore_index=True
    )

    statistic["Date"] = pd.to_datetime(statistic["Date"]).dt.date

    statistic["UFC W"] = 0
    statistic["UFC L"] = 0
    statistic["UFC D"] = 0
    statistic["UFC NC"] = 0

    for i in range(1, len(statistic)):

        # Carry forward previous totals
        statistic.loc[i, "UFC W"] = statistic.loc[i-1, "UFC W"]
        statistic.loc[i, "UFC L"] = statistic.loc[i-1, "UFC L"]
        statistic.loc[i, "UFC D"] = statistic.loc[i-1, "UFC D"]
        statistic.loc[i, "UFC NC"] = statistic.loc[i-1, "UFC NC"]

        # Update based on previous fight result
        result = statistic.loc[i-1, "Fighter 1 Outcome"]

        if result == "W":
            statistic.loc[i, "UFC W"] += 1
        elif result == "L":
            statistic.loc[i, "UFC L"] += 1
        elif result == "D":
            statistic.loc[i, "UFC D"] += 1
        elif result == "NC":
            statistic.loc[i, "UFC NC"] += 1

    statistic = statistic[::-1]

    statistic[
        ["UFC W", "UFC L", "UFC D", "UFC NC"]
    ] = (
        statistic[
            ["UFC W", "UFC L", "UFC D", "UFC NC"]
        ].iloc[::-1].reset_index(drop=True)
    )

    statistic["UFC Win Rate"] = (
        statistic["UFC W"] /
        (
            statistic["UFC L"]
            + statistic["UFC D"]
            + statistic["UFC NC"]
            + statistic["UFC W"]
        )
    )

    # Elo
    current_elo,elo = get_elo(fights_df, fighter_bio, r, k, s)

    elo = elo[
        (elo["Fighter 1 Link"] == fighter_link) |
        (elo["Fighter 2 Link"] == fighter_link)
    ]

    elo = elo[
        [
            "Fighter 1", "Fighter 1 Elo", "Fighter 1 Outcome",
            "Fighter 1 Link",
            "Fighter 2", "Fighter 2 Elo", "Fighter 2 Outcome",
            "Fighter 2 Link"
        ]
    ]

    elo = _mirror_helper(
        elo,
        [
            "Fighter 1", "Fighter 1 Elo",
            "Fighter 1 Outcome", "Fighter 1 Link"
        ],
        [
            "Fighter 2", "Fighter 2 Elo",
            "Fighter 2 Outcome", "Fighter 2 Link"
        ]
    )

    elo = elo[
        elo["Fighter 1 Link"] == fighter_link
    ]

    elo = elo.reset_index(drop=True)

    new_row = pd.DataFrame(
        [[np.nan] * len(elo.columns)],
        columns=elo.columns
    )

    elo = pd.concat(
        [new_row, elo],
        ignore_index=True
    )

    fighter_elo = elo.at[1, "Fighter 1 Elo"]
    opponent_elo = elo.at[1, "Fighter 2 Elo"]
    fighter_outcome = elo.at[1, "Fighter 1 Outcome"]

    if fighter_outcome == "W":
        expected_1 = expected_score(
            fighter_elo,
            opponent_elo,
            s
        )

        elo_1_new = update_rating(
            fighter_elo,
            k,
            1,
            expected_1
        )

        elo.at[0, "Fighter 1 Elo"] = elo_1_new

    elif fighter_outcome == "L":
        expected_1 = expected_score(
            fighter_elo,
            opponent_elo,
            s
        )

        elo_1_new = update_rating(
            fighter_elo,
            k,
            0,
            expected_1
        )

        elo.at[0, "Fighter 1 Elo"] = elo_1_new

    elif fighter_outcome == "D":
        expected_1 = expected_score(
            fighter_elo,
            opponent_elo,
            s
        )

        elo_1_new = update_rating(
            fighter_elo,
            k,
            0.5,
            expected_1
        )

        elo.at[0, "Fighter 1 Elo"] = elo_1_new

    elif fighter_outcome == "NC":
        elo.at[0, "Fighter 1 Elo"] = fighter_elo

    elo = elo["Fighter 1 Elo"]
    elo = elo.iloc[::-1].reset_index(drop=True)

    statistic = pd.concat(
        [statistic, elo],
        axis=1
    )

    # Get fight statistics
    fight_time = get_fighter_history(
        fighter_link,
        fighter_bio,
        fights_df
    )

    fight_time["new_time"] = fight_time["Time"].apply(
        lambda x: int(x.split(":")[0]) * 60
        + int(x.split(":")[1])
    )

    fight_time["new_round"] = (
        (fight_time["Round"] - 1) * 60 * 5
    )

    fight_time["Fight Time"] = (
        fight_time["new_time"]
        + fight_time["new_round"]
    ) / 60

    statistic["Fight Time"] = statistic["Date"].apply(
        lambda d: fight_time.loc[
            fight_time["Date"].dt.date < d,
            "Fight Time"
        ].sum()
    )

    rounds = rounds_df

    rounds = rounds[
        (rounds["Fighter 1 Link"] == fighter_link) |
        (rounds["Fighter 2 Link"] == fighter_link)
    ]

    rounds = _mirror_helper(
        rounds,
        [
            "Fighter 1", "Fighter 1 Link",
            "Fighter 1 TD", "Fighter 1 Sub Att",
            "Fighter 1 Rev", "Fighter 1 Ctrl",
            "Fighter 1 KD", "Fighter 1 Total SS"
        ],
        [
            "Fighter 2", "Fighter 2 Link",
            "Fighter 2 TD", "Fighter 2 Sub Att",
            "Fighter 2 Rev", "Fighter 2 Ctrl",
            "Fighter 2 KD", "Fighter 2 Total SS"
        ]
    )

    rounds = rounds[
        rounds["Fighter 1 Link"] == fighter_link
    ]

    rounds["Sig landed"] = (
        rounds["Fighter 1 Total SS"]
        .str.split()
        .str[0]
        .astype(int)
    )

    rounds["Sig att"] = (
        rounds["Fighter 1 Total SS"]
        .str.split()
        .str[2]
        .astype(int)
    )

    rounds["Strike acc"] = (
        rounds["Sig landed"] / rounds["Sig att"]
    )

    rounds["Strikes absorbed"] = (
        rounds["Fighter 2 Total SS"]
        .str.split()
        .str[0]
        .astype(int)
    )

    rounds["Opp sig att"] = (
        rounds["Fighter 2 Total SS"]
        .str.split()
        .str[2]
        .astype(int)
    )

    statistic["SLpM"] = statistic["Date"].apply(
        lambda d: rounds.loc[
            rounds["Date"].dt.date < d,
            "Sig landed"
        ].sum()
    )

    statistic["SLpM"] = (
        statistic["SLpM"] / statistic["Fight Time"]
    )

    statistic["Sig landed"] = statistic["Date"].apply(
        lambda d: rounds.loc[
            rounds["Date"].dt.date < d,
            "Sig landed"
        ].sum()
    )

    statistic["Sig att"] = statistic["Date"].apply(
        lambda d: rounds.loc[
            rounds["Date"].dt.date < d,
            "Sig att"
        ].sum()
    )

    statistic["Str Acc"] = (
        statistic["Sig landed"] /
        statistic["Sig att"]
    )

    statistic["SApM"] = statistic["Date"].apply(
        lambda d: rounds.loc[
            rounds["Date"].dt.date < d,
            "Strikes absorbed"
        ].sum()
    )

    statistic["SApM"] = (
        statistic["SApM"] / statistic["Fight Time"]
    )

    statistic["Strikes absorbed"] = statistic["Date"].apply(
        lambda d: rounds.loc[
            rounds["Date"].dt.date < d,
            "Strikes absorbed"
        ].sum()
    )

    statistic["Opp sig att"] = statistic["Date"].apply(
        lambda d: rounds.loc[
            rounds["Date"].dt.date < d,
            "Opp sig att"
        ].sum()
    )

    statistic["Str Def"] = 1 - (
        statistic["Strikes absorbed"] /
        statistic["Opp sig att"]
    )

    rounds["Td"] = (
        rounds["Fighter 1 TD"]
        .str.split()
        .str[0]
        .astype(int)
    )

    rounds["TD landed"] = (
        rounds["Fighter 1 TD"]
        .str.split()
        .str[0]
        .astype(int)
    )

    rounds["TD att"] = (
        rounds["Fighter 1 TD"]
        .str.split()
        .str[2]
        .astype(int)
    )

    rounds["TD absorbed"] = (
        rounds["Fighter 2 TD"]
        .str.split()
        .str[0]
        .astype(int)
    )

    rounds["Opp TD att"] = (
        rounds["Fighter 2 TD"]
        .str.split()
        .str[2]
        .astype(int)
    )

    rounds["Sub att"] = rounds["Fighter 1 Sub Att"]

    statistic["TD Avg"] = statistic["Date"].apply(
        lambda d: rounds.loc[
            rounds["Date"].dt.date < d,
            "Td"
        ].sum()
    )

    statistic["TD Avg"] = (
        statistic["TD Avg"] /
        statistic["Fight Time"] * 15
    )

    statistic["TD landed"] = statistic["Date"].apply(
        lambda d: rounds.loc[
            rounds["Date"].dt.date < d,
            "TD landed"
        ].sum()
    )

    statistic["TD att"] = statistic["Date"].apply(
        lambda d: rounds.loc[
            rounds["Date"].dt.date < d,
            "TD att"
        ].sum()
    )

    statistic["TD absorbed"] = statistic["Date"].apply(
        lambda d: rounds.loc[
            rounds["Date"].dt.date < d,
            "TD absorbed"
        ].sum()
    )

    statistic["Opp TD att"] = statistic["Date"].apply(
        lambda d: rounds.loc[
            rounds["Date"].dt.date < d,
            "Opp TD att"
        ].sum()
    )

    statistic["TD Acc"] = np.where(
        statistic["TD att"] > 0,
        statistic["TD landed"] /
        statistic["TD att"],
        np.nan
    )

    statistic["TD Def"] = np.where(
        statistic["Opp TD att"] > 0,
        1 - (
            statistic["TD absorbed"] /
            statistic["Opp TD att"]
        ),
        np.nan
    )

    statistic["Sub Avg"] = statistic["Date"].apply(
        lambda d: rounds.loc[
            rounds["Date"].dt.date < d,
            "Sub att"
        ].sum()
    )

    statistic["Sub Avg"] = (
        statistic["Sub Avg"] /
        statistic["Fight Time"] * 15
    )

    statistic = statistic.drop(
        columns=[
            "Sig landed",
            "Sig att",
            "Strikes absorbed",
            "Opp sig att",
            "TD landed",
            "TD att",
            "TD absorbed",
            "Opp TD att"
        ]
    )

    statistic.columns = statistic.columns.str.replace(
        "Fighter 1",
        "Fighter",
        regex=False
    )

    statistic = statistic.reset_index(drop=True)

    current_statistic = statistic.iloc[[0]].copy()
    current_statistic["Date"] = np.nan
    past_statistic = statistic.iloc[1:].reset_index(drop=True)

    return (current_statistic, past_statistic)

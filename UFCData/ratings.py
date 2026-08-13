import pandas as pd
from glicko2 import Player

#@title Elo function
def expected_score(rating, opponent_rating, s):
  return (1)/(1 + 10**((opponent_rating - rating)/(s)))

#Rating update
def update_rating(rating, k, outcome, expected):
  return rating + k*(outcome - expected)

# Elo function
#  Make sure fights are sorted from most recent to least recent. Gets Elo prior to fight.
def get_elo(fight_df, fighter_df, r=1500, k=30, s=400):
  """
    Calculates pre-fight Elo ratings for UFC fighters.

    Fights are processed chronologically from oldest to newest, with
    each fighter's Elo rating recorded immediately before each fight.
    Fighter ratings are initialized to `r` and updated after each fight
    using the specified K-factor and Elo scale.

    Parameters
    ----------
    fight_df : pandas.DataFrame
        UFC fight data sorted from most recent to least recent.
        Must contain fighter links, fight outcomes, and the fight
        information required to construct the output.
    fighter_df : pandas.DataFrame
        DataFrame containing fighter information. Must contain a
        "Fighter Link" column used to identify each fighter.
    r : float, default=1500
        Initial Elo rating assigned to each fighter.
    k : float, default=30
        K-factor controlling the magnitude of Elo rating changes
        after each fight.
    s : float, default=400
        Elo scaling factor used when calculating expected scores.

    Returns
    -------
    current_elo : dict
        Dictionary mapping each fighter's link to their current Elo rating
        after processing all fights.

    past_elo : pandas.DataFrame
        Fight-level DataFrame containing the original fight information
        and the Elo rating of each fighter immediately before the fight.

    Notes
    -----
    The input fight data should be sorted from most recent to least
    recent. The function reverses this order internally to process
    fights chronologically, then returns the resulting data in the
    original order.

    Examples
    --------
    >>> fighter_elo, fight_elo = get_elo(fight_df, fighter_df)
    >>> fight_elo[["Fighter 1", "Fighter 1 Elo",
    ...            "Fighter 2", "Fighter 2 Elo"]].head()
  """

  fight_df = fight_df[::-1]

  original_fight_df = fight_df.copy()

  fighter_1_elo = []
  fighter_2_elo = []

  ## Create a dictionary of fighters and their Elo
  fighter_df = fighter_df.copy()
  fighter_df["Elo"] = r
  fighter_df = dict(zip(fighter_df["Fighter Link"], fighter_df["Elo"]))

  ## Create a list of fights
  fight_df = fight_df[["Fighter 1 Link", "Fighter 1 Outcome", "Fighter 2 Link", "Fighter 2 Outcome"]]
  fight_df = fight_df.values.tolist()


  ## Loop through each fight in order
  for fight in fight_df:
    ## Get fighters Elo from fighter_df
    elo_1 = fighter_df[fight[0]]
    elo_2 = fighter_df[fight[2]]
    ## Add to final list
    fighter_1_elo.append(elo_1)
    fighter_2_elo.append(elo_2)
    ## Update Elo
    if (fight[1] == "W") and ((fight[3] == "L")):
      expected_1 = expected_score(elo_1, elo_2, s)
      elo_1_new = update_rating(elo_1, k, 1, expected_1)
      expected_2 = expected_score(elo_2, elo_1, s)
      elo_2_new = update_rating(elo_2, k, 0, expected_2)
      fighter_df[fight[0]] = elo_1_new
      fighter_df[fight[2]] = elo_2_new
    elif (fight[1] == "L") and (fight[3] == "W"):
      expected_1 = expected_score(elo_1, elo_2, s)
      elo_1_new = update_rating(elo_1, k, 0, expected_1)
      expected_2 = expected_score(elo_2, elo_1, s)
      elo_2_new = update_rating(elo_2, k, 1, expected_2)
      fighter_df[fight[0]] = elo_1_new
      fighter_df[fight[2]] = elo_2_new
    elif (fight[1] == "D") and (fight[3] == "D"):
      expected_1 = expected_score(elo_1, elo_2, s)
      elo_1_new = update_rating(elo_1, k, 0.5, expected_1)
      expected_2 = expected_score(elo_2, elo_1, s)
      elo_2_new = update_rating(elo_2, k, 0.5, expected_2)
      fighter_df[fight[0]] = elo_1_new
      fighter_df[fight[2]] = elo_2_new


  elo_1 = pd.DataFrame(fighter_1_elo, columns=["Fighter 1 Elo"])
  elo_2 = pd.DataFrame(fighter_2_elo, columns=["Fighter 2 Elo"])
  elo = pd.concat(
    [
        original_fight_df.reset_index(drop=True),
        elo_1.reset_index(drop=True),
        elo_2.reset_index(drop=True)
    ],
    axis=1
  )
  elo = elo[['Date', 'Event Link', 'Fight Number', 'Fight Link', 'Weight Class',
       'Gender', 'Title', 'Fighter 1', 'Fighter 1 Elo', 'Fighter 1 Odds', 'Fighter 1 Link',
       'Fighter 1 Outcome', 'Fighter 1 Bonus', 'Fighter 2','Fighter 2 Elo', 'Fighter 2 Odds',
       'Fighter 2 Link', 'Fighter 2 Outcome', 'Fighter 2 Bonus', 'Method',
       'Round', 'Time', 'Time Format', 'Referee', 'Details']]
  past_elo = elo[::-1].copy()
  current_elo = fighter_df
  return (current_elo, past_elo)
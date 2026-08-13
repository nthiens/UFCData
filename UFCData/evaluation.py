import numpy as np
import matplotlib.pyplot as plt

def train_test_split(fights_df, test_size=0.2):
  """
    Split a UFC fight DataFrame into chronological training and test sets.

    The input DataFrame must be ordered from the newest fight to the oldest
    fight. The most recent fights are assigned to the test set, while the
    remaining older fights are assigned to the training set. Both returned
    DataFrames are reversed so that they are ordered from oldest to newest.

    Parameters
    ----------
    fights_df : pandas.DataFrame
        UFC fight DataFrame ordered from newest to oldest.
    test_size : float or int, default=0.2
        Determines the size of the test set. If less than 1, it is interpreted
        as a proportion of the total number of fights. If greater than or
        equal to 1, it is interpreted as the exact number of fights to include
        in the test set.

    Returns
    -------
    tuple of pandas.DataFrame
        A tuple containing:

        - train : pandas.DataFrame
            Training data consisting of the older fights, ordered from
            oldest to newest.
        - test : pandas.DataFrame
            Test data consisting of the most recent fights, ordered from
            oldest to newest.
  """
  fights_df = fights_df.copy()

  fights_df["Winner"] = np.select(
    [
        fights_df["Fighter 1 Outcome"] == "W",
        fights_df["Fighter 2 Outcome"] == "W"
    ],
    [
        fights_df["Fighter 1 Link"],
        fights_df["Fighter 2 Link"]
    ],
    default=None
  )

  if test_size < 1:
    n_test = int(len(fights_df) * test_size)
  else:
    n_test = test_size

  test = fights_df[:n_test]
  train = fights_df[n_test:]

  test = test.iloc[::-1].reset_index(drop=True)
  train = train.iloc[::-1].reset_index(drop=True)

  return (train, test)

def get_expanding_window(fights_df, folds, test_size):
    """
    Create expanding training windows with fixed-size test sets for
    time-series cross-validation.

    Parameters
    ----------
    fights_df : pandas.DataFrame
        UFC fight DataFrame ordered chronologically from oldest to newest.
    folds : int
        Number of train/test folds to create.
    test_size : int
        Number of fights included in each test set.

    Returns
    -------
    dict
        Dictionary containing the training and test DataFrames for each fold.
        Each fold is stored using the key ``"Fold 1"``, ``"Fold 2"``, etc.,
        with the following structure:

        {
            "train": train_dataframe,
            "test": test_dataframe
        }

    Notes
    -----
    The training window expands with each fold while the test window remains
    fixed at `test_size` rows.

    For example, the folds follow the structure:

        Fold 1: [Train] [Test]
        Fold 2: [------ Train ------] [Test]
        Fold 3: [------------ Train ------------] [Test]

    This approach is suitable for time-series cross-validation because each
    training set only contains observations that occur before its
    corresponding test set.
    """
    fold_results = {}

    train_sizes = np.linspace(
        test_size,
        len(fights_df) - test_size,
        folds,
        dtype=int
    )

    for i, train_size in enumerate(train_sizes, start=1):
        train = fights_df.iloc[:train_size].reset_index(drop=True)
        test = fights_df.iloc[train_size:train_size + test_size].reset_index(drop=True)

        fold_results[f"Fold {i}"] = {
            "train": train,
            "test": test
        }

    return fold_results

def plot_cv(cv_labels, cv_accuracies, title="Cross Validation Accuracy"):
    plt.figure(figsize=(10, 5))

    plt.plot(
        cv_labels,
        cv_accuracies,
        color="#666666",
        linestyle="-",
        linewidth=2,
        marker="o",
        markersize=7,
        markerfacecolor="#D20A0A",  # UFC red dots
        markeredgecolor="#FFFFFF",
        markeredgewidth=1.5,
        label="Fold Accuracy"
    )


    # Mean accuracy across folds
    mean_accuracy = np.mean(cv_accuracies)

    plt.axhline(
        mean_accuracy,
        color="#D20A0A",
        linestyle="--",
        linewidth=2,
        label=f"Mean Accuracy: {mean_accuracy:.1%}"
    )


    plt.xlabel("Fold")
    plt.ylabel("Accuracy")
    plt.title(title)
    # plt.ylim(0, 1)

    plt.xticks(rotation=45)
    plt.grid(True, alpha=0.3)
    plt.legend()

    plt.tight_layout()
    plt.show()

def plot_test(accuracy, title="Test Accuracy"):
    plt.figure(figsize=(6, 5))

    plt.bar(
        0,
        accuracy,
        color="#D20A0A",
        width=0.25
    )

    plt.ylabel("Accuracy")
    plt.title(title)
    plt.ylim(0, 1)

    plt.xlim(-0.5, 0.5)
    plt.xticks([0], ["Test Set"])

    plt.text(
        0,
        accuracy + 0.02,
        f"{accuracy:.1%}",
        ha="center",
        fontweight="bold",
        color="#444444"
    )

    plt.tight_layout()
    plt.show()
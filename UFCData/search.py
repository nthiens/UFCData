from rapidfuzz.fuzz import ratio
import pandas as pd

def search(data, column , query, matches=1):
    """
    Searches a UFC dataset for rows matching a query.

    The dataset is loaded as a CSV file from the JunoML/MMA Hugging Face
    repository. Fuzzy string matching is used to identify the rows in the
    specified column that most closely match the query.

    Parameters
    ----------
    data : str
        Name of the CSV dataset to search, without the .csv extension.
        For example, "fighter_bio".
    column : str
        Name of the column to search.
    query : str
        Search query to match against the specified column.
    matches : int, default=1
        Number of closest matches to return.

    Returns
    -------
    pandas.DataFrame
        DataFrame containing the closest matching rows, sorted from
        highest to lowest similarity. The index is reset.

    Examples
    --------
    >>> results = search("fighter_bio", "Name", "John Jones", 1)
    >>> print(results)
    """

    url = f"https://huggingface.co/datasets/JunoML/MMA/resolve/main/{data}.csv"
    df = pd.read_csv(url)

    scores = df[column].fillna("").apply(
    lambda x: ratio(str(x), query))

    result = df.loc[scores.nlargest(matches).index].copy()
    result["score"] = scores.loc[result.index]
    result = result.sort_values("score", ascending=False).drop(columns="score")

    return result.reset_index(drop=True)

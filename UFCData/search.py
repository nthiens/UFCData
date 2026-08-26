from rapidfuzz.fuzz import ratio

def search(data, column , query, matches=1):
    """
    Searches a UFC DataFrame for rows matching a query.

    Uses fuzzy string matching to identify the rows in the specified
    column that most closely match the query.

    Parameters
    ----------
    data : pandas.DataFrame
        UFC DataFrame to search.
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
        highest to lowest similarity.

    Examples
    --------
    >>> data = get_data()
    >>> results = search(data["fighters"], "Name", "Jon Jones")
    """
    scores = data[column].fillna("").apply(
    lambda x: ratio(str(x), query))

    result = data.loc[scores.nlargest(matches).index].copy()
    result["score"] = scores.loc[result.index]
    result = result.sort_values("score", ascending=False).drop(columns="score")

    return result
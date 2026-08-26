from huggingface_hub import hf_hub_download
import pickle
import logging

def get_data():
    """
    Obtains all UFC related data

    Returns
    dict
        Dictionary containing UFC data as pandas DataFrames.
        Individual DataFrames can be accessed using their
        corresponding dictionary keys.

    Examples
    --------
    >>> data = get_data()
    >>> past_events = data["past_events"].copy()
    """

    logging.getLogger("huggingface_hub").setLevel(logging.ERROR)
    
    file = hf_hub_download(
    repo_id="JunoML/MMA",
    filename="ufc_data.pkl",
    repo_type="dataset")

    with open(file, "rb") as f:
        ufc_data = pickle.load(f)

    keys = list(ufc_data.keys())
    print("Data Obtained")
    print()
    print('To access a specific dataframe, use its corresponding key below')
    print(keys)
    print()
    print("For example:")
    print("data = get_data()")
    print("past_events = data['past_events'].copy()")

    return ufc_data

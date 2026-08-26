from events import get_past_events, get_future_events
from fighters import get_fighter_bio
from fights import get_past_fights, get_future_fights
from rounds import get_rounds
import asyncio
from datetime import datetime
from zoneinfo import ZoneInfo
import pandas as pd
import pickle
from huggingface_hub import upload_file

## Get past_events
past_events = asyncio.run(get_past_events())
past_events.to_csv(
    "scraper/scraper_data/past_events.csv",
    index=False
)
print("Done past_events")

## Get future_events
future_events = asyncio.run(get_future_events())
future_events.to_csv(
    "scraper/scraper_data/future_events.csv",
    index=False
)
print("Done future_events")

## Get fighter_bio
# fighter_bio = asyncio.run(get_fighter_bio())
# fighter_bio.to_csv(
#     "scraper/scraper_data/fighter_bio.csv",
#     index=False
# )
print("Done fighter_bio")
fighter_bio = pd.read_csv("scraper/scraper_data/fighter_bio.csv")

# Get past_fights
# past_fights = asyncio.run(get_past_fights())
# past_fights.to_csv(
#     "scraper/scraper_data/past_fights.csv",
#     index=False
# )
print("Done past_fights")
past_fights = pd.read_csv("scraper/scraper_data/past_fights.csv")

# Get future_fights
# future_fights = asyncio.run(get_future_fights())
# future_fights.to_csv(
#     "scraper/scraper_data/future_fights.csv",
#     index=False
# )
future_fights = pd.read_csv("scraper/scraper_data/future_fights.csv")
print("Done future_fights")

## Get rounds
rounds = asyncio.run(get_rounds())
rounds.to_csv(
    "scraper/scraper_data/rounds.csv",
    index=False
)
print("Done rounds")

## Package data into a dictionary
ufc_data = {
    "Last Updated": (datetime.now(ZoneInfo("America/New_York"))
                     .strftime("%Y-%m-%d %H:%M:%S %Z")),
    "past_events": past_events,
    "future_events": future_events,
    "fighter_bio": fighter_bio,
    "past_fights": past_fights,
    "future_fights": future_fights,
    "rounds": rounds
}

with open("ufc_data.pkl", "wb") as f:
    pickle.dump(ufc_data, f)

upload_file(
    path_or_fileobj="ufc_data.pkl",
    path_in_repo="ufc_data.pkl",
    repo_id="JunoML/MMA",
    repo_type="dataset"
)

print("Initial scrape complete!")
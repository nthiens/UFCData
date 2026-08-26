from events import get_past_events, get_future_events
from fighters import update_fighter_bio
from fights import update_past_fights, get_future_fights
from rounds import update_rounds
import asyncio
from datetime import datetime
from zoneinfo import ZoneInfo
import pickle
from huggingface_hub import upload_file

## Update past_events
past_events = asyncio.run(get_past_events())
past_events.to_csv("scraper/scraper_data/past_events.csv",index=False)
print("Updated past_events")

## Update future_events
future_events = asyncio.run(get_future_events())
future_events.to_csv("scraper/scraper_data/future_events.csv",index=False)
print("Updated future_events")

## Update fighter_bio
fighter_bio = asyncio.run(update_fighter_bio())
fighter_bio.to_csv("scraper/scraper_data/fighter_bio.csv",index=False)
print("Updated fighter_bio")

## Update past_fights
past_fights = asyncio.run(update_past_fights())
past_fights.to_csv("scraper/scraper_data/past_fights.csv",index=False)
print("Updated past_fights")

# Update future_fights
future_fights = asyncio.run(get_future_fights())
future_fights.to_csv("scraper/scraper_data/future_fights.csv",index=False)
print("Updated future_fights")

# Update rounds
rounds = asyncio.run(update_rounds())
rounds.to_csv("scraper/scraper_data/rounds.csv",index=False)
print("Updated rounds")

# Package data into a dictionary
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

# Convert dictionary into pickle file
with open("ufc_data.pkl", "wb") as f:
    pickle.dump(ufc_data, f)

# Upload pickle file to HuggingFace
upload_file(
    path_or_fileobj="ufc_data.pkl",
    path_in_repo="ufc_data.pkl",
    repo_id="JunoML/MMA",
    repo_type="dataset"
)

# Upload CSV files to HuggingFace
csv_files = ["past_events.csv", "future_events.csv", "fighter_bio.csv",
             "past_fights.csv", "future_fights.csv", "rounds.csv"]

for csv_file in csv_files:
    upload_file(
        path_or_fileobj=f"scraper/scraper_data/{csv_file}",
        path_in_repo=csv_file,
        repo_id="JunoML/MMA",
        repo_type="dataset"
    )

print("Update complete!")

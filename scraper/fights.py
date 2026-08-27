from bs4 import BeautifulSoup
import pandas as pd
import asyncio
import pandas as pd
from playwright.async_api import async_playwright
from tqdm.asyncio import tqdm_asyncio
import numpy as np
from huggingface_hub import hf_hub_download
import pickle
from datetime import datetime
import re
import random
from tqdm import tqdm
import os
from rapidfuzz import process, fuzz
from rapidfuzz.fuzz import ratio
from rapidfuzz.fuzz import WRatio
from rapidfuzz.fuzz import token_sort_ratio


## Gets all events from Tapology
async def tapology_events(update=False):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()

        ## Open the UFC promotion page to find last page number
        url = (
            "https://www.tapology.com/fightcenter/"
            "promotions/1-ultimate-fighting-championship-ufc"
        )

        await page.goto(url, wait_until="domcontentloaded")

        href = await page.locator(".last a").first.get_attribute("href")
        max_page = int(re.search(r"\d+$", href).group())

        ## During an update, only scrape the first page
        if update == True:
            max_page = 1

        ## Base URL used to iterate through all Tapology event pages
        base_url = (
            "https://www.tapology.com/fightcenter/promotions/"
            "1-ultimate-fighting-championship-ufc?page="
        )

        results = []

        ## Scrape each page of UFC events
        for page_num in range(1, max_page + 1):
            delay = random.uniform(3, 7)
            await asyncio.sleep(delay)
            url = base_url + str(page_num)
            await page.goto(url, wait_until="domcontentloaded")
            await asyncio.sleep(random.uniform(1, 3))

            soup = BeautifulSoup(
                await page.content(),
                "html.parser"
            )

            promotions = soup.select(
                "div.promotion.flex.flex-wrap.items-center."
                "leading-6.whitespace-nowrap.overflow-hidden"
            )

            for promotion in promotions:
                link = promotion.select_one(
                    "a.border-b.border-tap_3.border-dotted."
                    "hover\\:border-solid"
                )

                hidden_elements = promotion.select(
                    ".hidden.md\\:inline"
                )

                second_hidden = (
                    hidden_elements[1]
                    if len(hidden_elements) > 1
                    else None
                )

                results.append({
                    "Event Link": link.get("href") if link else None,
                    "Event": (
                        link.get_text(" ", strip=True)
                        if link else None
                    ),
                    "Date": (
                        second_hidden.get_text(" ", strip=True)
                        if second_hidden else None
                    ),
                })

        df = pd.DataFrame(results)
        df = df[["Date", "Event Link", "Event"]]
        df["Event Link"] = "https://www.tapology.com" + df["Event Link"]
        df["Date"] = (
            df["Date"]
            .str.replace(
                r"\b(?:Monday, |Tuesday, |Wednesday,|Thursday, |Friday, |Saturday, |Sunday, )\b",
                "",
                regex=True
            )
            .str.replace(r"\s+", " ", regex=True)
            .str.strip()
        )
        await browser.close()
        df["Date"] = df["Date"].str.replace(
            r",\s*\d{1,2}:\d{2}\s*(?:AM|PM)\s*\w+$",
            "",
            regex=True
        )

        current_year = datetime.now().year

        df["Date"] = df["Date"].apply(
            lambda x: (
                f"{x}, {current_year}"
                if len(x.split(",")) == 1
                else x
            )
        )

        df["Date"] = pd.to_datetime(
            df["Date"],
            format="mixed"
        )

        df_tap = df.copy()
        df_tap["Date"] = pd.to_datetime(df_tap["Date"])

        file = hf_hub_download(
            repo_id="JunoML/MMA",
            filename="ufc_data.pkl",
            repo_type="dataset"
        )

        with open(file, "rb") as f:
            ufc_data = pickle.load(f)
        df_ufc = ufc_data["past_events"]

        df_ufc["Date"] = pd.to_datetime(df_ufc["Date"])
        df_tap["Date"] = pd.to_datetime(df_tap["Date"])

        df_ufc["_occurrence"] = df_ufc.groupby("Date").cumcount()
        df_tap["_occurrence"] = df_tap.groupby("Date").cumcount()

        df = df_ufc.merge(
            df_tap,
            on=["Date", "_occurrence"],
            how="left",
            suffixes=("_ufc", "_tap")
        )

        df = df.drop(columns="_occurrence")
        df.columns = [
            "Date",
            "Event Link",
            "Event",
            "Location",
            "Venue",
            "Attendance",
            "Tapology Link",
            "Tapology Event"
        ]

        return df

## Gets all odds and time format from Tapology
async def tapology_fight_odds(df):
    all_fights = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()

        ## Process each Tapology event

        for _, row in tqdm(df.iterrows(), total=len(df), desc="Processing Tapology"):
            link = row.iloc[-1]
            await asyncio.sleep(random.uniform(3, 7))

            await page.goto(link, wait_until="domcontentloaded")
            await asyncio.sleep(random.uniform(1, 3))

            fights = page.locator("li.border-b.border-dotted.border-tap_6")

            for i in range(await fights.count()):
                item = fights.nth(i)

                fighter = item.locator(".link-primary-red")
                odds = item.locator("div.hidden.md\\:inline")
                time_format = item.locator("div.text-xs11")

                all_fights.append({
                    "Fighter 1": (await fighter.nth(0).inner_text()).strip(),
                    "Fighter 2": (await fighter.nth(2).inner_text()).strip(),
                    "Fighter 1 Odds": (await odds.nth(0).inner_text()).strip(),
                    "Fighter 2 Odds": (await odds.nth(1).inner_text()).strip(),
                    "Tapology Link": link,
                    "Time Format": await time_format.nth(1).inner_text(),
                })

        await browser.close()

    all_fights = pd.DataFrame(all_fights)
    return all_fights

## Helper function for ufc_stats_1
async def ufc_stats_helper_1(page, event_url):

    attempt = 0

    ## Continue retrying until the page successfully loads

    while True:
        attempt += 1

        try:
            await page.goto(event_url, wait_until="domcontentloaded")

            await page.wait_for_selector(
                "table.b-fight-details__table tbody tr",
                timeout=15000
            )

            rows = page.locator(
                "table.b-fight-details__table tbody tr"
            )

            records = []

            for i in range(await rows.count()):
                row = rows.nth(i)

                fight_link = await row.get_attribute("data-link")

                weight_class = await row.locator(
                    "td:nth-child(7) p"
                ).first.text_content()

                weight_class = (
                    weight_class.strip()
                    if weight_class
                    else None
                )

                records.append({
                    "Event Link": event_url,
                    "Fight Link": fight_link,
                    "Weight Class": weight_class,
                })

            df = pd.DataFrame(records)

            ## UFCStats lists fights from the main event downward
            ## The first fight is the first one chronologically,
            ##   not the main event.
            if len(df) > 0:
                df["Fight Number"] = list(range(len(df), 0, -1))

                df = df[
                    [
                        "Event Link",
                        "Fight Number",
                        "Fight Link",
                        "Weight Class",
                    ]
                ]
            else:
                df["Fight Number"] = pd.Series(dtype=int)

            return df

        except Exception as e:
            wait_time = min(2 ** attempt, 600)

            print(
                f"\n[Retry {attempt}] {event_url} failed: {e}"
            )
            print(f"Retrying in {wait_time}s...")

            await asyncio.sleep(wait_time)

## Gets the event_link, fight link, fight number, and weight class
async def ufc_stats_1(update_size=False):

    file = hf_hub_download(
        repo_id="JunoML/MMA",
        filename="ufc_data.pkl",
        repo_type="dataset"
    )

    with open(file, "rb") as f:
        ufc_data = pickle.load(f)

    if update_size == False:
        event_links = ufc_data["past_events"]["Event Link"].tolist()
    else:
        event_links = ((ufc_data["past_events"]["Event Link"].
                        tolist())[0:update_size])

    results = [None] * len(event_links)

    async with async_playwright() as p:

        browser = await p.chromium.launch(headless=True)

        semaphore = asyncio.Semaphore(5)

        progress = tqdm(
            total=len(event_links),
            desc="Processing events",
            unit="event"
        )

        async def worker(i, event_url):

            async with semaphore:

                page = await browser.new_page()

                try:
                    df = await ufc_stats_helper_1(
                        page,
                        event_url
                    )

                    results[i] = df

                finally:
                    await page.close()

                    progress.update(1)

        await asyncio.gather(*[
            worker(i, url)
            for i, url in enumerate(event_links)
        ])

        progress.close()

        await browser.close()

    return pd.concat(results, ignore_index=True)

## Helper function for ufc_stats_helper_2
async def ufc_stats_helper_2(browser, link):
    page = await browser.new_page()

    try:
        await page.goto(link, wait_until="domcontentloaded")
        await page.wait_for_selector("i.b-fight-details__fight-title")

        ## Extract image URLs associated with bonuses

        img_srcs = await page.eval_on_selector_all(
            "i.b-fight-details__fight-title img",
            """
            imgs => imgs
                .map(img => img.src || img.getAttribute('data-src'))
                .filter(Boolean)
            """
        )

        ## Convert image filenames into bonus labels

        labels = [
            os.path.splitext(src.rsplit("/", 1)[-1])[0]
            for src in img_srcs
        ]

        method = None

        method_label = page.locator(
            "i.b-fight-details__label",
            has_text="Method"
        )

        if await method_label.count() > 0:
            method = await method_label.first.locator(
                "xpath=following-sibling::i[1]"
            ).text_content()

            method = method.strip() if method else None

        round_ = None
        time_ = None
        format_ = None
        ref_ = None

        items = page.locator(".b-fight-details__text-item")

        if await items.count() >= 4:
            round_raw = await items.nth(0).text_content()
            time_raw = await items.nth(1).text_content()
            format_raw = await items.nth(2).text_content()
            ref_raw = await items.nth(3).text_content()

            round_ = " ".join(round_raw.split()) if round_raw else None
            time_ = " ".join(time_raw.split()) if time_raw else None
            format_ = " ".join(format_raw.split()) if format_raw else None
            ref_ = " ".join(ref_raw.split()) if ref_raw else None

            if round_:
                round_ = round_.replace("Round: ", "")

            if time_:
                time_ = time_.replace("Time: ", "")

            if format_:
                format_ = format_.replace("Time format: ", "")

            if ref_:
                ref_ = ref_.replace("Referee: ", "")

        p_locator = page.locator("p.b-fight-details__text")

        texts = await p_locator.all_text_contents()
        texts = [" ".join(t.split()) for t in texts if t]

        if texts:
            texts = texts[-1].replace("Details: ", "")
        else:
            texts = None

        title = (await page.locator("i.b-fight-details__fight-title").first.text_content()).strip()

        fighters = await page.query_selector_all(
            "a.b-link.b-fight-details__person-link"
        )

        fighter_1_name = fighter_1_href = None
        fighter_2_name = fighter_2_href = None

        if len(fighters) >= 1:
            fighter_1_name = (await fighters[0].inner_text()).strip()
            fighter_1_href = await fighters[0].get_attribute("href")

        if len(fighters) >= 2:
            fighter_2_name = (await fighters[1].inner_text()).strip()
            fighter_2_href = await fighters[1].get_attribute("href")

        statuses = await page.query_selector_all(
            "i.b-fight-details__person-status"
        )

        fighter_1_status = (
            (await statuses[0].inner_text()).strip()
            if len(statuses) >= 1
            else None
        )

        fighter_2_status = (
            (await statuses[1].inner_text()).strip()
            if len(statuses) >= 2
            else None
        )

        return {
            "Bonus": labels,
            "Fighter 1": fighter_1_name,
            "Fighter 1 Link": fighter_1_href,
            "Fighter 1 Outcome": fighter_1_status,
            "Fighter 2": fighter_2_name,
            "Fighter 2 Link": fighter_2_href,
            "Fighter 2 Outcome": fighter_2_status,
            "Method": method,
            "Round": round_,
            "Time": time_,
            "Time Format": format_,
            "Referee": ref_,
            "Details": texts,
            "Title": title
        }

    finally:
        await page.close()

## Gets all other fight information
async def ufc_stats_2(df, concurrency=5, max_retries=50):

    semaphore = asyncio.Semaphore(concurrency)
    total = len(df)

    async with async_playwright() as p:

        browser = await p.chromium.launch(headless=True)

        async def worker(i, link):
            delay = 1

            for attempt in range(max_retries):
                try:
                    async with semaphore:
                        result = await ufc_stats_helper_2(browser, link)

                    return i, result

                except Exception:

                    if attempt == max_retries - 1:
                        print(f"\nFailed: {link}")
                        return i, None

                    await asyncio.sleep(delay)
                    delay *= 2

        tasks = [
            worker(i, link)
            for i, link in enumerate(df["Fight Link"])
        ]

        # tqdm_asyncio.gather displays progress as tasks complete
        completed_results = await tqdm_asyncio.gather(
            *tasks,
            total=total,
            desc="Scraping UFC stats",
        )

        await browser.close()

    completed_results.sort(key=lambda x: x[0])

    results = [r for _, r in completed_results]

    details_df = pd.DataFrame(results)

    return pd.concat(
        [df.reset_index(drop=True), details_df],
        axis=1,
    )

## Cleans past_fights
def clean_past_fights(df):
    ## Reverse the DataFrame so fights are ordered chronologically
    df.index = range(len(df) - 1, -1, -1)
    df = df.reset_index()

    mapping = {
      "perf": "POTN",
      "ko": "KOTN",
      "sub": "SOTN",
      "fight": "FOTN",
      "belt": "Title"
    }

    df["Bonus_raw"] = df["Bonus"]
    df["Bonus"] = df["Bonus_raw"].apply(
      lambda lst: [mapping[x] for x in lst if x in mapping]
  )

    ## Assign bonuses to Fighter 1.
    ##  Winners receive all applicable performance bonuses,
    ##  while losers only receive Fight of the Night.

    df["Fighter 1 Bonus"] = df.apply(
        lambda row: (
            [x for x in row["Bonus"] if x != "Title"]
            if row["Fighter 1 Outcome"] == "W"
            else (
                ["FOTN"] if "FOTN" in row["Bonus"] else []
            )
        ),
        axis=1
    )
    # Assign bonuses to Fighter 2 using the same logic

    df["Fighter 2 Bonus"] = df.apply(
        lambda row: (
            [x for x in row["Bonus"] if x != "Title"]
            if row["Fighter 2 Outcome"] == "W"
            else (
                ["FOTN"] if "FOTN" in row["Bonus"] else []
            )
        ),
        axis=1
    )


    df["Gender"] = np.where(
        df["Weight Class"].str.contains("Women's", na=False),
        "Female",
        "Male"
    )
    df["Weight Class"] = df["Weight Class"].str.replace("Women's", "", regex=False)

    title_col = df["Title"].str.lower()

    df["Title"] = np.select(
        [
            title_col.str.contains("interim", na=False),
            title_col.str.contains("title", na=False)
        ],
        [
            "Interim",
            "Undisputed"
        ],
        default="No"
    )

    df["Weight Class"] = df["Weight Class"].str.lstrip()

    df = df[[
        "Event Link",
        "Fight Number",
        "Fight Link",
        "Weight Class",
        'Gender',
        'Title',
        "Fighter 1",
        "Fighter 1 Link",
        "Fighter 1 Outcome",
        "Fighter 1 Bonus",
        "Fighter 2",
        "Fighter 2 Link",
        "Fighter 2 Outcome",
        "Fighter 2 Bonus",
        "Method",
        "Round",
        "Time",
        "Time Format",
        "Referee",
        "Details",
    ]]

    file = hf_hub_download(
    repo_id="JunoML/MMA",
    filename="ufc_data.pkl",
    repo_type="dataset"
    )

    with open(file, "rb") as f:
        ufc_data = pickle.load(f)

    past_events = ufc_data["past_events"]

    df = df.merge(
    past_events[["Event Link", "Date"]],
    on="Event Link",
    how="left"
    )

    df.insert(0, "Date", df.pop("Date"))

    return df
    
## Gets past_fights
async def get_past_fights(concurrency=5):
    tapology = await (tapology_events())
    tapology = tapology[['Date', 'Event Link', 'Event',
                        'Location', 'Venue', 'Attendance',
                        'Tapology Link']]
    
    ## Earlier fights have no odds and will return an error
    tapology = tapology.iloc[:-24]

    tapology = await (tapology_fight_odds(tapology))
    tapology = tapology.drop(columns=["Time Format"])

    for col in ["Fighter 1 Odds", "Fighter 2 Odds"]:
        tapology.loc[
            tapology[col].astype(str).str.contains
            (r"cm|kg", case=False, na=False),
            col
        ] = np.nan

    for col in ["Fighter 1 Odds", "Fighter 2 Odds"]:
        tapology[col] = tapology[col].apply(
            lambda x: int(m.group()) if 
            (m := re.search(r"[+-]?\d+", str(x))) else pd.NA
        ).astype("Int64")

    ufc_stats = await ufc_stats_1()
    ufc_stats = await ufc_stats_2(ufc_stats, concurrency)
    ufc_stats = clean_past_fights(ufc_stats)

    past_fights = pd.concat(
        [ufc_stats.reset_index(drop=True), tapology.reset_index(drop=True)],
        axis=1
    )

    past_fights.columns.values[21] = "Fighter 1 Tap"
    past_fights.columns.values[22] = "Fighter 2 Tap"

    score1 = past_fights.apply(
        lambda r: token_sort_ratio(
            str(r["Fighter 1"]),
            str(r["Fighter 1 Tap"])
        ),
        axis=1
    )

    score2 = past_fights.apply(
        lambda r: token_sort_ratio(
            str(r["Fighter 1"]),
            str(r["Fighter 2 Tap"])
        ),
        axis=1
    )

    match = score1 >= score2

    f1_odds = past_fights["Fighter 1 Odds"].copy()
    f2_odds = past_fights["Fighter 2 Odds"].copy()

    past_fights["F1 Odds"] = f1_odds.where(match, f2_odds)
    past_fights["F2 Odds"] = f2_odds.where(match, f1_odds)
        
    past_fights = past_fights[
        ['Date', 'Event Link', 'Fight Number', 'Fight Link', 
         'Weight Class', 'Gender', 'Title', 'Fighter 1', 'F1 Odds',
         'Fighter 1 Link', 'Fighter 1 Outcome', 'Fighter 1 Bonus', 
         'Fighter 2', 'F2 Odds', 'Fighter 2 Link', 'Fighter 2 Outcome',
         'Fighter 2 Bonus', 'Method', 'Round', 'Time', 'Time Format',
         'Referee', 'Details']
    ]

    past_fights = past_fights.rename(columns={
        "F1 Odds": "Fighter 1 Odds",
        "F2 Odds": "Fighter 2 Odds"
    })

    float_cols = past_fights.select_dtypes(include="float").columns
    past_fights[float_cols] = past_fights[float_cols].astype("Int64")

    exclude = ["Fighter 1 Bonus", "Fighter 2 Bonus"]
    object_cols = (past_fights.select_dtypes(include="object").
                   columns.difference(exclude))
    past_fights[object_cols] = past_fights[object_cols].astype("string")

    return past_fights

## Updates past_fights
async def update_past_fights(concurrency=5):
    
    past_events = pd.read_csv("scraper/scraper_data/past_events.csv")
    past_events_unique = set(past_events["Event Link"])

    past_fights = pd.read_csv("scraper/scraper_data/past_fights.csv")
    past_fights_unique = set(past_fights["Event Link"])

    if len(past_events_unique) == len(past_fights_unique):
        past_fights["Date"] = (pd.to_datetime(past_fights["Date"]).
                               astype("datetime64[ns]"))
        past_fights["Fighter 1 Odds"] = (past_fights["Fighter 1 Odds"].
                                         astype("Int64"))
        past_fights["Fighter 2 Odds"] = (past_fights["Fighter 2 Odds"].
                                         astype("Int64"))
        objects = (past_fights.select_dtypes("object").
                   columns.difference(["Fighter 1 Bonus", "Fighter 2 Bonus"]))
        past_fights[objects] = past_fights[objects].astype("string")
        print("No new past_fights")
        return past_fights
    
    new_events = past_events_unique - past_fights_unique

    tapology = await (tapology_events(True))
    tapology = tapology[['Date', 'Event Link', 'Event',
                        'Location', 'Venue', 'Attendance',
                        'Tapology Link']]
    tapology = tapology.iloc[:len(new_events)]

    tapology = await (tapology_fight_odds(tapology))
    tapology = tapology.drop(columns=["Time Format"])

    for col in ["Fighter 1 Odds", "Fighter 2 Odds"]:
        tapology.loc[
            tapology[col].astype(str).str.contains
            (r"cm|kg", case=False, na=False),
            col
        ] = np.nan

    for col in ["Fighter 1 Odds", "Fighter 2 Odds"]:
        tapology[col] = tapology[col].apply(
            lambda x: int(m.group()) if 
            (m := re.search(r"[+-]?\d+", str(x))) else pd.NA
        ).astype("Int64")

    ufc_stats = await ufc_stats_1(len(new_events))
    ufc_stats = await ufc_stats_2(ufc_stats, concurrency)

    ufc_stats = clean_past_fights(ufc_stats)

    past_fights = pd.concat(
        [ufc_stats.reset_index(drop=True), tapology.reset_index(drop=True)],
        axis=1
    )

    past_fights.columns.values[21] = "Fighter 1 Tap"
    past_fights.columns.values[22] = "Fighter 2 Tap"

    score1 = past_fights.apply(
        lambda r: ratio(str(r["Fighter 1"]), str(r["Fighter 1 Tap"])),
        axis=1
    )
    score2 = past_fights.apply(
        lambda r: ratio(str(r["Fighter 1"]), str(r["Fighter 2 Tap"])),
        axis=1
    )

    match = score1 >= score2

    f1_odds = past_fights["Fighter 1 Odds"].copy()
    f2_odds = past_fights["Fighter 2 Odds"].copy()

    past_fights["F1 Odds"] = f1_odds.where(match, f2_odds)
    past_fights["F2 Odds"] = f2_odds.where(match, f1_odds)
        
    past_fights = past_fights[
        ['Date', 'Event Link', 'Fight Number', 'Fight Link', 
         'Weight Class', 'Gender', 'Title', 'Fighter 1', 'F1 Odds',
         'Fighter 1 Link', 'Fighter 1 Outcome', 'Fighter 1 Bonus', 
         'Fighter 2', 'F2 Odds', 'Fighter 2 Link', 'Fighter 2 Outcome',
         'Fighter 2 Bonus', 'Method', 'Round', 'Time', 'Time Format',
         'Referee', 'Details']
    ]

    past_fights = past_fights.rename(columns={
        "F1 Odds": "Fighter 1 Odds",
        "F2 Odds": "Fighter 2 Odds"
    })

    float_cols = past_fights.select_dtypes(include="float").columns
    past_fights[float_cols] = past_fights[float_cols].astype("Int64")

    exclude = ["Fighter 1 Bonus", "Fighter 2 Bonus"]
    object_cols = (past_fights.select_dtypes(include="object").
                   columns.difference(exclude))
    past_fights[object_cols] = past_fights[object_cols].astype("string")

    old_past_fights = pd.read_csv("scraper/scraper_data/past_fights.csv")
    new_past_fights = (pd.concat([past_fights, old_past_fights],
                                  axis=0, ignore_index=True))
    
    new_past_fights["Round"] = new_past_fights["Round"].astype("int64")
    new_past_fights["Date"] = pd.to_datetime(new_past_fights["Date"]).dt.date

    return new_past_fights

## Gets future_fights
async def get_future_fights():
    file = hf_hub_download(
        repo_id="JunoML/MMA",
        filename="ufc_data.pkl",
        repo_type="dataset"
    )

    with open(file, "rb") as f:
        ufc_data = pickle.load(f)

    next_event = ufc_data["future_events"].iloc[0, 1]
    next_event_date = ufc_data["future_events"].iloc[0, 0]

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        df = await ufc_stats_helper_1(page, next_event)
        await browser.close()

    df = await ufc_stats_2(df)
    df = clean_past_fights(df)

    swap = (
        df["Fighter 1"].str.lower()
        > df["Fighter 2"].str.lower()
    )

    df.loc[swap, ["Fighter 1", "Fighter 2"]] = (
        df.loc[swap, ["Fighter 2", "Fighter 1"]].to_numpy()
    )

    df.loc[swap, ["Fighter 1 Link", "Fighter 2 Link"]] = (
        df.loc[swap, ["Fighter 2 Link", "Fighter 1 Link"]].to_numpy()
    )

    df = df[
        [
            "Date",
            "Event Link",
            "Fight Number",
            "Fight Link",
            "Weight Class",
            "Gender",
            "Title",
            "Fighter 1",
            "Fighter 1 Link",
            "Fighter 2",
            "Fighter 2 Link"
        ]
    ]
    df["Date"] = next_event_date
    df["Names"] = df["Fighter 1"] + " " + df["Fighter 2"]
    df["Names"] = df["Names"].apply(
        lambda x: " ".join(sorted(x.split()))
    )

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()

        tapology_link = "https://www.tapology.com" + \
        "/fightcenter/promotions/1-ultimate-fighting-championship-ufc"

        await page.goto(tapology_link, wait_until="domcontentloaded")

        link = page.locator(".link-primary-gray").first
        href = await link.get_attribute("href")

        await browser.close()

    link = pd.DataFrame({
        "Tapology Link": [
            "https://www.tapology.com" + href
        ]
    })

    tapology_odds = await tapology_fight_odds(link)
    tapology_odds["Names"] = (tapology_odds["Fighter 1"] + " " + 
                               tapology_odds["Fighter 2"])
    tapology_odds["Names"] = tapology_odds["Names"].apply(
        lambda x: " ".join(sorted(x.split()))
    )
    
    choices = tapology_odds["Names"].dropna().tolist()

    matches = []

    for name in df["Names"]:
        match = process.extractOne(
            name,
            choices,
            scorer=fuzz.token_sort_ratio,
            score_cutoff=80
        )

        if match:
            matches.append((match[0], match[1]))
        else:
            matches.append((None, None))

    df["Matched Names"] = [x[0] for x in matches]
    df["Match Score"] = [x[1] for x in matches]

    df = df.merge(
        tapology_odds,
        left_on="Matched Names",
        right_on="Names",
        how="left",
        suffixes=("_df", "_tapology")
    )

    original_score = (
        df.apply(lambda x: WRatio(str(x["Fighter 1_df"]), 
                                  str(x["Fighter 1_tapology"])), axis=1)
        + df.apply(lambda x: WRatio(str(x["Fighter 2_df"]),
                                     str(x["Fighter 2_tapology"])), axis=1)
    )

    swapped_score = (
        df.apply(lambda x: WRatio(str(x["Fighter 1_df"]), 
                                  str(x["Fighter 2_tapology"])), axis=1)
        + df.apply(lambda x: WRatio(str(x["Fighter 2_df"]), 
                                    str(x["Fighter 1_tapology"])), axis=1)
    )

    swap = swapped_score > original_score

    df.loc[swap, ["Fighter 1 Odds", "Fighter 2 Odds"]] = (
        df.loc[swap, ["Fighter 2 Odds", "Fighter 1 Odds"]].values
    )

    df = df[[
        "Date", "Event Link",
        "Fight Link", "Fight Number",
        "Weight Class", "Gender", "Title",
        "Fighter 1_df", "Fighter 1 Link",
        "Fighter 1 Odds", "Fighter 2_df",
        "Fighter 2 Link", "Fighter 2 Odds",
        "Time Format"
    ]]

    df = df.rename(
        columns={
            "Fighter 1_df": "Fighter 1",
            "Fighter 2_df": "Fighter 2",
        }
    )

    df["Fighter 1 Odds"] = pd.to_numeric(
        df["Fighter 1 Odds"].astype(str).str.extract(r'([+-]?\d+)')[0],
        errors="coerce"
    )

    df["Fighter 2 Odds"] = pd.to_numeric(
        df["Fighter 2 Odds"].astype(str).str.extract(r'([+-]?\d+)')[0],
        errors="coerce"
    )

    df[df.select_dtypes(include="object").columns] = (
        df.select_dtypes(include="object").astype("string")
    )

    df["Time Format"] = df["Time Format"].replace({
        "5 x 5": "5 Rnd (5-5-5-5-5)",
        "3 x 5": "3 Rnd (5-5-5)"
    })

    return df

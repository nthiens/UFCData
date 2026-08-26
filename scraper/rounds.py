import asyncio
import pickle

import pandas as pd
from huggingface_hub import hf_hub_download
from playwright.async_api import async_playwright
from tqdm import tqdm


## Gets all rounds in a single fight.
async def single_fight(page, fight_link, fight_id, fight_number, date, event_link):
    await page.goto(
        fight_link,
        wait_until="domcontentloaded",
        timeout=8000
    )

    ## Get the profile links for both fighters
    links = page.locator(
        "a.b-link.b-link_style_black"
    )

    fighter_1_link = await links.nth(0).get_attribute("href")
    fighter_2_link = await links.nth(1).get_attribute("href")

    sections = page.locator(
        ".b-fight-details__section.js-fight-section"
    )

    await sections.first.wait_for(
        state="attached",
        timeout=10_000
    )

    ## Extract grappling statistics for each round
    section = sections.nth(2)
    rows = section.locator("tr")
    count = await rows.count()

    round_data = []

    for i in range(2, count, 2):
        text = await rows.nth(i).text_content()

        grappling = [
            " ".join(line.split())
            for line in text.splitlines()
            if line.strip()
        ]

        round_data.append(grappling)

    ## Extract striking statistics for each round
    section = sections.nth(4)
    rows = section.locator("tr")
    count = await rows.count()

    round_2_data = []

    for i in range(2, count, 2):
        text = await rows.nth(i).text_content()

        strikes = [
            " ".join(line.split())
            for line in text.splitlines()
            if line.strip()
        ]

        round_2_data.append(strikes)

    ## Combine the grappling and striking statistics
    result = [
        x + y
        for x, y in zip(
            round_data,
            round_2_data
        )
    ]

    ## Add fight information and round numbers to each row
    result = [
        [
            date,
            event_link,
            fight_link,
            fight_id,
            fight_number,
            round_number,
            fighter_1_link,
            fighter_2_link
        ] + row
        for round_number, row in enumerate(
            result,
            start=1
        )
    ]

    return result

# Worker that pulls fights from the queue and scrapes them.
async def round_worker(queue, page, results, failed_urls, max_retries, progress):
    while True:
        try:
            (
                i,
                fight_link,
                fight_id,
                fight_number,
                date,
                event_link
            ) = queue.get_nowait()

        except asyncio.QueueEmpty:
            break

        for attempt in range(max_retries):
            try:
                scraped = await single_fight(
                    page,
                    fight_link,
                    fight_id,
                    fight_number,
                    date,
                    event_link
                )

                results[i] = scraped
                break

            except Exception as e:
                if attempt == max_retries - 1:
                    print(
                        f"\nFailed: "
                        f"{fight_id} | "
                        f"{fight_link}\n"
                        f"{type(e).__name__}: {e}"
                    )

                    failed_urls.append(
                        (
                            fight_id,
                            fight_link
                        )
                    )

                else:
                    await asyncio.sleep(2)

        progress.update(1)
        queue.task_done()

## Scrapes rounds for all fights concurrently.
async def scrape_rounds(df, concurrency=5, max_retries=5):
    df = df.copy()
    df["index"] = range(1, len(df) + 1)

    ## Add each fight and its data to the queue
    queue = asyncio.Queue()

    for i in range(len(df)):
        await queue.put(
            (
                i,
                df.iloc[i]["Fight Link"],
                df.iloc[i]["index"],
                df.iloc[i]["Fight Number"],
                df.iloc[i]["Date"],
                df.iloc[i]["Event Link"]
            )
        )

    results = [None] * len(df)
    failed_urls = []

    progress = tqdm(
        total=len(df),
        desc="Scraping UFC stats",
        unit="fight"
    )

    ## Create a browser page for each concurrent worker
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True
        )

        context = await browser.new_context(
            java_script_enabled=True
        )

        pages = []

        for _ in range(concurrency):
            page = await context.new_page()

            page.set_default_timeout(
                10_000
            )

            page.set_default_navigation_timeout(
                30_000
            )

            pages.append(page)

        ## Start the workers and wait for all fights to finish
        workers = [
            asyncio.create_task(
                round_worker(
                    queue,
                    pages[i],
                    results,
                    failed_urls,
                    max_retries,
                    progress
                )
            )
            for i in range(concurrency)
        ]

        await asyncio.gather(*workers)

        for page in pages:
            await page.close()

        await context.close()
        await browser.close()

    progress.close()

    ## Report fights that could not be scraped.
    ##  Contains some very old fights with no round statistics
    if failed_urls:
        print()
        print("=" * 60)
        print("FAILED URLS")
        print("=" * 60)

        failed_urls.sort(
            key=lambda x: x[0]
        )

        for fight_id, fight_link in failed_urls:
            print(
                f"{fight_id}: {fight_link}"
            )

    else:
        print()
        print("No failed URLs!")

    print("=" * 60)

    ## Combine results from all successfully scraped fights
    flattened_results = []

    for result in results:
        if result is not None:
            flattened_results.extend(result)

    return clean_rounds(flattened_results)

## Cleans and standardizes round statistics.
def clean_rounds(flattened_results):
    stats_df = pd.DataFrame(
        flattened_results
    )

    ## Assign meaningful names to the scraped columns
    stats_df = stats_df.rename(
        columns={
            0: "Date",
            1: "Event Link",
            2: "Fight Link",
            3: "index",
            4: "Fight Number",
            5: "Round",
            6: "Fighter 1 Link",
            7: "Fighter 2 Link",
            8: "Fighter 1",
            9: "Fighter 2",
            10: "Fighter 1 KD",
            11: "Fighter 2 KD",
            12: "Fighter 1 Total SS",
            13: "Fighter 2 Total SS",
            18: "Fighter 1 TD",
            19: "Fighter 2 TD",
            22: "Fighter 1 Sub Att",
            23: "Fighter 2 Sub Att",
            24: "Fighter 1 Rev",
            25: "Fighter 2 Rev",
            26: "Fighter 1 Ctrl",
            27: "Fighter 2 Ctrl",
            34: "Fighter 1 Head SS",
            35: "Fighter 2 Head SS",
            36: "Fighter 1 Body SS",
            37: "Fighter 2 Body SS",
            38: "Fighter 1 Leg SS",
            39: "Fighter 2 Leg SS",
            40: "Fighter 1 Distance SS",
            41: "Fighter 2 Distance SS",
            42: "Fighter 1 Clinch SS",
            43: "Fighter 2 Clinch SS",
            44: "Fighter 1 Ground SS",
            45: "Fighter 2 Ground SS",
        }
    )

    ## Keep only the columns used in the final dataset
    stats_df = stats_df[[
        "Date",
        "Fight Link",
        "Event Link",
        "Fight Number",
        "Round",
        "Fighter 1",
        "Fighter 2",
        "Fighter 1 Link",
        "Fighter 2 Link",
        "Fighter 1 TD",
        "Fighter 2 TD",
        "Fighter 1 Sub Att",
        "Fighter 2 Sub Att",
        "Fighter 1 Rev",
        "Fighter 2 Rev",
        "Fighter 1 Ctrl",
        "Fighter 2 Ctrl",
        "Fighter 1 KD",
        "Fighter 2 KD",
        "Fighter 1 Total SS",
        "Fighter 2 Total SS",
        "Fighter 1 Head SS",
        "Fighter 2 Head SS",
        "Fighter 1 Body SS",
        "Fighter 2 Body SS",
        "Fighter 1 Leg SS",
        "Fighter 2 Leg SS",
        "Fighter 1 Distance SS",
        "Fighter 2 Distance SS",
        "Fighter 1 Clinch SS",
        "Fighter 2 Clinch SS",
        "Fighter 1 Ground SS",
        "Fighter 2 Ground SS",
    ]]

    ## Convert objects to string
    object_cols = stats_df.select_dtypes(
        include="object"
    ).columns

    stats_df[object_cols] = (
        stats_df[object_cols]
        .astype("string")
    )

    ## Convert other objects to string
    cols = [
        "Fight Number",
        "Fighter 1 Sub Att",
        "Fighter 2 Sub Att",
        "Fighter 1 Rev",
        "Fighter 2 Rev",
        "Fighter 1 KD",
        "Fighter 2 KD"
    ]

    stats_df[cols] = stats_df[cols].astype(
        "int64"
    )

    stats_df["Date"] = pd.to_datetime(
        stats_df["Date"]
    )

    return stats_df

## Gets rounds for the initial dataset.
async def get_rounds(concurrency=5, max_retries=5):
    file = hf_hub_download(
        repo_id="JunoML/MMA",
        filename="ufc_data.pkl",
        repo_type="dataset"
    )

    with open(file, "rb") as f:
        ufc_data = pickle.load(f)

    df = ufc_data["past_fights"].copy()

    return await scrape_rounds(
        df,
        concurrency,
        max_retries
    )

## Updates the existing rounds dataset.
async def update_rounds(concurrency=5, max_retries=5):

    past_fights = pd.read_csv("scraper/scraper_data/past_fights.csv")
    old_rounds = pd.read_csv("scraper/scraper_data/rounds.csv")

    ## Find fights that are missing from the existing rounds dataset
    missing_rounds = past_fights[
        (
            ~past_fights["Fight Link"].isin(
                old_rounds["Fight Link"]
            )
        )
        &
        (
            pd.to_datetime(
                past_fights["Date"]
            ) >= "2026-01-01"
        )
    ].copy()

    ## Return the existing dataset if there are no new fights
    if len(missing_rounds) == 0:
        object_cols = old_rounds.select_dtypes(
            include="object"
        ).columns

        old_rounds[object_cols] = (
            old_rounds[object_cols]
            .astype("string")
        )

        old_rounds["Date"] = pd.to_datetime(
            old_rounds["Date"]
        )

        return old_rounds

    ## Scrape the missing fights
    new_rounds = await scrape_rounds(
        missing_rounds,
        concurrency,
        max_retries
    )

    ## Combine the new data with the existing dataset
    rounds = pd.concat(
        [
            new_rounds,
            old_rounds
        ],
        ignore_index=True
    )

    rounds["Date"] = pd.to_datetime(rounds["Date"]).dt.date

    return rounds

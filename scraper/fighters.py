from bs4 import BeautifulSoup
import pandas as pd
import asyncio
import pandas as pd
from playwright.async_api import async_playwright
import string
from tqdm.asyncio import tqdm_asyncio
import numpy as np
from huggingface_hub import hf_hub_download
import pickle

## Gets the UFCStats fighter list for a single letter and returns
## the fighter data and profile links.
async def scrape_letter(page, char):
    url = f"http://ufcstats.com/statistics/fighters?char={char}&page=all"

    print(f"\rScraping {char.upper()}      ", end="", flush=True)

    await page.goto(url, wait_until="networkidle")
    html = await page.content()
    soup = BeautifulSoup(html, "html.parser")
    table = soup.find("table")

    data = []

    headers = [
        th.get_text(strip=True)
        for th in table.select("thead th")
    ]
    headers.append("Fighter Link")

    for row in table.select("tbody tr"):
        tds = row.select("td")
        if not tds:
            continue

        cols = [td.get_text(strip=True) for td in tds]

        a_tag = tds[0].find("a")
        fighter_link = a_tag.get("href") if a_tag else None

        cols.append(fighter_link)
        data.append(cols)

    return data, headers

## Worker that pulls letters from the queue, scrapes them, and
## stores the results.
async def worker(queue, browser, results):
    context = await browser.new_context()
    page = await context.new_page()

    while True:
        char = await queue.get()
        if char is None:
            break

        try:
            data, headers = await scrape_letter(page, char)
            results.append((data, headers))
        except Exception as e:
            print(f"Error scraping {char}: {e}")

        queue.task_done()

    await context.close()

## Gets fighter information for all letters A–Z concurrently
async def fighter_bio(concurrency=5):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)

        queue = asyncio.Queue()

        for char in string.ascii_lowercase:
            queue.put_nowait(char)

        results = []

        workers = [
            asyncio.create_task(worker(queue, browser, results))
            for _ in range(concurrency)
        ]

        await queue.join()

        for _ in workers:
            queue.put_nowait(None)

        await asyncio.gather(*workers)
        await browser.close()

    ## Combine results from each letter into a single DataFrame
    all_data = []
    headers = None

    for data, h in results:
        all_data.extend(data)
        headers = h

    df = pd.DataFrame(all_data, columns=headers)

    ## Remove unnecessary columns and standardize column names
    df = df.iloc[1:].reset_index(drop=True)
    df = df.drop("Belt", axis=1, errors="ignore")
    df = df.rename(columns={
        "Ht.": "Height",
        "Wt.": "Weight"
    })

    ## Clean physical measurements and missing values
    df["Reach"] = df["Reach"].str.replace('"', "", regex=False)
    df["Weight"] = df["Weight"].str.replace(" lbs.", "", regex=False)

    df = df.apply(
        lambda col: col.str.replace("--", "", regex=False)
        if col.dtype == "object" else col
    )

    df["Reach"] = pd.to_numeric(df["Reach"], errors="coerce")
    df["Weight"] = pd.to_numeric(df["Weight"], errors="coerce")

    ## Convert height from feet and inches to total inches
    df["Height"] = df["Height"].str.replace('"', "", regex=False)
    df["Height"] = df["Height"].str.replace("'", "", regex=False)

    df["Height"] = df["Height"].str.split()

    df["Height"] = df["Height"].apply(
        lambda x: float(x[0]) * 12 + float(x[1])
        if isinstance(x, list) and len(x) == 2 else np.nan
    )

    df["Height"] = pd.to_numeric(df["Height"], errors="coerce")
    df = df.dropna(subset=["Fighter Link"])

    return df

## Gets a single fighter's birthday
async def birthdate(page, url):
    await page.goto(
        url,
        wait_until="domcontentloaded",
        timeout=30_000
    )

    items = page.locator(
        ".b-list__box-list-item"
    )

    await items.first.wait_for(
        state="attached",
        timeout=10_000
    )

    dob = None

    for i in range(await items.count()):
        text = (await items.nth(i).inner_text()).strip()

        if text.startswith("DOB:"):
            dob = text.replace("DOB:", "").strip()
            break

    record = None

    try:
        record = await page.locator(
            "span.b-content__title-record"
        ).text_content(timeout=5_000)

        record = record.strip() if record else None

    except Exception:
        pass

    return url, dob, record

## Gets all fighters birthday
async def birthdates(df, concurrency=5, url_col="links", retry=10):
    semaphore = asyncio.Semaphore(concurrency)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)

        async def worker(url):
            async with semaphore:
                for attempt in range(1, retry + 1):
                    page = await browser.new_page()

                    try:
                        result = await birthdate(page, url)
                        return result

                    except Exception as e:
                        print(
                            f"Attempt {attempt}/{retry} failed\n"
                            f"Fighter: {url}\n"
                            f"Error: {e}"
                        )

                        if attempt < retry:
                            delay = 2 ** attempt
                            await asyncio.sleep(delay)

                    finally:
                        await page.close()

                print(
                    f"FAILED AFTER {retry} ATTEMPTS: {url}"
                )

                return url, None, None

        tasks = [
            worker(url)
            for url in df[url_col]
        ]

        results = await tqdm_asyncio.gather(
            *tasks,
            total=len(tasks),
            desc="Scraping fighter bios"
        )

        await browser.close()

    df = df.copy()

    df["DOB"] = [r[1] for r in results]
    df["Record"] = [r[2] for r in results]

    return df

## Cleans and standardizes fighter_bio
def clean_fighter_bio(df):
    df = df.copy()

    df = df.dropna(subset=["Fighter Link"])

    df["DOB"] = df["DOB"].replace("--", "")
    df["DOB"] = pd.to_datetime(df["DOB"], errors="coerce")

    df["NC"] = (
        df["Record"]
        .str.extract(r"\((\d+)")[0]
        .fillna("0")
        .astype(int)
    )

    df = df.drop(columns=["Record"])

    ## Create a full name and select the final columns
    df["Name"] = df["First"] + " " + df["Last"]

    df = df[
        [
            "Fighter Link",
            "Name",
            "Nickname",
            "Height",
            "Weight",
            "Reach",
            "Stance",
            "W",
            "L",
            "D",
            "NC",
            "DOB"
        ]
    ]

    df = df.rename(columns={
        "W": "Total W",
        "L": "Total L",
        "D": "Total D",
        "NC": "Total NC"
    })

    ## Set appropriate data types
    for col in ["Height", "Weight", "Reach"]:
        df[col] = pd.to_numeric(
            df[col],
            errors="coerce"
        ).astype("Float64")

    for col in ["Total W", "Total L", "Total D", "Total NC"]:
        df[col] = pd.to_numeric(
            df[col],
            errors="coerce"
        ).round().astype("Int64")

    for col in ["Fighter Link", "Name", "Nickname", "Stance"]:
        df[col] = df[col].astype("string")

    return df

## Merges fighter_bio and birthdates then cleans it to produce future_events
async def get_fighter_bio(concurrency=5):
    df = await fighter_bio(concurrency)
    df = await birthdates(df, concurrency, url_col="Fighter Link")
    df = clean_fighter_bio(df)
    return df

## Updates fighter_bio
async def update_fighter_bio(concurrency=5):
 
    old_fighter_bio = pd.read_csv("scraper/scraper_data/fighter_bio.csv")
    new_fighter_bio = await fighter_bio(concurrency)

    ## Return the existing dataset if no new fighters were found
    if len(old_fighter_bio) == len(new_fighter_bio):
        old_fighter_bio["DOB"] = pd.to_datetime(
            old_fighter_bio["DOB"],
            errors="coerce"
        )

        old_fighter_bio[
            old_fighter_bio.select_dtypes(include="object").columns
        ] = (
            old_fighter_bio
            .select_dtypes(include="object")
            .astype("string")
        )

        print("No new fighters")
        return old_fighter_bio

    print()

    ## Keep only fighters that are not already in the dataset
    new_fighters = new_fighter_bio[
        ~new_fighter_bio["Fighter Link"].isin(
            old_fighter_bio["Fighter Link"]
        )
    ]

    ## Scrape DOB for the new fighters
    new_fighters = await birthdates(
        new_fighters,
        concurrency,
        url_col="Fighter Link"
    )

    new_fighters = clean_fighter_bio(new_fighters)

    ## Add the new fighters to the existing dataset
    new_fighters = pd.concat(
        [new_fighters, old_fighter_bio],
        axis=0,
        ignore_index=True
    )

    new_fighters = new_fighters.sort_values(
        by="Name",
        key=lambda x: x.str.split().str[::-1].str.join(" ")
    ).reset_index(drop=True)

    return new_fighters

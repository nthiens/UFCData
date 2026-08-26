import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
import unicodedata
import pandas as pd
from playwright.async_api import async_playwright

## Helper function for squash_table. Extracts an integer
##   from a value.
def safe_int(val, default=1):
    if val is None:
        return default
    m = re.search(r"\d+", str(val))
    return int(m.group()) if m else default

## Wikipedia tables sometimes use rowspan and colspan attributes.
##  These make it difficult to convert the table directly into a
##  Pandas DataFrame.
## This function expands those cells so that every row has a
##  regular grid structure.
def squash_table(table):
    rows = table.find_all("tr")

    grid = []
    span_map = {}

    for r_idx, row in enumerate(rows):
        cells = row.find_all(["td", "th"])

        if not cells:
            continue

        out = []
        c_idx = 0
        col_pos = 0

        while c_idx < len(cells):
            cell = cells[c_idx]
            while (r_idx, col_pos) in span_map:
                out.append(span_map.pop((r_idx, col_pos)))
                col_pos += 1

            text = cell.get_text(" ", strip=True)

            rowspan = safe_int(cell.get("rowspan", 1))
            colspan = safe_int(cell.get("colspan", 1))

            for i in range(colspan):
                out.append(text)

                if rowspan > 1:
                    for r in range(1, rowspan):
                        span_map[(r_idx + r, col_pos)] = text

                col_pos += 1

            c_idx += 1

        while (r_idx, col_pos) in span_map:
            out.append(span_map.pop((r_idx, col_pos)))
            col_pos += 1

        grid.append(out)

    return grid

## Gets past location, venue, and attendance information 
##  from Wikipedia
def wikipedia_past_events():
  url = "https://en.wikipedia.org/wiki/List_of_UFC_events"
  headers = {"User-Agent": "Mozilla/5.0"}

  html = requests.get(url, headers=headers).text
  soup = BeautifulSoup(html, "html.parser")

  tables = soup.find_all("table")
  table = tables[1]

  grid = squash_table(table)

  df = pd.DataFrame(grid)
  df.columns = df.iloc[0]
  df = df[1:].reset_index(drop=True)
  df = df[df["#"] != "—"]
  df["Date"] = pd.to_datetime(df["Date"]).dt.date
  df["Attendance"] = df["Attendance"].replace("— N/a", "")
  df["Location"] = df["Location"].str.replace(" ,", ",", regex=False)
  df["Attendance"] = df["Attendance"].str.replace(",", "", regex=False)
  df = df.iloc[:, 1:-1]

  wiki_events = df
  wiki_events["Date"] = pd.to_datetime(wiki_events["Date"])

  ## Normalize Text
  wiki_events["Event"] = wiki_events["Event"].apply(
      lambda x: unicodedata.normalize("NFKD", x).encode("ascii", "ignore").
      decode("ascii") if isinstance(x, str) else x
  )
  wiki_events["Location"] = wiki_events["Location"].apply(
      lambda x: unicodedata.normalize("NFKD", x).
      encode("ascii", "ignore").decode("ascii") if isinstance(x, str) else x
  )
  wiki_events["Event"] = (wiki_events["Event"].
                          str.replace("de ", "De", regex=False))

  ## Extract and standardize country names from the location
  wiki_events["Country"] = (
      wiki_events["Location"]
      .str.split(", ")
      .str[-1]
  )

  wiki_events["Country"] = (wiki_events["Country"].
                            str.replace("U.S.", "USA", regex=False))
  wiki_events["Country"] = (wiki_events["Country"].
                            str.replace("England", "United Kingdom",
                                        regex=False))
  wiki_events["Country"] = (wiki_events["Country"].
                            str.replace("Northern Ireland", "United Kingdom",
                                        regex=False))
  wiki_events["Country"] = (wiki_events["Country"].
                            str.replace("Scotland", "United Kingdom",
                                        regex=False))
  wiki_events = wiki_events.reset_index(drop=True)

  return wiki_events

## Gets past date, event, and event_link information from UFC Stats
async def ufc_stats_past_events():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        await page.goto(
            "http://ufcstats.com/statistics/events/completed?page=all",
            wait_until="networkidle"
        )

        html = await page.content()
        await browser.close()

    soup = BeautifulSoup(html, "html.parser")
    rows = soup.select("tr.b-statistics__table-row")

    data = []

    for row in rows:
        cols = row.find_all("td")
        if len(cols) < 2:
            continue

        event_col = cols[0]

        name_tag = event_col.find("a")
        date_tag = event_col.find("span")

        data.append({
            "Event": name_tag.get_text(strip=True) if name_tag else None,
            "Date": date_tag.get_text(strip=True) if date_tag else None,
            "Location": cols[1].get_text(strip=True),
            "Event_link": name_tag["href"] if name_tag and name_tag.has_attr("href") else None
        })

    df = pd.DataFrame(data)
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df["Event"] = df["Event"].str.replace("vs ", "vs. ", regex=False)

    df["Country"] = (
      df["Location"]
      .str.split(", ")
      .str[-1]
  )

    df = df[["Event", "Date", "Location", "Event_link", "Country"]]

    return df

## Merges Wikipedia and UFCStats then cleans it to produce past_events
async def get_past_events():
  ufc_events = await ufc_stats_past_events()
  wiki_events = wikipedia_past_events()

  ## Account for historical events where the dates differ 
  ##  between sources
  wiki_missing_dates = (
    wiki_events.merge(
      ufc_events[["Date"]],
      on="Date",
      how="left",
      indicator=True
    )
    .query('_merge == "left_only"')
  )

  wiki_missing_dates["Date"] = (
    wiki_missing_dates["Date"] - pd.Timedelta(days=1)
  )

  wiki_missing_dates = wiki_missing_dates.drop(columns="_merge")

  combined_events = wiki_events.merge(
    wiki_missing_dates,
    on=["Event"],
    how="outer",
    indicator=True
  )

  combined_events.loc[
    combined_events["_merge"] == "both",
    "Date_x"
  ] = combined_events["Date_y"]

  combined_events = combined_events.rename(columns={
    "Date_x": "Date",
    "Venue_x": "Venue",
    "Country_x": "Country",
    "Location_x": "Location",
    "Attendance_x": "Attendance"
  })

  combined_events = combined_events.drop(columns=[
    "Date_y",
    "Venue_y",
    "Country_y",
    "Location_y",
    "Attendance_y",
    "_merge"
  ])

  past_events = combined_events.merge(
    ufc_events,
    on=["Date", "Country"],
    how="right"
  )

  past_events = past_events.drop(
    columns=["Event_x", "Location_x", "Country"]
  )

  past_events = past_events.rename(columns={
    "Event_y": "Event",
    "Location_y": "Location",
    "Event_link": "Event Link"
  })

  past_events = past_events[
    ["Event", "Date", "Location", "Venue", "Attendance", "Event Link"]
  ]

  ## Edge cases
  past_events.loc[
    past_events["Event"] == "UFC Fight Night: Rockhold vs. Bisping",
    ["Venue", "Attendance"]
  ] = ["Qudos Bank Arena", 9904]

  past_events.loc[
    past_events["Event"] == "UFC on FX: Sotiropoulos vs. Pearson",
    ["Venue", "Attendance"]
  ] = ["Gold Coast Convention and Exhibition Centre", 5133]

  past_events = past_events[["Date", "Event Link", "Event",
                             "Location", "Venue", "Attendance"]]
  
  past_events["Attendance"] = pd.to_numeric(
    past_events["Attendance"],
    errors="coerce"
    ).astype("Int64")
  
  past_events = past_events.astype({
    "Date": "datetime64[ns]",
    "Event Link": "string",
    "Event": "string",
    "Location": "string",
    "Venue": "string",
    "Attendance": "Int64"
  })

  return past_events

## Gets future location and venue information from Wikipedia
def wikipedia_future_events():
    url = "https://en.wikipedia.org/wiki/List_of_UFC_events"
    headers = {"User-Agent": "Mozilla/5.0"}

    html = requests.get(url, headers=headers).text
    soup = BeautifulSoup(html, "html.parser")

    tables = soup.find_all("table")
    table = tables[0]

    grid = squash_table(table)
    df = pd.DataFrame(grid)
    df.columns = df.iloc[0]   # first row → column names
    df = df.iloc[1:].reset_index(drop=True)
    df["Date"] = pd.to_datetime(df["Date"]).dt.date
    df["Location"] = df["Location"].str.replace(" ,", ",", regex=False)
    df = df[["Event", "Date", "Venue", "Location"]]

    return df

## Gets future date, event, and event_link information from UFC Stats
async def ufc_stats_future_events():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        await page.goto("http://ufcstats.com/statistics/events/upcoming")
        await page.wait_for_selector("table")

        html = await page.content()
        await browser.close()

    soup = BeautifulSoup(html, "html.parser")

    table = soup.find("table", class_="b-statistics__table-events")
    tables = soup.find_all("table")
    table = tables[0]
    tbody = table.find("tbody")

    rows = []

    for tr in tbody.find_all("tr"):
        tds = tr.find_all("td")

        if len(tds) < 2:
            continue

        a = tds[0].find("a")
        span = tds[0].find("span", class_="b-statistics__date")

        event_name = a.get_text(strip=True) if a else None
        event_url = a["href"] if a and a.has_attr("href") else None
        event_date = span.get_text(strip=True) if span else None
        location = tds[1].get_text(strip=True)

        rows.append({
            "Event": event_name,
            "Date": event_date,
            "Location": location,
            "Event Link": event_url
        })

        df = pd.DataFrame(rows)
        df["Date"] = pd.to_datetime(df["Date"]).dt.date

    return df

## Merges Wikipedia and UFCStats then cleans it to produce future_events
async def get_future_events():
  merged = pd.merge(await ufc_stats_future_events(), wikipedia_future_events(), on="Date", how="inner")
  merged = merged.drop(columns=["Event_y", "Location_y"])
  merged = merged.rename(columns={
      "Event_x": "Event",
      "Location_x": "Location"
  })
  merged = merged[["Date", "Event Link", "Event", "Location", "Venue"]]
  merged = merged.astype({
    "Date": "datetime64[ns]",
    "Event Link": "string",
    "Event": "string",
    "Location": "string",
    "Venue": "string"
  })

  return merged

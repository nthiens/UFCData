from playwright.async_api import async_playwright
from datetime import datetime
import asyncio
import re
from huggingface_hub import upload_file

## Gets the date and time of next event
async def get_next_event():

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()

        tapology_link = (
            "https://www.tapology.com"
            "/fightcenter/promotions/1-ultimate-fighting-championship-ufc"
        )

        await page.goto(tapology_link, wait_until="domcontentloaded")

        span = page.locator("h2 span").first
        date_time = await span.inner_text()
        date_time = re.sub(
            r"^(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)\s+",
            "",
            date_time
        )
        date_time = date_time.replace(" at", "")
        date_time = date_time.replace(" ET", "")
        date_time = datetime.strptime(date_time, "%m.%d.%Y %I:%M %p")

        await browser.close()
        return date_time

next_event = asyncio.run(get_next_event())
with open("scraper/scraper_data/next_event_time.txt", "w") as f:
    f.write(next_event.strftime("%Y-%m-%d %H:%M:%S"))

upload_file(
    path_or_fileobj="scraper/scraper_data/next_event_time.txt",
    path_in_repo="next_event_time.txt",
    repo_id="JunoML/MMA",
    repo_type="dataset",
)
import asyncio
from os import makedirs, listdir
from functools import partial

import bs4
import aiohttp

base_url = "https://eldritchhorror.fandom.com"
all_cards = f"{base_url}/wiki/Special:AllPages"
source_view_suffix = "?action=edit"
async def fetch(url, session):
    try:
        async with session.get(url) as response:
            return await response.text()
    except aiohttp.ClientError:
        print(f"Error fetching {url}")
        return None
async def save_card(session, card_name, card_url):
    if card_name in [file.removesuffix(".txt") for file in listdir("cards")]:
        print(f"Skipping {card_name} because it already exists...")
        return
    card_page = await fetch(f"{base_url}{card_url}{source_view_suffix}", session)
    if not card_page:
        print(f"Skipping {card_name} because the page is empty...")
        return
    card_soup = bs4.BeautifulSoup(card_page, "html.parser")
    card_text_box = card_soup.find(id="wpTextbox1").get_text()

    print(f"Writing {card_name} to file...")
    with open(f"cards/{card_name}.txt", "w+") as f:
        f.write(card_text_box)

async def main():
    async with aiohttp.ClientSession() as session:
        all_cards_page = await fetch(all_cards, session)
        soup = bs4.BeautifulSoup(all_cards_page, "html.parser").find(id="mw-content-text").find_all("a")[1:]
        cards = {link.getText(): link.get("href") for link in soup if link.get("href").startswith("/wiki/")}

        makedirs("cards", exist_ok=True)
        print(listdir("cards"))

        save_tasks = [partial(save_card, session, card_name, card_url) for card_name, card_url in cards.items()]
        await asyncio.gather(*(asyncio.create_task(task()) for task in save_tasks))
    print("Done!")
# Run the main coroutine
asyncio.run(main())

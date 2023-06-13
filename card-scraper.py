import asyncio
import json

from os import getenv, makedirs, listdir, path, remove
from functools import partial
from shutil import rmtree

from bs4 import BeautifulSoup
import aiohttp

base_url = "https://eldritchhorror.fandom.com"
all_cards = f"{base_url}/wiki/Special:AllPages"
source_view_suffix = "?action=edit"
clear_cards_folder = getenv("CLEAR_CARDS_FOLDER", False)

if clear_cards_folder:
    print("Clearing cards folder...")
    rmtree("cards")


async def fetch(url, session):
    try:
        async with session.get(url) as response:
            return await response.text()
    except aiohttp.ClientError:
        print(f"Error fetching {url}")
        return None


async def write_to_file(file, text):
    makedirs(path.dirname(file), exist_ok=True)
    with open(file, "w+") as f:
        f.write(text)

async def construct_json(horrible_formatted_text_from_hell: str):
    starts_with_blacklist = ['!', '<', '{','}']
    constructed_object = {}
    for line in horrible_formatted_text_from_hell.splitlines():
        if line.startswith(tuple(starts_with_blacklist)):continue
        if "=" in line:
            key, value = line.split("=")[0], ''.join(line.split("=")[1:])
            constructed_object[key.removeprefix("|")] = value
    return json.dumps(constructed_object, indent=4)

async def save_card(session, card_name, card_url):
    if card_name in [file.split('.')[:-1] for file in listdir("cards")]:
        print(f"Skipping {card_name} because it already exists...")
        return
    card_page = await fetch(f"{base_url}{card_url}{source_view_suffix}", session)
    if not card_page:
        print(f"Skipping {card_name} because the page is empty...")
        return
    card_soup = bs4.BeautifulSoup(card_page, "html.parser")
    card_text_box = card_soup.find(id="wpTextbox1").get_text()

    print(f"Writing {card_name} to file...")
    card_path = "cards/{card_name}"
    if card_text_box.lower().startswith("#redirect"):
        print(f"Skipping {card_name} because it is a redirect...")
        return
    if card_text_box.startswith("{{"):
        card_type = card_text_box.removeprefix(
            "{{").removeprefix('Template:').split('|')[0]
        print(f"{card_name} is of type {card_type}")
        card_path = f"cards/{card_type}/{card_name}"
    content = await construct_json(card_text_box)
    await write_to_file(card_path, content)


async def main():
    async with aiohttp.ClientSession() as session:
        all_cards_page = await fetch(all_cards, session)
        soup = BeautifulSoup(all_cards_page, "html.parser").find(
            id="mw-content-text").find_all("a")[1:]
        cards = {link.getText(): link.get("href")
                 for link in soup if link.get("href").startswith("/wiki/")}

        makedirs("cards", exist_ok=True)
        print(listdir("cards"))

        save_tasks = [partial(save_card, session, card_name, card_url)
                      for card_name, card_url in cards.items()]
        await asyncio.gather(*(asyncio.create_task(task()) for task in save_tasks))
    print("Done!")
# Run the main coroutine
asyncio.run(main())

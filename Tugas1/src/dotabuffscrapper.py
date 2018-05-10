from bs4 import BeautifulSoup
from urllib.request import urljoin
import subprocess
import os
import json
import shutil
import time
import scrapper

url_root = "https://www.dotabuff.com/"
url_dota_heroes = "https://www.dotabuff.com/heroes"
url_dota_items = "https://www.dotabuff.com/items"

url_scrape_state = "state.json"

url_data_dir = "../data/"

url_raw_dir = os.path.join(url_data_dir, "raw/")
url_raw_heroes = os.path.join(url_raw_dir, "heroes.html")
url_raw_heroes_dir = os.path.join(url_raw_dir, "heroes/")
url_raw_items = os.path.join(url_raw_dir, "items.html")
url_raw_items_dir = os.path.join(url_raw_dir, "items/")

url_scrapped_dir = os.path.join(url_data_dir, "scrapped/")
url_scrapped_heroes = os.path.join(url_scrapped_dir, "heroes.json")
url_scrapped_heroes_dir = os.path.join(url_scrapped_dir, "heroes/")
url_scrapped_items = os.path.join(url_scrapped_dir, "items.json")
url_scrapped_items_dir = os.path.join(url_scrapped_dir, "items/")

DEFAULT_STATE = {
    "state":-1,
    "status":0,
    "state-data":{}
}

state = dict(DEFAULT_STATE)

logs = True

def log(*args, **kwargs):
    if logs:
        print(*args, **kwargs)

def load_state():
    global url_scrape_state, state
    with open(url_scrape_state, 'r') as f:
        try:
            state = json.load(f)
        except:
            print("Error loading state, restarting process")

def save_state():
    global url_scrape_state, state
    with open(url_scrape_state, 'w') as f:
        json.dump(state, f, indent=4)

if os.path.exists(url_scrape_state):
    load_state()
else:
    save_state()

def save_url(url, filename):
    cmd = "curl -s {url} --output {outfile}".format(url=url, outfile=filename)
    cmd_l = cmd.split(" ")
    return subprocess.call(cmd_l) == 0

def move_state(target):
    global state, tries
    state["state"] = target
    state["status"] = 0
    save_state()
    tries = 0

running = True

if state["state"] == -2:
    state = dict(DEFAULT_STATE)
    save_state()

max_tries = 3
tries = 0

default_delay = 0.5
to_delay = 0

while running:
    tries += 1
    if to_delay > 0:
        time.sleep(to_delay)
        to_delay = 0
    try:
        if state["state"] == -1:
            if state["status"] == 0:
                log("Start scraping")
                # Clean data
                if os.path.isdir(url_data_dir):
                    log("Cleaning previous scrap data")
                    for filename in os.listdir(url_data_dir):
                        file_path = os.path.join(url_data_dir, filename)
                        try:
                            if os.path.isfile(file_path):
                                os.unlink(file_path)
                            elif os.path.isdir(file_path):
                                shutil.rmtree(file_path)
                        except:
                            pass
                # Initialize Directories
                os.makedirs(url_data_dir, exist_ok=True)
                os.makedirs(url_raw_dir, exist_ok=True)
                os.makedirs(url_raw_heroes_dir, exist_ok=True)
                os.makedirs(url_raw_items_dir, exist_ok=True)
                os.makedirs(url_scrapped_dir, exist_ok=True)
                os.makedirs(url_scrapped_heroes_dir, exist_ok=True)
                os.makedirs(url_scrapped_items_dir, exist_ok=True)
                # Finish initializing
                state["status"] = 1
                save_state()
            else:
                move_state(0)     
        elif state["state"] == 0:
            # Scrape Heroes
            if state["status"] == 0:
                log("Scrapping heroes hyperlink from {}".format(url_dota_heroes))
                if save_url(url_dota_heroes, url_raw_heroes):
                    with open(url_raw_heroes, 'r') as f:
                        html = f.read()
                        soup = BeautifulSoup(html, "html.parser")
                        heroes = soup.find("div", {"class":"hero-grid"})
                        children = heroes.findChildren("a")
                        links = []
                        for child in children:
                            link = urljoin(url_dota_heroes, child['href'])
                            name = child.find("div", {"class":"name"}).text
                            l = child['href'].split("/")
                            h_id = l.pop()
                            hero = {
                                "id": h_id,
                                "name": name,
                                "url": link
                            }
                            links.append(hero)
                        with open(url_scrapped_heroes, 'w') as f2:
                            json.dump(links, f2, indent=4)
                    # Finish scraping heroes url
                    state["state-data"] = {
                        "max": len(links),
                        "index": 0,
                        "heroes": links
                    }
                    state["status"] = 1
                    save_state()
                    to_delay = default_delay
                else:
                    log("Failed to retrieve url")
            else:
                move_state(1)
        elif state["state"] == 1:
            if state["state-data"]["index"] >= state["state-data"]["max"]:
                move_state(2)
            else:
                if state["status"] < 4:
                    index = state['state-data']["index"]
                    data = state['state-data']["heroes"][index]
                    name = data["id"]
                    url = data["url"]
                    
                    url = state['state-data']["heroes"][index]["url"]
                    url_items = url + "/items?date=year"
                    url_counters = url + "/counters?date=year"

                    f_dir = os.path.join(url_raw_heroes_dir, name)
                    os.makedirs(f_dir, exist_ok=True)
                    filename = os.path.join(f_dir, "hero.html")
                    filename_items = os.path.join(f_dir, "items.html")
                    filename_counters = os.path.join(f_dir, "counters.html")
                    filename_scrapped = os.path.join(url_scrapped_heroes_dir, name+".json")
                    if state["status"] == 0:
                        log("Downloading hero page for {}".format(name))
                        # Save the main hero page.
                        save_url(url, filename)
                        tries = 0
                        state["status"] = 1
                        save_state()
                        to_delay = default_delay
                    elif state["status"] == 1:
                        log("Downloading items page for {}".format(name))
                        # Save the items page.
                        save_url(url_items, filename_items)
                        tries = 0
                        state["status"] = 2
                        save_state()
                        to_delay = default_delay
                    elif state["status"] == 2:
                        log("Downloading counters page for {}".format(name))
                        # Save the counters page.
                        save_url(url_counters, filename_counters)
                        tries = 0
                        state["status"] = 3
                        save_state()
                        to_delay = default_delay
                    elif state["status"] == 3:
                        log("Scrapping pages for {}".format(name))
                        # Start scraping
                        with open(filename, 'r') as f:
                            page = f.read()
                        with open(filename_items, 'r') as f:
                            page_item = f.read()
                        with open(filename_counters, 'r') as f:
                            page_counter = f.read()
                        scrapped = scrapper.scrap_hero_data(page, page_item, page_counter)
                        with open(filename_scrapped, 'w') as f:
                            json.dump(scrapped, f, indent=4)
                        tries = 0
                        state["status"] = 4
                        save_state()
                else:
                    state["state-data"]["index"] += 1
                    state["status"] = 0
                    save_state() 
        elif state["state"] == -2:
            # finished
            running = False
            log("Scrapping finished")
    except Exception as e:
        print(e)
    if running and max_tries != -1 and tries >= max_tries:
        log("Max tries of a state reached. Automatically stopping")
        running = False


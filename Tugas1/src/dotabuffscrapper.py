from bs4 import BeautifulSoup
from urllib.request import urljoin
import subprocess
import os
import json
import shutil
import time
import scrapper
import sys
import display
import traceback

# Url to the website (to be scrapped from).
url_root = "https://www.dotabuff.com/"
url_dota_heroes = "https://www.dotabuff.com/heroes"
url_dota_items = "https://www.dotabuff.com/items"

# Filename for the saved state.
url_scrape_state = "state.json"

# Data directory.
url_data_dir = "data/"

# Path to raw files.
url_raw_dir = os.path.join(url_data_dir, "raw/")
url_raw_heroes = os.path.join(url_raw_dir, "heroes.html")
url_raw_heroes_dir = os.path.join(url_raw_dir, "heroes/")
url_raw_items = os.path.join(url_raw_dir, "items.html")
url_raw_items_dir = os.path.join(url_raw_dir, "items/")

# Path to scrapped files.
url_scrapped_dir = os.path.join(url_data_dir, "scrapped/")
url_scrapped_heroes = os.path.join(url_scrapped_dir, "heroes.json")
url_scrapped_heroes_dir = os.path.join(url_scrapped_dir, "heroes/")
url_scrapped_items = os.path.join(url_scrapped_dir, "items.json")
url_scrapped_items_dir = os.path.join(url_scrapped_dir, "items/")

# The title of the program.
title = "Dota 2 Data Scraper"

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
    '''
    Load state from state.json.
    '''
    global url_scrape_state, state
    with open(url_scrape_state, 'r') as f:
        try:
            state = json.load(f)
        except:
            print("Error loading state, starting a new session")

def save_state():
    '''
    Save current state to state.json.
    '''
    global url_scrape_state, state
    with open(url_scrape_state, 'w') as f:
        json.dump(state, f, indent=4)

# Loads state.json.
if os.path.exists(url_scrape_state):
    load_state()
    log("Continuing previous session")
else:
    # Create a new state.json if not found.
    save_state()

def save_url(url, filename):
    '''
    Save a url as a file.
    '''
    cmd = "curl -s {url} --output {outfile}".format(url=url, outfile=filename)
    cmd_l = cmd.split(" ")
    return subprocess.call(cmd_l) == 0

def move_state(target):
    '''
    Moves the state of the program to the specified state.
    '''
    global state, tries
    state["state"] = target
    state["status"] = 0
    save_state()
    tries = 0

running = True

if state["state"] == -2:
    print("Previous session finished, restart ? (y)")
    y = input()
    if y.lower() == "y":
        state = dict(DEFAULT_STATE)
        save_state()
    else:
        sys.exit(0)

# The number of tries (if an error occured before giving up)
max_tries = 3
tries = 0

# The default delay value.
default_delay = 0.2
# The amount of time to delay the program.
to_delay = 0

while running:
    tries += 1
    if to_delay > 0:
        # Delays the program execution.
        time.sleep(to_delay)
        to_delay = 0
    try:
        if state["state"] == -1:
            if state["status"] == 0:
                display.show([title, "Initializing"])
                # Clean data
                if os.path.isdir(url_data_dir):
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
                display.show([title, "Scrapping heroes url list"], "-", 0)
                if save_url(url_dota_heroes, url_raw_heroes):
                    with open(url_raw_heroes, 'r') as f:
                        html = f.read()
                        links = scrapper.scrap_hero_links(html, url_root)
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
                    os.unlink(url_raw_heroes)
                else:
                    log("Failed to retrieve url")
            else:
                move_state(1)
        elif state["state"] == 1:
            max_entries = state["state-data"]["max"]
            if state["state-data"]["index"] >= max_entries:
                move_state(2)
            else:
                if state["status"] < 4:
                    # Retrieve all information for the state
                    index = state['state-data']["index"]
                    data = state['state-data']["heroes"][index]
                    name = data["id"]
                    
                    # Get urls for all necessary pages.
                    url = state['state-data']["heroes"][index]["url"]
                    url_items = url + "/items?date=year"
                    url_counters = url + "/counters?date=year"

                    # Initialize directory and get filenames
                    f_dir = os.path.join(url_raw_heroes_dir, name)
                    os.makedirs(f_dir, exist_ok=True)
                    filename = os.path.join(f_dir, "hero.html")
                    filename_items = os.path.join(f_dir, "items.html")
                    filename_counters = os.path.join(f_dir, "counters.html")
                    filename_scrapped = os.path.join(url_scrapped_heroes_dir, name+".json")
                    if state["status"] == 0:
                        display.show([title, name], "Downloading hero page", (index * 4 + state["status"]) / (max_entries * 8), index, max_entries)
                        # Save the main hero page.
                        save_url(url, filename)
                        tries = 0
                        state["status"] = 1
                        save_state()
                        to_delay = default_delay
                    elif state["status"] == 1:
                        display.show([title, name], "Downloading item page", (index * 4 + state["status"]) / (max_entries * 8), index, max_entries)
                        # Save the items page.
                        save_url(url_items, filename_items)
                        tries = 0
                        state["status"] = 2
                        save_state()
                        to_delay = default_delay
                    elif state["status"] == 2:
                        display.show([title, name], "Downloading counter page", (index * 4 + state["status"]) / (max_entries * 8), index, max_entries)
                        # Save the counters page.
                        save_url(url_counters, filename_counters)
                        tries = 0
                        state["status"] = 3
                        save_state()
                        to_delay = default_delay
                    elif state["status"] == 3:
                        display.show([title, name], "Scrapping pages", (index * 4 + state["status"]) / (max_entries * 8), index, max_entries)
                        # Start scraping.
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
                        # Removes raw html files.
                        shutil.rmtree(f_dir)
                else:
                    # Advance to the next hero.
                    state["state-data"]["index"] += 1
                    state["status"] = 0
                    save_state()
        elif state["state"] == 2:
            # Scrape Items
            if state["status"] == 0:
                display.show([title, "Scrapping items url list"], "-", 0.5)
                if save_url(url_dota_items, url_raw_items):
                    with open(url_raw_items, 'r') as f:
                        html = f.read()
                        links = scrapper.scrap_item_links(html, url_root)
                        with open(url_scrapped_items, 'w') as f2:
                            json.dump(links, f2, indent=4)
                    # Finish scraping items url
                    state["state-data"] = {
                        "max": len(links),
                        "index": 0,
                        "items": links
                    }
                    state["status"] = 1
                    save_state()
                    # Adds a delay for the next step.
                    to_delay = default_delay
                    # Removes raw html files.
                    os.unlink(url_raw_items)
                else:
                    log("Failed to retrieve url")
            else:
                move_state(3)
        elif state["state"] == 3:
            max_entries = state["state-data"]["max"]
            if state["state-data"]["index"] >= max_entries:
                move_state(-2)
            else:
                if state["status"] < 2:
                    # Retrieve all information for the state
                    index = state['state-data']["index"]
                    data = state['state-data']["items"][index]
                    name = data["id"]
                    
                    # Get urls for all necessary pages.
                    url = state['state-data']["items"][index]["url"]

                    # Initialize directory and get filenames
                    f_dir = os.path.join(url_raw_items_dir, name)
                    os.makedirs(f_dir, exist_ok=True)
                    filename = os.path.join(f_dir, "item.html")
                    filename_scrapped = os.path.join(url_scrapped_items_dir, name+".json")
                    if state["status"] == 0:
                        display.show([title, name], "Downloading item page", (index * 2 + state["status"]) / (max_entries * 4) + 0.5, index, max_entries)
                        # Save the item page.
                        save_url(url, filename)
                        tries = 0
                        state["status"] = 1
                        save_state()
                        to_delay = default_delay
                    elif state["status"] == 1:
                        display.show([title, name], "Scrapping item page", (index * 2 + state["status"]) / (max_entries * 4) + 0.5, index, max_entries)
                        # Start scraping.
                        with open(filename, 'r') as f:
                            page = f.read()
                        scrapped = scrapper.scrap_item_data(page)
                        with open(filename_scrapped, 'w') as f:
                            json.dump(scrapped, f, indent=4)
                        tries = 0
                        state["status"] = 2
                        save_state()
                        # Removes raw html files.
                        shutil.rmtree(f_dir)
                else:
                    # Advance to the next item.
                    state["state-data"]["index"] += 1
                    state["status"] = 0
                    save_state()
        elif state["state"] == -2:
            # finished
            running = False
            display.show([title, "Finished"], "-", 1)
    except Exception as e:
        print(e)
        traceback.print_exc()
    if running and max_tries != -1 and tries >= max_tries:
        # Stop the programs if it is not making any progress
        log("Max tries of a state reached. Automatically stopping")
        running = False


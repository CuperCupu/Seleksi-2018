from bs4 import BeautifulSoup
import sys, os, re
import json
from urllib.request import urljoin
import display

def scrap_hero_links(page, baselink):
    soup = BeautifulSoup(page, "html.parser")
    heroes = soup.find("div", {"class":"hero-grid"})
    children = heroes.findChildren("a")
    links = []
    for child in children:
        link = urljoin(baselink, child['href'])
        name = child.find("div", {"class":"name"}).text
        l = child['href'].split("/")
        h_id = l.pop()
        hero = {
            "id": h_id,
            "name": name,
            "url": link
        }
        links.append(hero)
    return links

def scrap_hero_data(page, page_item, page_counter):
    data = {}
    soup = BeautifulSoup(page, "html.parser")
    # Scrap hero name
    title = soup.find("div", {"class":"header-content-title"})
    cat_text = title.find("small").text
    name = title.find("h1").text
    data["name"] = name[:len(name)-len(cat_text)]
    data["category"] = cat_text.split(", ")
    # Scrap secondary data
    secondary = soup.find("div", {"class":"header-content-secondary"})
    for dl in secondary.find_all("dl"):
        dd = dl.find("dd").text
        dt = dl.find("dt").text.lower().replace(" ", "-")
        data[dt] = dd
    # Scrap hero attributes
    data['attributes'] = {}
    attr = soup.find("section", {"class":"hero_attributes"})
    attr_table = attr.find("tbody")
    primary = ""
    for k in attr_table['class']:
        match = re.match("primary-(.*)", k)
        if match:
            primary = match.group(1)
            break
    data['attributes']['primary'] = primary
    attr_data = attr_table.find_all("tr")[1]
    for att in ['str', 'agi', 'int']:
        text = attr_data.find("td", {"class":att}).text
        d = text.split()
        data['attributes'][att] = {
            "base": int(d[0]),
            "growth": float(d[1])
        }
    # Scrap used items
    soup2 = BeautifulSoup(page_item, "html.parser")
    items = soup2.find("table", {"class":"sortable"}).find("tbody")
    data["items"] = []
    for item in items.find_all("tr"):
        col = item.find_all("td")
        d_item = {}
        d_item['name'] = col[1].text
        d_item['matches'] = int(col[2].text.replace(",", ""))
        d_item['win-rate'] = col[3].text
        data["items"].append(d_item)
    soup3 = BeautifulSoup(page_counter, "html.parser")
    matchups = soup3.find("table", {"class":"sortable"}).find("tbody")
    # Scrap matchup
    data["matchups"] = []
    for matchup in matchups.find_all("tr"):
        col = matchup.find_all("td")
        d_item = {}
        d_item['name'] = col[1].text
        d_item['disadvantages'] = col[2].text
        d_item['win-rate'] = col[3].text
        d_item['matches'] = int(col[4].text.replace(",", ""))
        data["matchups"].append(d_item)
    return data

def scrap_item_links(page, baselink):
    data = []
    # Scraps items links
    soup = BeautifulSoup(page, "html.parser")
    items = soup.find("table", {"class":"sortable"}).find("tbody")
    for item in items.find_all("tr"):
        col = item.find_all("td")
        l = col[1].find("a")['href'].split("/")
        i_id = l.pop()
        d_item = {
            'id': i_id,
            'name': col[1].text,
            'used': int(col[2].text.replace(",", "")),
            'use-rate': col[3].text,
            'win-rate': col[4].text,
            'url': urljoin(baselink, col[1].find("a")['href']),
        }
        data.append(d_item)
    return data

def scrap_item_data(page):
    data = {}
    soup = BeautifulSoup(page, "html.parser")
    # Scraps item information
    desc = soup.find("div", {"class":['item-tooltip', 'reborn-tooltip']})
    data['name'] = desc.find("div", {"class":"name"}).text
    try:
        data['price'] = int(desc.find("div", {"class":"price"}).text.replace(",",""))
    except:
        pass
    div = desc.find("div", {"class":"stats"})
    if div:
        stats = []
        for d in div.find_all("div"):
            stats.append(d.text)
        data['stats'] = stats
    div = desc.find("div", {"class":"description"})
    if div:
        descs = []
        for d in div.find_all("div", {"class":"description-block"}):
            attrs = []
            for attr in d.attrs['class']:
                if attr:
                    attrs.append(attrs)
            if len(attrs) == 2:
                special = d.attrs['class'][1]
                spec_data = {}
                t = d.find("div")
                title = d.find("div").text
                text = d.text[len(title):]
                spec_data['name'] = title.split(':')[1].strip()
                spec_data['description'] = text
                data[special] = spec_data
            else:
                descs.append(d.text)
        if descs:
            data['description'] = descs
    div = desc.find("div", {"class":"cooldown"})
    if div:
        splits = div.text.split(' ')
        if len(splits) == 1:
            data['cooldown'] = float(div.text)
        else:
            d = div.find("span", {"class":"number"})
            data['cooldown'] = float(d.text)
    div = desc.find("div", {"class":"manacost"})
    if div:
        splits = div.text.split(' ')
        if len(splits) == 1:
            data['manacost'] = int(div.text)
        else:
            d = div.find("span", {"class":"number"})
            data['manacost'] = int(d.text)
    div = desc.find("div", {"class":"notes"})
    if div:
        data['notes'] = div.text
    div = desc.find("div", {"class":"lore"})
    if div:
        data['lore'] = div.text
    # Scraps heroes usage
    items = soup.find("table", {"class":"sortable"})
    if items:
        items = items.find("tbody")
        data["used-by"] = []
        for item in items.find_all("tr"):
            col = item.find_all("td")
            d_item = {
                'name': col[1].text,
                'matches': int(col[2].text.replace(",", "")),
                'wins': int(col[3].text.replace(",", "")),
            }
            data["used-by"].append(d_item)
    return data

if __name__ == "__main__":
    args = sys.argv
    mode = 0
    if len(args) > 1:
        if args[1] == "--list-items":
            mode = 1
        elif args[1] == "--items":
            mode = 2
        elif args[1] == "--list-heroes":
            mode = 3
        elif args[1] == "--heroes":
            mode = 4
    if mode == 0:
        print("usage:")
        print("--items item_page [json_filename]")
        sys.exit(0)
    if mode == 1:
        if len(args) > 3:
            if not os.path.isfile(args[2]):
                print("file {} not found".format(args[2]))
                sys.exit(0)
            else:
                with open(args[2], 'r') as f:
                    page = f.read()
                scrapped = scrap_item_links(page, args[3])
                if len(args) > 4:
                    with open(args[4], 'w') as f2:
                        json.dump(scrapped, f2, indent=4)
                else:
                    print(scrapped)
    elif mode == 2:
        if len(args) > 2:
            if not os.path.isfile(args[2]):
                print("file {} not found".format(args[2]))
                sys.exit(0)
            else:
                with open(args[2], 'r') as f:
                    page = f.read()
                scrapped = scrap_item_data(page)
                if len(args) > 3:
                    with open(args[3], 'w') as f2:
                        json.dump(scrapped, f2, indent=4)
                else:
                    print(scrapped)
    elif mode == 3:
        if len(args) > 3:
            if not os.path.isfile(args[2]):
                print("file {} not found".format(args[2]))
                sys.exit(0)
            else:
                with open(args[2], 'r') as f:
                    page = f.read()
                scrapped = scrap_hero_links(page, args[3])
                if len(args) > 4:
                    with open(args[4], 'w') as f2:
                        json.dump(scrapped, f2, indent=4)
                else:
                    print(scrapped)
    elif mode == 4:
        if len(args) > 4:
            if not os.path.isfile(args[2]):
                print("file {} not found".format(args[2]))
                sys.exit(0)
            elif not os.path.isfile(args[3]):
                print("file {} not found".format(args[3]))
                sys.exit(0)
            elif not os.path.isfile(args[4]):
                sys.exit(0)
                print("file {} not found".format(args[4]))
            else:
                with open(args[2], 'r') as f:
                    page = f.read()
                with open(args[3], 'r') as f:
                    page_item = f.read()
                with open(args[4], 'r') as f:
                    page_counter = f.read()
                scrapped = scrap_hero_data(page, page_item, page_counter)
                if len(args) > 5:
                    with open(args[4], 'w') as f2:
                        json.dump(scrapped, f2, indent=4)
                else:
                    print(scrapped)

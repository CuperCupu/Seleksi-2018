from bs4 import BeautifulSoup
import sys, os, re
import json

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

if __name__ == "__main__":
    args = sys.argv
    if len(args) > 3:
        if os.path.isfile(args[1]):
            with open(args[1], 'r') as f:
                page = f.read()
            with open(args[2], 'r') as f:
                page_item = f.read()
            with open(args[3], 'r') as f:
                page_counter = f.read()
            scrapped = scrap_hero_data(page, page_item, page_counter)
            if len(args) > 4:
                with open(args[4], 'w') as f2:
                    json.dump(scrapped, f2, indent=4)
            else:
                print(scrapped)
        else:
            print("file {} not found".format(args[1]))
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import csv
import re

def get_all_fight_stats():
    html = requests.get("http://ufcstats.com/statistics/events/completed?page=all").content
    soup = BeautifulSoup(html, features="lxml")
    all_events = soup.select("tbody tr")
    for event in all_events:
        if not event.select("span"): continue
        if event.select("img.b-statistics__icon"): continue #future events
        event_name = event.select("a.b-link")[0].text.strip()
        event_url = event.select("a.b-link")[0]["href"]
        event_date = event.select("span.b-statistics__date")[0].text.strip()
        date = datetime.strptime(event_date, "%B %d, %Y").strftime("%Y%m%d")
        print(date, event_name)
        event_data = {
            "event": event_name,
            "event_url": event_url,
            "event_date": date
        }
        for fight_data in get_event_fight_stats(event_url):
            yield {
                **event_data,
                **fight_data,
            }

def get_event_fight_stats(event_url):
    html = requests.get(event_url).content
    soup = BeautifulSoup(html, features="lxml")
    all_fights = soup.select("tbody tr")
    for fight in all_fights:
        fight_url = fight["data-link"]
        details = get_fight_details(fight_url)
        
        all_cells = fight.select("td")
        if len(all_cells) < 7:
            raise
        result_raw_text = all_cells[0].text.strip()
        result = list(set(result_raw_text.split()))
        if len(result) > 1: raise
        if result[0] == "nc": continue
        result_numeric = {"win":1,"draw":0.5}[result[0]]
        
        fight_data = {
            "fighter1": all_cells[1].select("p")[0].text.strip(),
            "fighter2": all_cells[1].select("p")[1].text.strip(),
            "division": all_cells[6].text.strip(),
            "result": result_numeric,
            "method": all_cells[7].text.strip().split()[0],
            "round": all_cells[8].text.strip(),
            "time": all_cells[9].text.strip(),
            **details
        }
        yield fight_data

def get_fight_details(fight_url):
    html = requests.get(fight_url).content
    soup = BeautifulSoup(html, features="lxml")

    division = soup.select("i.b-fight-details__fight-title")[0].text.strip()

    #overall info
    details, outcome = soup.select("div.b-fight-details__content p")

    info = [[y.strip() for y in x.text.split(":",1)] for x in details.findChildren(recursive=False)]
    outcome = [y.strip() for y in outcome.text.strip().split(":",1)]
    info.append(outcome)
    info = dict(info)
    
    match = re.findall("(\d+) - (\d+)",info["Details"])
    if match:
        if len(match) != 3:
            print(f"expected three judges but {len(match)} found. scores: {match}")
            raise
        #judge scoring
        info["Judges"] = [int(x[0])-int(x[1]) for x in match]
    else:
        info["Judges"] = ["","",""]

    fighter1 = {}
    fighter2 = {}

    if "Round-by-round stats not currently available." not in soup.select("section.b-fight-details__section")[0].text:
        #fighter stats
        headers = [x.text.strip() for x in soup.select("thead.b-fight-details__table-head")[0].select("tr th")]
        values = list(zip(*[[p.text.strip() for p in x.select("p")] for x in soup.select("tbody.b-fight-details__table-body")[0].select("tr td")]))

        fighter1 = dict(zip(headers, values[0]))
        fighter2 = dict(zip(headers, values[1]))

    fight_types = {
        "5 Rnd (5-5-5-5-5)": {"rounds": 5, "minutes": 5},
        "3 Rnd (5-5-5)": {"rounds": 3, "minutes": 5},
        "3 Rnd + OT (5-5-5-5)": {"rounds": 3, "minutes": 5},
        "2 Rnd (5-5)": {"rounds": 2, "minutes": 5},
        "1 Rnd + 2OT (15-3-3)": {"rounds": 1, "minutes": 15},
        "1 Rnd + OT (12-3)": {"rounds": 1, "minutes": 12},
        "1 Rnd (12)": {"rounds": 1, "minutes": 12},
        '1 Rnd + OT (15-3)': {"rounds": 1, "minutes": 15},
        '1 Rnd (15)': {"rounds": 1, "minutes": 15},
        '1 Rnd + 2OT (24-3-3)': {"rounds": 1, "minutes": 24},
        '1 Rnd (10)': {"rounds": 1, "minutes": 10},
        '1 Rnd + OT (27-3)': {"rounds": 1, "minutes": 27},
        '1 Rnd (18)': {"rounds": 1, "minutes": 18},
        '1 Rnd + OT (30-5)': {"rounds": 1, "minutes": 30},
        '1 Rnd + OT (30-3)': {"rounds": 1, "minutes": 30},
        '1 Rnd (20)': {"rounds": 1, "minutes": 20},
        '1 Rnd (30)': {"rounds": 1, "minutes": 30},
        '1 Rnd + OT (31-5)': {"rounds": 1, "minutes": 31},
        'No Time Limit': {"rounds": 1, "minutes": 60} #not sure what to do here
    }

    def parse_minutes(s):
        minutes = s.split(":")[0]
        seconds = s.split(":")[1]
        return str(int(minutes) * 60 + int(seconds))

    output = {
        "num_rounds": fight_types[info["Time format"]]["rounds"],
        "num_minutes": fight_types[info["Time format"]]["minutes"],
        "judge1": info["Judges"][0],
        "judge2": info["Judges"][1],
        "judge3": info["Judges"][2],
    }

    return output
    
if __name__ == "__main__":
    with open("ufc.csv","w") as f_out:
        writer = csv.DictWriter(f_out, fieldnames=["event","event_url","event_date","fighter1","fighter2","division","result","method","round","time","num_rounds","num_minutes","judge1","judge2","judge3"])
        writer.writeheader()
        for fight in get_all_fight_stats():
            writer.writerow(fight)


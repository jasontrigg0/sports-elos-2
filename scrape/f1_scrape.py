import requests
import json
import re
import csv
import datetime

def get_all_events(year):
    url = f"https://www.formula1.com/en/results/{year}/races"

    headers = {
        "rsc": "1"
    }

    response = requests.get(url, headers=headers)

    for l in response.text.split("\n"):
        if re.findall("^2:",l):
            l = l.replace("2:","")
            data = json.loads(l)
            for race in data[1][0][3]["children"][2][3]["content"]:
                yield {
                    "id": race["value"],
                    "name": race["text"],
                }

def constructor_to_id(constructor):
    mappings = {
        "Sauber": "Sauber",
        "Sauber Mercedes": "Sauber",
        "Sauber Ford": "Sauber",
        "Sauber Petronas": "Sauber",
        "Sauber BMW": "Sauber",
        "Sauber Ferrari": "Sauber",
        "Alfa Romeo Racing Ferrari": "Sauber",
        "Alfa Romeo Ferrari": "Sauber",
        "McLaren Ford": "McLaren",
        "McLaren Serenissima": "McLaren",
        "McLaren Ford": "McLaren",
        "McLaren BRM": "McLaren",
        "Eagle Weslake": "McLaren",
        "McLaren Alfa Romeo": "McLaren",
        "McLaren TAG": "McLaren",
        "McLaren Honda": "McLaren",
        "McLaren Peugeot": "McLaren",
        "McLaren Mercedes": "McLaren",
        "McLaren Honda": "McLaren",
        "McLaren Renault": "McLaren",
    }

    return mappings.get(constructor, constructor)
                
def get_event_results(year, event_id, event_name):
    url = f'https://www.formula1.com/en/results/{year}/races/{event_id}/{event_name}/race-result?_rsc=m68ps'
    
    headers = {
        "rsc": "1",
        "next-router-state-tree": "%5B%22%22%2C%7B%22children%22%3A%5B%22(pages)%22%2C%7B%22children%22%3A%5B%5B%22locale%22%2C%22en%22%2C%22d%22%5D%2C%7B%22children%22%3A%5B%22results%22%2C%7B%22children%22%3A%5B%5B%22season%22%2C%222023%22%2C%22d%22%5D%2C%7B%22children%22%3A%5B%5B%22pageType%22%2C%22races%22%2C%22d%22%5D%2C%7B%22children%22%3A%5B%5B%22contentId%22%2C%221141%22%2C%22d%22%5D%2C%7B%22children%22%3A%5B%5B%22contentName%22%2C%22bahrain%22%2C%22d%22%5D%2C%7B%22children%22%3A%5B%5B%22pageSlug%22%2C%22race-result%22%2C%22d%22%5D%2C%7B%22children%22%3A%5B%22__PAGE__%22%2C%7B%7D%2C%22%2Fen%2Fresults%2F2023%2Fraces%2F1141%2Fbahrain%2Frace-result%22%2C%22refetch%22%5D%7D%5D%7D%5D%7D%5D%7D%5D%7D%5D%7D%5D%7D%5D%7D%5D%7D%5D"
    }
    
    response = requests.get(url, headers=headers)

    for l in response.text.split("\n"):
        if "Standings" in l:
            l = l.replace("2:","")
            data = json.loads(l)
            info = data[1][1][3]["children"][3]["children"]
            date_str = info[1][3]["children"][0][3]["children"]
            if "-" in date_str:
                date_str = date_str.split("-")[1].strip()
            date = datetime.datetime.strptime(date_str, "%d %b %Y").strftime("%Y%m%d")
            
            results = info[2][3]["children"][1][3]["children"]
            if type(results) is str and "Results for this session" in str(results) and "available yet." in str(results):
                print(f"No results for {event_name}, skipping...")
                return
            rows = results[3]["children"][1][3]["children"]
            for r in rows:
                cols = r[3]["children"]
                position = cols[0][3]["children"][3]["children"]
                first_name = cols[2][3]["children"][3]["children"][0][3]["children"].strip()
                last_name = cols[2][3]["children"][3]["children"][2][3]["children"].strip()
                driver_id = cols[2][3]["children"][3]["children"][3][3]["children"]
                constructor = cols[3][3]["children"][3]["children"][0]
                time = cols[5][3]["children"][3]["children"]
                yield {
                    "year": year,
                    "date": date,
                    "event_id": event_id,
                    "event_name": event_name,
                    "position": position,
                    "driver": " ".join([first_name, last_name]),
                    "constructor": constructor,
                    "time": time,
                }
    

if __name__ == "__main__":
    # for year in range(1950, 2026):
    for year in range(2025, 2026):
        print(year)
        with open(f"../data/f1/f1_{year}.csv","w") as f_out:
            writer = csv.DictWriter(f_out, fieldnames=["year","date","event_id","event_name","position","driver","constructor","time"])
            writer.writeheader()
            for event in get_all_events(year):
                event_id = event["id"]
                event_name = event["name"].lower().replace(" ","-")
                print(year, event_name)
                for result in get_event_results(year, event_id, event_name):
                    writer.writerow(result)

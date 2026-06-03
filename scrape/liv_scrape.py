import requests
import json
import re
import csv

def get_event_results(year, event_name, event_id):
    url = f"https://www.livgolf.com/leaderboard/{year}/{event_name}"

    headers = {
        "content-type": "text/plain;charset=UTF-8",
        "next-action": "7028e3d76d33bd5ff784a9adcfa6db6d8a6befbb9f",
    }

    payload = f"[{event_id},{year},null]"
    
    response = requests.post(url, headers=headers, data=payload)

    matches = [l for l in response.text.split("\n") if "playoff" in l]

    if len(matches) != 1:
        raise Exception("New format")

    l = matches[0]
    l = re.sub("^.+?:","",l)
    data = json.loads(l)

    all_players = data["all"]["players"]

    if data["playoff"] != "$undefined":
        all_players += data["playoff"]["players"]
    
    for player in all_players:
        if "playoff" in player["rounds"]: continue #player information found in the playoff section
        for i,score in enumerate(player["rounds"]):
            if score == None: continue
            yield {
                "player_id": player["playerId"],
                "player_name": player["player"],
                "round": (i+1),
                "score": score
            }
    
                
def get_all_events(year):
    url = "https://www.livgolf.com/leaderboard"
    params = {
        "_rsc": "qmbzs"
    }

    headers = {
        "rsc": "1",
        "next-router-segment-prefetch": "/!KG1haW4p/!KGdsb2JhbCk/leaderboard/__PAGE__",
        "next-router-prefetch": "1",
    }
    
    response = requests.get(url, params=params, headers=headers)
    for l in response.text.split("\n"):
        if "seasonsWithEvents" in l:
            l = re.sub("^.+?:","",l)
            data = json.loads(l)
            all_seasons = data["rsc"][3]["children"][0][3]["children"][1][3]["seasonsWithEvents"]
            for season in all_seasons:
                if season["season"] != year: continue
                for e in season["events"]:
                    event_id = e["id"]
                    event_name = e["event"]
                    print(event_name, event_id)
                    start_date = e["startDate"].split("T")[0].replace("-","")
                    yield {
                        "event_id": event_id,
                        "event_name": event_name,
                        "start_date": start_date,
                    }
                
            
if __name__ == "__main__":
    # for year in range(2022, 2026):
    for year in range(2026, 2027):
        print(year)
        writer = csv.DictWriter(open(f"../data/liv/liv_{year}.csv",'w'),fieldnames=["player_id", "player_name", "event_id", "event_name", "start_date", "round", "score"])
        writer.writeheader()
        events = get_all_events(year)
        for e in events:
            print(e)
            #skip team championships and other year end events without good data
            if e["event_name"] in ["miami-2022","miami-2023","liv-golf-team-championship-dallas-2024","promotions-event-2024"]: continue
            for result in get_event_results(year, e["event_name"], e["event_id"]):
                row = {**e, **result}
                writer.writerow(row)

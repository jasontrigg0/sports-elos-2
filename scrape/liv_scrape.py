import requests
import json
import re
import csv

def get_event_results(event_name):
    url = f"https://www.livgolf.com/schedule/{event_name}/leaderboard?_rsc=k4aap"

    headers = {
        "RSC": "1",
    }

    response = requests.get(url, headers=headers)

    matches = [l for l in response.text.split("\n") if "playersLeaderboard" in l]

    if len(matches) != 1:
        raise Exception("New format")

    l = matches[0]
    l = re.sub("^.+?:","",l)
    data = json.loads(l)
    for player in data[3]["leaderboardResult"]["playersLeaderboard"]:
        if player["rounds"] == None: continue
        for round_ in player["rounds"]:
            score = round_["score"]

            if score == "E":
                score = 0
            else:
                score = score.replace("+","")

            if score == "-": continue
                
            yield {
                "player_id": player["player_id"],
                "player_name": " ".join([player["first_name"],player["last_name"]]),
                "round": round_["round_number"],
                "score": score
            }
    
                
def get_all_events(year):
    url = "https://www.livgolf.com/schedule"
    headers = {
        "Next-Action": "7fd51be4e2065909862fab9779e033675be9fa07b6",
    }
    payload = f'''["{year}",[]]'''
    response = requests.post(url, headers=headers, data=payload)
    for l in response.text.split("\n"):
        if "completedEvents" in l:
            l = re.sub("^(.*?){","{",l)
            data = json.loads(l)
            for e in data["completedEvents"]:
                event_name = e["entity"]["slug"]
                event_id = e["entity"]["fields"]["livEventId"]
                print(event_name, event_id)
                start_date = e["entity"]["fields"]["startDate"].split("T")[0].replace("-","")
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
            #skip team championships and other year end events without good data
            if e["event_name"] in ["miami-2022","miami-2023","liv-golf-team-championship-dallas-2024","promotions-event-2024"]: continue
            for result in get_event_results(e["event_name"]):
                row = {**e, **result}
                writer.writerow(row)

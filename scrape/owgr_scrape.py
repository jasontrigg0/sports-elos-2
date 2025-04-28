import requests
from bs4 import BeautifulSoup
import re
import csv

def get_all_event_info(year, token):
    #owgr goes back to the 80s but doesn't have round-by-round data until 2006
    event_list = requests.get(f"https://apiweb.owgr.com/api/owgr/events/getEventsToDate?year={year}&pageSize=0&pageNumber=1&tourId=0&sortString=WeekNumber+DESC,+Winners[0].PointsAwarded+DESC").json()["eventsList"]
    for event in event_list:
        for row in get_event_info(event["id"], token):
            yield row

def get_token():
    #can find token by visiting https://www.owgr.com/events-to-date
    #then clicking on an event which will trigger an request that includes the token
    data = requests.get("https://www.owgr.com/events-to-date").text
    return re.findall("/_next/static/([^/]*?)/_buildManifest.js",data)[0]
            
def get_event_info(event_id, token):
    print(f"pulling event {event_id}")
    data = requests.get(f"https://www.owgr.com/_next/data/{token}/events/{event_id}.json?slug={event_id}").json()
    event_details = data["pageProps"]["eventDetailsData"]["eventDetails"]
    start_date = event_details["startDate"].split("T")[0].replace("-","")
    results = event_details["results"]

    #skipping players who withdrew from the tournament. they may include partial rounds and don't know a way to distinguish those rounds otherwise
    #results = [res for res in results if res["nonFinishingState"] != "WD"]
    
    round_scores = {}
    round_averages = {}
    for res in results:
        for x in res["resultScores"]:
            round_scores.setdefault(x["roundNumber"],[]).append(x["score"])

    for rnd in round_scores:
        round_averages[rnd] = sum(round_scores[rnd]) / len(round_scores[rnd])
            
    for res in results:
        player_id = res["player"]["id"]
        player_name = res["player"]["fullName"]

        for x in res["resultScores"]:
            rnd = x["roundNumber"]
            if round_averages[rnd] < 60:
                print(f'skipping event {event_id}, round {rnd}, with average score {round_averages[rnd]}')
                continue

            if x["score"] < 50:
                print(f'skipping event {event_id}, player {player_name} with score {x["score"]}')
                continue
        
            yield {
                "player_id": player_id,
                "player_name": player_name,
                "start_date": start_date,
                "event_id": event_id,
                "round": x["roundNumber"],
                "score": x["score"]
            }

if __name__ == "__main__":
    token = get_token()
    # for year in range(2006,2025):
    for year in range(2025,2026):
        writer = csv.DictWriter(open(f"/files/git/sports-elos-2/data/owgr/owgr_{year}.csv",'w'),fieldnames=["player_id", "player_name", "event_id", "start_date", "round", "score"])
        writer.writeheader()
        for row in get_all_event_info(year, token):
            writer.writerow(row)

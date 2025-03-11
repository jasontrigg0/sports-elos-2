import csv
import requests

def get_all_liv_rows():
    for event in get_all_liv_events():
        start_date = event["startDate"].split("T")[0].replace("-","")
        for row in get_liv_event_data(event["year"], event["eventId"], start_date):
            yield row


def get_all_liv_events():
    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/118.0',
        'Accept': '*/*',
        'Accept-Language': 'en-US,en;q=0.5',
        # 'Accept-Encoding': 'gzip, deflate, br',
        'Referer': 'https://www.livgolf.com/',
        'Origin': 'https://www.livgolf.com',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-site',
        'Pragma': 'no-cache',
        'Cache-Control': 'no-cache',
        # Requests doesn't support trailers
        # 'TE': 'trailers',
    }

    for year in [2022,2023,2024]:
        for event in (requests.get(f'https://web-common.livgolf.com/api/events/previous/{year}', headers=headers)).json():
            yield {**event, "year": year}

def get_liv_event_data(year, event_id, start_date):
    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/118.0',
        'Accept': '*/*',
        'Accept-Language': 'en-US,en;q=0.5',
        # 'Accept-Encoding': 'gzip, deflate, br',
            'Access-Control-Request-Method': 'GET',
        'Access-Control-Request-Headers': 'x-cf-preview',
        'Referer': 'https://www.livgolf.com/',
        'Origin': 'https://www.livgolf.com',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-site',
        'Pragma': 'no-cache',
        'Cache-Control': 'no-cache',
        # Requests doesn't support trailers
        # 'TE': 'trailers',
    }

    event = requests.get(f'https://web-common.livgolf.com/api/leaderboard/players/{event_id}', headers=headers).json()

    for player_result in event["players"]:
        for round_ in player_result["rounds"]:
            if round_["id"] == "301": continue #this is the total score
            if round_["id"] == "201": continue #not sure about this one but only one instance
            
            score = round_["score"]

            if score == "": #player didn't play this round (why?)
                continue

            if score == "E":
                score = 0
            else:
                score = score.replace("+","")

            yield {
                "player_id": player_result["id"],
                "player_name": player_result["name"],
                "event_id": event_id,
                "round": round_["id"],
                "score": score,
                "start_date": start_date
            }


if __name__ == "__main__":
    writer = csv.DictWriter(open("/tmp/liv.csv",'w'),fieldnames=["player_id", "player_name", "event_id", "start_date", "round", "score"])
    writer.writeheader()
    for row in sorted(get_all_liv_rows(), key=lambda x: (dict(x)["event_id"], dict(x)["round"])):
        writer.writerow(row)

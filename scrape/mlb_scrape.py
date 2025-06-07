import requests
from bs4 import BeautifulSoup
import csv
import time
import re

REQUEST_HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:72.0) Gecko/20100101 Firefox/72.0"
}

def scrape_games(year):
    time.sleep(2)
    url = f'https://www.baseball-reference.com/leagues/MLB/{year}-schedule.shtml'
    html = requests.get(url, headers = REQUEST_HEADERS).content

    soup = BeautifulSoup(html, features="lxml")
    output = []
    for game_day in soup.select('div.section_wrapper div.section_content > div'):
        if "Today's Games" in game_day.text: continue
        
        date = game_day.select("a")[-1]["href"].split("=")[-1].replace("-","")
        for game in game_day.select("p.game"):
            if "(Spring)" in game.text: continue
            if "Preview" in game.text: continue
            
            print(game.select("a"))
            away_team = game.select('a')[0]["href"].split("/")[2]
            home_team = game.select('a')[1]["href"].split("/")[2]

            if len(game.select('a')) == 3:
                game_url = game.select('a')[2]["href"]
            else:
                game_url = ""
                
            scores = re.findall(r"\(\d+\)",game.text)
            away_score = scores[0].replace("(","").replace(")","")
            home_score = scores[1].replace("(","").replace(")","")

            # if (not home_score or not away_score):
            #     continue
        
            output.append({
                "game_url": game_url,
                "date": date,
                "home_team": home_team,
                "away_team": away_team,
                "home_score": home_score,
                "away_score": away_score
            })

    return output

if __name__ == "__main__":
    # for year in range(1876,2025):
    for year in range(2025,2026):
        print(year)
        with open(f"../data/mlb/mlb_{year}.csv","w") as f_out:
            writer = csv.DictWriter(f_out, fieldnames=["year","game_url","date","home_team","away_team","home_score","away_score"])
            writer.writeheader()
            for game in scrape_games(year):
                writer.writerow({"year":year,**game})

import requests
from bs4 import BeautifulSoup
import csv
import time
import re

REQUEST_HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:72.0) Gecko/20100101 Firefox/72.0"
}

def scrape_games(url):
    time.sleep(2)
    url = f'https://www.hockey-reference.com/leagues/NHL_{year+1}_games.html'
    html = requests.get(url, headers = REQUEST_HEADERS).content

    soup = BeautifulSoup(html, features="lxml")
    output = []
    for game in soup.select('tbody tr:not(.thead)'):
        game_link = game.select('th[data-stat="date_game"] a')
        if not game_link: continue
        
        date = game_link[0].text.replace("-","")
        game_url = game_link[0]["href"]
        date = re.findall("\d{8}",game_url)[0]
        
        home_team = game.select('td[data-stat="home_team_name"] a')[0]["href"]
        home_team = home_team.split("/")[2]
        away_team = game.select('td[data-stat="visitor_team_name"] a')[0]["href"]
        away_team = away_team.split("/")[2]
        home_score = game.select('td[data-stat="home_goals"]')[0].text
        away_score = game.select('td[data-stat="visitor_goals"]')[0].text

        if (not home_score or not away_score):
            continue
        
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
    # for year in range(1917,2025):
    for year in range(2024,2025):
        print(year)
        with open(f"../data/nhl/nhl_{year}.csv","w") as f_out:
            writer = csv.DictWriter(f_out, fieldnames=["year","game_url","date","home_team","away_team","home_score","away_score"])
            writer.writeheader()
            for game in scrape_games(year):
                writer.writerow({"year":year,**game})

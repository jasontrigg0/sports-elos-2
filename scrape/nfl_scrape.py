import requests
from bs4 import BeautifulSoup
import csv
import time

REQUEST_HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:72.0) Gecko/20100101 Firefox/72.0"
}

def scrape_teams(year):
    url = f'https://www.pro-football-reference.com/years/{year}/'
    html = requests.get(url, headers = REQUEST_HEADERS).content
    soup = BeautifulSoup(html, features="lxml")
    allTeamUrls = [x["href"] for x in soup.select('th[data-stat="team"] a')]
    return allTeamUrls;

def scrape_games(year):
    time.sleep(10)
    url = f'https://www.pro-football-reference.com/years/{year}/games.htm';
    html = requests.get(url, headers = REQUEST_HEADERS).content

    soup = BeautifulSoup(html, features="lxml")
    output = []
    for game in soup.select('tbody tr:not(.thead)'):
        if game.select('td[data-stat="game_date"]')[0].text == "Playoffs": continue
        
        winner_url = game.select('td[data-stat="winner"] a')[0]["href"]
        loser_url = game.select('td[data-stat="loser"] a')[0]["href"]
        winner = winner_url.split("/")[2].upper()
        loser = loser_url.split("/")[2].upper()

        location = game.select('td[data-stat="game_location"]')[0].text
        winner_score = game.select('td[data-stat="pts_win"]')[0].text
        loser_score = game.select('td[data-stat="pts_lose"]')[0].text

        winner_yards = game.select('td[data-stat="yards_win"]')[0].text
        loser_yards = game.select('td[data-stat="yards_lose"]')[0].text
        
        game_url = game.select('td[data-stat="boxscore_word"] a')[0]["href"]
        date = game_url.split("/")[2][:8]

        home_team  = loser if location == "@" else winner
        away_team  = winner  if location == "@" else loser
        home_score = loser_score if location == "@" else winner_score
        away_score = winner_score if location == "@" else loser_score
        home_yards = loser_yards if location == "@" else winner_yards
        away_yards = winner_yards if location == "@" else loser_yards
        
        output.append({
            "game_url": game_url,
            "date": date,
            "home_team": home_team,
            "away_team": away_team,
            "home_score": home_score,
            "away_score": away_score,
            "home_yards": home_yards,
            "away_yards": away_yards,
        })

    return output

if __name__ == "__main__":
    with open("nfl.csv","w") as f_out:
        writer = csv.DictWriter(f_out, fieldnames=["year","game_url","date","home_team","away_team","home_score","away_score","home_yards","away_yards"])
        writer.writeheader()
        for year in range(1922,2025):
            for game in scrape_games(year):
                writer.writerow({"year":year,**game})

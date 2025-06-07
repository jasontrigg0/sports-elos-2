import requests
from bs4 import BeautifulSoup
import time
import re
import csv

REQUEST_HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:72.0) Gecko/20100101 Firefox/72.0"
}

def scrape_games(year):
    time.sleep(2)
    url = f'https://www.sports-reference.com/cfb/years/{year}-schedule.html'
    html = requests.get(url, headers=REQUEST_HEADERS).content

    soup = BeautifulSoup(html, features="lxml")

    for game in soup.select('tbody tr:not(.thead)'):
        game_url = game.select('td[data-stat="date_game"] a')[0]["href"]
        date = re.findall(r"\d{4}-\d{2}-\d{2}",game_url)[0].replace("-","")

        is_home = game.select('td[data-stat="game_location"]')[0].text == ""
        is_neutral = game.select('td[data-stat="game_location"]')[0].text == "N"

        winner_team = game.select('td[data-stat="winner_school_name"]')[0].text
        winner_team = re.sub(r"\(\d+\)","",winner_team).strip()
        loser_team = game.select('td[data-stat="loser_school_name"]')[0].text
        loser_team = re.sub(r"\(\d+\)","",loser_team).strip()
        
        winner_score = game.select('td[data-stat="winner_points"]')[0].text
        loser_score = game.select('td[data-stat="loser_points"]')[0].text

        home_team  = winner_team if is_home else loser_team
        away_team  = loser_team if is_home else winner_team
        home_score = winner_score if is_home else loser_score
        away_score = loser_score if is_home else winner_score

        notes = game.select('td[data-stat="notes"]')[0].text
        
        if (not home_score and not away_score and "Cancelled" in notes): continue
        
        if (not home_score or not away_score):
            print(game)
            raise

        yield {
            "game_url": game_url,
            "date": date,
            "home_team": home_team,
            "away_team": away_team,
            "home_score": home_score,
            "away_score": away_score,
            "is_neutral": 1 * is_neutral
        }


if __name__ == "__main__":
    # for year in range(1869,2025):
    for year in range(2024,2025):
        print(year)
        with open(f"../data/cfb/cfb_{year}.csv","w") as f_out:
            writer = csv.DictWriter(f_out, fieldnames=["year","game_url","date","home_team","away_team","home_score","away_score","is_neutral"])
            writer.writeheader()
            for game in scrape_games(year):
                writer.writerow({"year":year,**game})

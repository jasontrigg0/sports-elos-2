import requests
from bs4 import BeautifulSoup
import csv
import time
import re

REQUEST_HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:72.0) Gecko/20100101 Firefox/72.0"
}

def scrape_teams(year):
    url = f'https://www.basketball-reference.com/leagues/NBA_{year+1}.html'
    html = requests.get(url, headers = REQUEST_HEADERS).content
    soup = BeautifulSoup(html, features="lxml")
    all_team_urls = [x["href"] for x in soup.select('th[data-stat="team_name"] a')]
    return all_team_urls;

def scrape_games(url):
    time.sleep(2)
    url = f'https://www.basketball-reference.com/{url}'.replace(".html","_games.html"); #2020.html -> 2020_games.html
    html = requests.get(url, headers = REQUEST_HEADERS).content

    soup = BeautifulSoup(html, features="lxml")
    output = []
    for game in soup.select('tbody tr:not(.thead)'):
        #if game.select('td[data-stat="game_date"]')[0].text == "Playoffs": continue
        game_url = game.select('td[data-stat="box_score_text"] a')[0]["href"]
        date = re.findall(r"\d{8}",game_url)[0]
        
        is_home = game.select('td[data-stat="game_location"]')[0].text == ""
        team1 = re.findall("[A-Z]{3}",url)[0]
        team2 = re.findall("[A-Z]{3}",game.select('td[data-stat="opp_name"] a')[0]["href"])[0]
        score1 = game.select('td[data-stat="pts"]')[0].text
        score2 = game.select('td[data-stat="opp_pts"]')[0].text

        home_team  = team1 if is_home else team2
        away_team  = team2 if is_home else team1
        home_score = score1 if is_home else score2
        away_score = score2 if is_home else score1

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

def scrape_year(year):
    all_games = []
    all_team_urls = scrape_teams(year)
    for team_url in all_team_urls:
        games = scrape_games(team_url)
        all_games.extend(games)

    #dedup dictionaries https://stackoverflow.com/a/9427216
    all_games = [dict(t) for t in {tuple(sorted(d.items())) for d in all_games}]
    all_games.sort(key=lambda x: x["date"])
    return all_games

if __name__ == "__main__":
    # for year in range(1949,2025):
    for year in range(2024,2025):
        print(year)
        with open(f"../data/nba/nba_{year}.csv","w") as f_out:
            writer = csv.DictWriter(f_out, fieldnames=["year","game_url","date","home_team","away_team","home_score","away_score"])
            writer.writeheader()
            for game in scrape_year(year):
                writer.writerow({"year":year,**game})

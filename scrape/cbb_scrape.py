import requests
from bs4 import BeautifulSoup, Comment
import csv
import time
import re
from datetime import datetime

REQUEST_HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:72.0) Gecko/20100101 Firefox/72.0"
}

def scrape_teams(year):
    time.sleep(2)
    url = f'https://www.sports-reference.com/cbb/seasons/men/{year+1}-standings.html'
    html = requests.get(url, headers = REQUEST_HEADERS).content
    soup = BeautifulSoup(html, features="lxml")
    comments = soup.find_all(string=lambda text: isinstance(text, Comment))
    for c in comments:
        if "school_name" not in c: continue
        soup = BeautifulSoup(c, features="lxml")
        for school in soup.select('td[data-stat="school_name"] a'):
            yield {
                "school_name": school.text,
                "url": school["href"],
            }
    
def scrape_games(team_info):
    time.sleep(2)
    school_name = team_info["school_name"]
    url = team_info["url"]
    url = f"https://www.sports-reference.com{url}".replace(".html","-schedule.html")
    html = requests.get(url, headers = REQUEST_HEADERS).content

    soup = BeautifulSoup(html, features="lxml")

    for game in soup.select("table#schedule tbody tr:not(.thead)"):
        game_cell = game.select('td[data-stat="date_game"]')[0]
        date = datetime.strptime(game_cell.text, "%a, %b %d, %Y").strftime("%Y%m%d")

        if game_cell.select("a"):
            game_url = game_cell.select('a')[0]["href"]
        else:
            game_url = ""
            
        is_home = game.select('td[data-stat="game_location"]')[0].text == ""
        is_neutral = game.select('td[data-stat="game_location"]')[0].text == "N"

        opp_team = game.select('td[data-stat="opp_name"]')[0].text
        opp_team = re.sub(r"\(\d+\)","",opp_team).strip()
        
        score = game.select('td[data-stat="pts"]')[0].text
        opp_score = game.select('td[data-stat="opp_pts"]')[0].text

        home_team  = school_name if is_home else opp_team
        away_team  = opp_team if is_home else school_name
        home_score = score if is_home else opp_score
        away_score = opp_score if is_home else score

        if (not home_score or not away_score):
            if date < datetime.today().strftime('%Y%m%d'):
                print(url, date)
            continue


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
    # for year in range(1900,2025):
    for year in range(2025, 2026):
        print(year)
        with open(f"../data/cbb/cbb_{year}.csv","w") as f_out:
            writer = csv.DictWriter(f_out, fieldnames=["year","game_url","date","home_team","away_team","home_score","away_score","is_neutral"])
            writer.writeheader()

            all_team_info = scrape_teams(year)
            for team_info in all_team_info:
                #print(team_info)
                for game in scrape_games(team_info):
                    writer.writerow({"year":year,**game})
        

import requests
import re
import csv
from bs4 import BeautifulSoup, Comment

def chunks(lst, n):
    #https://stackoverflow.com/a/312464
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]

def get_players():
    url = "https://www.go4go.net/go/games/byplayer"
    html = requests.get(url).content
    soup = BeautifulSoup(html, features="lxml")

    for table in soup.select("table table"):
        country = table.select("tr")[0].text.strip().rsplit(" ",1)[0].lower()
        for player in table.select("option")[1:]:
            yield {
                "country": country,
                "player": player.text.strip().rsplit(" ",1)[0]
            }
        
def get_year(year):
    offset = 0

    while True:
        url = f'https://www.go4go.net/go/games/bydate/{year}/{offset}'
        html = requests.get(url).content
        soup = BeautifulSoup(html, features="lxml")
        table = soup.select("table")[1]
        rows = table.select("tr")

        if len(rows) <= 2: break
        offset += 30
        
        for pair in chunks(rows[2:],2):
            first, second = pair
            info = first.select("td")[0].text.strip()
            date = re.findall("[0-9\-]+",info)[0]
            event = info.split(" ",1)[1]
            black = second.select("td")[0].text.rsplit(" ",1)[0]
            white = second.select("td")[1].text.rsplit(" ",1)[0]
            winner = second.select("td")[2].text.split("+")[0]
            yield {
                "date": date,
                "event": event,
                "black": black,
                "white": white,
                "winner": winner
            }
    
        
if __name__ == "__main__":
    players = get_players()
    writer = csv.DictWriter(open("../data/go/players.csv","w"), fieldnames=["country","player"])
    writer.writeheader()
    for p in players:
        writer.writerow(p)
    raise
    
    for year in range(2020, 1968, -1): #2021, 2022): #1969,2026):
        print(year)
        with open(f"../data/go/go_{year}.csv","w") as f_out:
            writer = csv.DictWriter(f_out, fieldnames=["year","date","event","black","white","winner"])
            writer.writeheader()
            
            for result in get_year(year):
                writer.writerow(
                    {
                        "year": year,
                        **result
                    }
                )

import pandas as pd
import requests

#repo with data through end of 2023, will need better sources
#https://github.com/schochastics/football-data
r = requests.get("https://raw.githubusercontent.com/schochastics/football-data/refs/heads/master/data/results/games.parquet", allow_redirects=True)
open('/tmp/games.parquet', 'wb').write(r.content)
df = pd.read_parquet('/tmp/games.parquet')
df.to_csv('../data/soccer.csv', index=False)

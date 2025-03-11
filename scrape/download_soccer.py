import pandas as pd
df = pd.read_parquet('/home/jason/Downloads/games.parquet')
df.to_csv('soccer.csv', index=False)

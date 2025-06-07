set -x

#flip in july
python3 cfb_scrape.py
python3 nfl_scrape.py 
python3 cbb_scrape.py
python3 nba_scrape.py
python3 nhl_scrape.py

#flip in jan
python3 mlb_scrape.py
python3 f1_scrape.py
python3 liv_scrape.py
python3 pga_scrape.py
python3 ufc_scrape.py
python3 lol_scrape.py
python3 cs_scrape.py

set +x

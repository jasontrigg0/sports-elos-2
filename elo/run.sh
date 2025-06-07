set -x

python3 mlb_elo.py > /dev/null
python3 nba_elo.py > /dev/null
python3 nfl_elo.py > /dev/null
python3 nhl_elo.py > /dev/null

python3 cbb_elo.py > /dev/null
python3 cfb_elo.py > /dev/null

python3 f1_elo.py > /dev/null
python3 golf_elo.py > /dev/null
python3 ufc_elo.py > /dev/null

python3 cs_elo.py > /dev/null
python3 lol_elo.py > /dev/null

set +x

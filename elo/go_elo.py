import sys
sys.path.append(".")
import elo
import csv
import glob

def load_data():
    players = csv.DictReader(open("../data/go/players.csv"))
    player_to_country = {r["player"]:r["country"] for r in players}
    
    all_files = glob.glob("../data/go/go_*.csv")

    all_rows = []
    for filename in all_files:
        reader = csv.DictReader(open(filename))
        all_rows += [row for row in reader]

    for row in all_rows:
        if row["winner"] == "Void": continue

        #skip AI games for elo purposes
        if player_to_country[row["black"]] == "ai players" or player_to_country[row["white"]] == "ai players": continue
        
        if row["winner"] not in ["W","B"]:
            print(row)
            raise
        
        yield {
            "type": "match",
            "yyyymmdd": row["date"].replace("-",""),
            "event": row["event"],
            "results": [
                {
                    "player_id": row["black"],
                    "player_name": row["black"],
                    "league_id": player_to_country[row["black"]],
                    "league_name": player_to_country[row["black"]],
                    "opp_id": row["white"],
                    "opp_name": row["white"],
                    "is_home": "HOME",
                    "score": 1 * (row["winner"] == "B"),
                    "raw_score": 1 * (row["winner"] == "B")
                },
                {
                    "player_id": row["white"],
                    "player_name": row["white"],
                    "league_id": player_to_country[row["white"]],
                    "league_name": player_to_country[row["white"]],
                    "opp_id": row["black"],
                    "opp_name": row["black"],
                    "is_home": "AWAY",
                    "score": 1 * (row["winner"] == "W"),
                    "raw_score": 1 * (row["winner"] == "W")
                }
            ]
        }
    

if __name__ == "__main__":
    all_match_data = sorted(list(load_data()), key = lambda x: x["yyyymmdd"])
    #all_match_data = [x for x in all_match_data if x["yyyymmdd"] >= "20200101"]
    
    config = {
        "name": "go",
        "basic_elo": True,
        "print_new": False,
        "output_dir": "../",
        "home_adv": -12,
        "elo_components": [
            {
                "name": "player",
                "external_id": "player_id",
                "external_name": "player_name",
                "primary": True,
                "event_subtype": False,
            },
            {
                "name": "league",
                "external_id": "league_id",
                "external_name": "league_name",
                "primary": False,
                "event_subtype": False,
            }
        ],
        "elo_settings": {
            "default": {
                "new_k_mult": 3.8,
                "player": {
                    "k": 20,
                    "update_max": 1000,
                    "year_end_shrinkage_frac": 0
                },
                "league": {
                    "k": 4,
                    "update_max": 1000,
                    "year_end_shrinkage_frac": 0
                }
            }
        },
        "normalize": True,
        "normalize_cnt": 16,
        "record_scores": True
    }

    elo_calc = elo.Elo(all_match_data, config)
    elo_calc.generate_elos()
    elo_calc.print_elos()
    

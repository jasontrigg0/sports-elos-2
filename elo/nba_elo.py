import sys
sys.path.append(".")
import elo
import csv
import glob

def get_id(name):
    name_to_id = {
        "TRI": "ATL",
        "PHW": "GSW",
        "SFW": "GSW",
        "MNL": "LAL",
        "SYR": "PHI",
        "FTW": "DET",
        "MLH": "ATL",
        "STL": "ATL",
        "ROC": "SAC",
        "CIN": "SAC",
        "KCO": "SAC",
        "KCK": "SAC",
        "CHP": "WAS",
        "CHZ": "WAS",
        "BAL": "WAS",
        "CAP": "WAS",
        "WSB": "WAS",
        "SEA": "OKC",
        "SDR": "HOU",
        "BUF": "LAC",
        "SDC": "LAC",
        "NOJ": "UTA",
        "NYN": "NJN",
        "CHH": "CHA",
        "VAN": "MEM",
        "NOK": "NOH",
        "BRK": "NJN",
        "NOP": "NOH",
        "CHO": "CHA"
    }
    return name_to_id.get(name, name)

def load_data():
    all_files = glob.glob("../data/nba/nba_*.csv")
    league = "nba"

    for filename in all_files:
        reader = csv.DictReader(open(filename))
        for row in reader:
            yield {
                "type": "match",
                "yyyymmdd": row["date"],
                "event": league,
                "results": elo.get_simple_match_res({
                    "home_id": get_id(row["home_team"]),
                    "home_name": row["home_team"],
                    "away_id": get_id(row["away_team"]),
                    "away_name": row["away_team"],
                    "home_score": row["home_score"],
                    "away_score": row["away_score"],
                    "league_id": league,
                    "league_name": league,
                    "is_neutral": 0,
                })
            }

        


if __name__ == "__main__":
    all_match_data = sorted(list(load_data()),key=lambda x: x["yyyymmdd"])
    all_events = elo.add_year_ends(all_match_data, lambda x: "0801")

    config = {
        "name": "nba",
        "basic_elo": False,
        "print_new": False,
        "output_dir": "../",
        "home_adv": 85,
        "elo_components": [
            {
                "name": "player",
                "external_name": "player_name",
                "external_id": "player_id",
                "primary": True,
                "event_subtype": False,
            }
        ],
        "elo_settings": {
            "default": {
                "new_k_mult": 20,
                "sigmoid_max": 40,
                "raw_to_elo_mult": 28,
                "player": {
                    "k": 0.035,
                    "update_max": 29,
                    "year_end_shrinkage_frac": 0.30,
                }
            },
        },
        "normalize": True,
        "normalize_cnt": 32,
        "record_scores": True,
        "modern_era_start": "19660101",
    }

    
    elo_calc = elo.Elo(all_events, config)
    elo_calc.generate_elos()
    elo_calc.print_elos()

import sys
sys.path.append(".")
import elo
import csv

def get_id(name):
    name_to_id = {
        "TRA": "TOR",
        "TRS": "TOR",
        "QBC": "HAM",
        "CBH": "CHI",
        "DTC": "DET",
        "DTF": "DET",
        "BRO": "NYA",
        "OAK": "CLE",
        "CGS": "CLE",
        "MNS": "DAL",
        "ATF": "CGY",
        "KCS": "NJD",
        "CLR": "NJD",
        "WIN": "PHX",
        "QUE": "COL",
        "HAR": "CAR",
        "MDA": "ANA",
        "ATL": "WPG",
        "ARI": "PHX"
    }
    return name_to_id.get(name, name)

def load_data():
    reader = csv.DictReader(open("nhl.csv"))

    league = "nhl"

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
    all_match_data = list(load_data())

    get_cutoff = lambda year: "1101" if year == "2020" else "0801"
    all_events = elo.add_year_ends(all_match_data, get_cutoff)

    
    config = {
        "name": "nhl",
        "basic_elo": False,
        "print_new": False,
        "home_adv": 50,
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
                "new_k_mult": 36,
                "sigmoid_max": 1000,
                "raw_to_elo_mult": 105,
                "player": {
                    "k": 0.021,
                    "update_max": 17,
                    "year_end_shrinkage_frac": 0.15,
                }
            }
        },
        "normalize": True,
        "normalize_cnt": 32,
        "record_scores": True,
        "modern_era_start": "19670101",
    }

    elo_calc = elo.Elo(all_events, config)
    elo_calc.generate_elos()
    elo_calc.print_elos()
    

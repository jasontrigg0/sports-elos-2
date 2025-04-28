import sys
sys.path.append(".")
import elo
import csv
import glob

def load_data():
    all_files = glob.glob("../data/nfl/nfl_*.csv")
    league = "nfl"
    for filename in all_files:
        reader = csv.DictReader(open(filename))
        for row in reader:
            yield {
                "type": "match",
                "yyyymmdd": row["date"],
                "event": league,
                "results": elo.get_simple_match_res({
                    "home_id": row["home_team"],
                    "home_name": row["home_team"],
                    "away_id": row["away_team"],
                    "away_name": row["away_team"],
                    "home_score": row["home_score"],
                    "away_score": row["away_score"],
                    "league_id": league,
                    "league_name": league,
                    "is_neutral": 0, #TODO: fix superbowl
                })
            }

if __name__ == "__main__":
    all_match_data = sorted(list(load_data()),key=lambda x: x["yyyymmdd"])
    all_events = elo.add_year_ends(all_match_data, lambda x: "0401")

    config = {
        "name": "nfl",
        "basic_elo": False,
        "print_new": False,
        "output_dir": "../",
        "home_adv": 55,
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
                "new_k_mult": 14,
                "sigmoid_max": 30,
                "raw_to_elo_mult": 27,
                "player": {
                    "k": 0.07,
                    "update_max": 160,
                    "year_end_shrinkage_frac": 0.35,
                }
            }
        },
        "normalize": True,
        "normalize_cnt": 32,
        "record_scores": True,
        "modern_era_start": "19660401",
    }

    
    elo_calc = elo.Elo(all_events, config)
    elo_calc.generate_elos()
    elo_calc.print_elos()

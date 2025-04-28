import sys
sys.path.append(".")
import elo
import csv
import glob

def load_data():
    all_files = glob.glob("../data/cfb/cfb_*.csv")
    
    league = "cfb"
    
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
                    "is_neutral": int(row["is_neutral"])
                })
            }

if __name__ == "__main__":
    all_match_data = sorted(list(load_data()), key=lambda x: x["yyyymmdd"])
    all_events = elo.add_year_ends(all_match_data, lambda x: "0401")
        
    config = {
        "name": "cfb",
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
            "slow": {
                "k": 0.07,
                "raw_to_elo_mult": 22,
            },
            "default": {
                "new_k_mult": 8,
                "sigmoid_max": 40,
                "raw_to_elo_mult": 20,
                "player": {
                    "k": 0.165,
                    "update_max": 180,
                    "year_end_shrinkage_frac": 0.6,
                }
            }
        },
        "normalize": True,
        "normalize_cnt": 25,
        "record_scores": True,
        "modern_era_start": "19500101",
        "has_slow": True,
    }

    #all_events = [x for x in all_events if x["yyyymmdd"] < "20191001"]
    elo_calc = elo.Elo(all_events, config)
    elo_calc.generate_elos()
    elo_calc.print_elos()

import sys
sys.path.append(".")
import elo
import csv
import glob

def load_data():
    all_files = glob.glob("cbb/cbb_*.csv")

    league = "cbb"
    
    for filename in all_files:
        reader = csv.DictReader(open(filename))
        visited_games = set() #deduping matches seen from both sides
        for row in reader:
            key = "|".join(sorted([row["date"],row["home_team"],row["away_team"],row["home_score"],row["away_score"]]))
            if key in visited_games: continue
            visited_games.add(key)

            if row["date"] > "20241231" and not row["home_score"]:
                #print(row)
                continue
            
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
    all_match_data = sorted(list(load_data()), key = lambda x: x["yyyymmdd"])
    all_events = elo.add_year_ends(all_match_data, lambda x: "0601")

    config = {
        "name": "cbb",
        "basic_elo": False,
        "print_new": False,
        "home_adv": 105,
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
                "k": 0.065,
                "raw_to_elo_mult": 25,
            },
            "default": {
                "new_k_mult": 4,
                "sigmoid_max": 60,
                "raw_to_elo_mult": 26,
                "player": {
                    "k": 0.090,
                    "update_max": 1000,
                    "year_end_shrinkage_frac": 1.0,
                }
            }
        },
        "normalize": False,
        "normalize_cnt": 64, #march madness count
        "record_scores": True,
        "has_slow": True,
    }

    elo_calc = elo.Elo(all_events, config)
    elo_calc.generate_elos()
    elo_calc.print_elos()

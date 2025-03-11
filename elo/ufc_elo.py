import sys
sys.path.append(".")
import elo
import csv
import re


def load_data(complex_score = False):
    # reader = csv.DictReader(open("ufc.csv"))
    reader = csv.DictReader(open("ufc.csv"))

    all_match_data = []

    all_rows = sorted([row for row in reader], key = lambda x: x["event_date"])

    league = "ufc"

    fighter_to_division = {}
    
    for row in all_rows:
        fighter_to_division[row["fighter1"]] = row["division"]
        fighter_to_division[row["fighter2"]] = row["division"]

        wdl_score = float(row["result"])
        
        if not complex_score:
            score1 = wdl_score
            score2 = 1 - wdl_score
        else:
            score = {
                "SUB": 1.7,
                "KO/TKO": 2.0,
                "U-DEC": 1.7,
                "S-DEC": 0.01,
                "DQ": 0.01,
                "Other": 0.01,
                "M-DEC": 0,
            }[row["method"]]
            
            score1 = score
            score2 = 0
        
        yield {
            "type": "match",
            "yyyymmdd": row["event_date"],
            "event": row["event"],
            "results": [
                {
                    "player_id": row["fighter1"], #todo change to id
                    "player_name": row["fighter1"],
                    "league_id": fighter_to_division[row["fighter1"]],
                    "league_name": fighter_to_division[row["fighter1"]],
                    "opp_id": row["fighter2"],
                    "opp_name": row["fighter2"],
                    "is_home": "NEUTRAL",
                    "score": wdl_score,
                    "raw_score": score1,
                    "score_type": "default",
                },
                {
                    "player_id": row["fighter2"],
                    "player_name": row["fighter2"],
                    "league_id": fighter_to_division[row["fighter2"]],
                    "league_name": fighter_to_division[row["fighter2"]],
                    "opp_id": row["fighter1"],
                    "opp_name": row["fighter1"],
                    "is_home": "NEUTRAL",
                    "score": 1 - wdl_score,
                    "raw_score": score2,
                    "score_type": "default",
                }
            ]
        }


if __name__ == "__main__":
    basic_config = {
        "name": "ufc",
        "basic_elo": True,
        "print_new": False,
        "home_adv": 0,
        "elo_components": [
            {
                "name": "player",
                "external_name": "player_id",
                "external_id": "player_id",
                "primary": True,
                "event_subtype": False,
            },
        ],
        "elo_settings": {
            "default": {
                "new_k_mult": 0.4,
                "player": {
                    "k": 65,
                    "update_max": 500,
                    "year_end_shrinkage_frac": 0,
                }
            }
        },
        "normalize": False,
        "normalize_cnt": 10,
        "record_scores": False,
    }

    score_config = {
        "name": "ufc",
        "basic_elo": False,
        "print_new": False,
        "home_adv": 0,
        "elo_components": [
            {
                "name": "player",
                "external_name": "player_id",
                "external_id": "player_id",
                "primary": True,
                "event_subtype": False,
            },
            {
                "name": "league",
                "external_name": "league_id",
                "external_id": "league_id",
                "primary": False,
                "event_subtype": False,
            }
        ],
        "elo_settings": {
            "default": {
                "new_k_mult": 1.3,
                "sigmoid_max": 1000,
                "raw_to_elo_mult": 95,
                "player": {
                    "k": 0.19,
                    "update_max": 1000,
                    "year_end_shrinkage_frac": 0,
                },
                "league": {
                    "k": 0,
                    "update_max": 1,
                    "year_end_shrinkage_frac": 0,
                }
            },
        },
        "normalize": True,
        "normalize_cnt": 25,
        "alltime_window": 1e6, #alltime
        "inactive_window": 365,
        "record_scores": True,
        "modern_era_start": "20100101",
    }
    
    complex_score = True
    all_match_data = list(load_data(complex_score))
    all_events = elo.add_year_ends(all_match_data, lambda x: "1231")

    config = score_config if complex_score else basic_config
    elo_calc = elo.Elo(all_events, config)
    elo_calc.generate_elos()
    elo_calc.print_elos()
    

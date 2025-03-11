import sys
sys.path.append(".")
import elo
import csv

def load_data():
    reader = csv.DictReader(open("soccer.csv"))

    team_to_league = {}
    
    for row in reader:
        if row["level"] == "national":
            team_to_league[row["home_ident"]] = row["competition"]
            team_to_league[row["away_ident"]] = row["competition"]

        home_league = team_to_league.get(row["home_ident"],"unknown")
        away_league = team_to_league.get(row["away_ident"],"unknown")
        
        yield {
            "type": "match",
            "yyyymmdd": row["date"].replace("-",""),
            "event": row["competition"],
            "results": elo.get_simple_match_res({
                "home_id": row["home_ident"],
                "home_name": row["home_ident"],
                "away_id": row["away_ident"],
                "away_name": row["away_ident"],
                "home_score": row["gh"],
                "away_score": row["ga"],
                "home_league_id": home_league,
                "home_league_name": home_league,
                "away_league_id": away_league,
                "away_league_name": away_league,
                "is_neutral": 0,
            })
        }
    
if __name__ == "__main__":
    all_match_data = list(load_data())

    get_cutoff = lambda year: "0701"
    all_events = elo.add_year_ends(all_match_data, get_cutoff)

    
    config = {
        "name": "soccer",
        "basic_elo": False,
        "print_new": False,
        "home_adv": 46.5, #TODO: update to elo
        "elo_components": [
            {
                "name": "player",
                "external_name": "player_name",
                "external_id": "player_id",
                "primary": True,
                "event_subtype": False,
            },
            {
                "name": "league",
                "external_name": "league_name",
                "external_id": "league_id",
                "primary": False,
                "event_subtype": False,
            }
        ],
        "elo_settings": {
            "default": {
                "new_k_mult": 9,
                "sigmoid_max": 17,
                "raw_to_elo_mult": 155,
                "player": {
                    "k": 0.035,
                    "update_max": 0.40,
                    "year_end_shrinkage_frac": 0.10,
                },
                "league": {
                    "k": 0.033,
                    "update_max": 0.45,
                    "year_end_shrinkage_frac": 0.10,
                }
            },
        },
        "normalize": True,
        "normalize_cnt": 32, #number of champions league teams that make groups
        "record_scores": True,
        "modern_era_start": "19500101",
    }

    elo_calc = elo.Elo(all_events, config)
    elo_calc.generate_elos()
    elo_calc.print_elos()
    

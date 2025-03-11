import sys
sys.path.append(".")
import elo
import csv

def load_liv_data():
    liv_owgr_id_map = {}
    for row in csv.DictReader(open("liv_owgr_map.csv")):
        liv_owgr_id_map[row["liv_id"]] = row["owgr_id"]
    
    reader = csv.DictReader(open("liv.csv"))

    matches = {}

    for row in reader:
        if not row["player_id"] in liv_owgr_id_map:
            raise Exception("Unknown LIV player, please add to liv_owgr_map.csv")
        row["player_id"] = liv_owgr_id_map[row["player_id"]]
        key = row["event_id"] + f" (round {row['round']})"
        matches.setdefault(key,{
            "type": "match",
            "yyyymmdd": row["start_date"],
            "event": key,
        })
        matches[key].setdefault("results",[]).append({
            "player_id": row["player_id"],
            "player_name": row["player_name"],
            "league_id": "liv",
            "league_name": "liv",
            "opp_id": "",
            "opp_name": "",
            "is_home": "NEUTRAL",
            "raw_score": int(row["score"]),
            "score_type": "default"
        })

    return list(matches.values())
        
def load_owgr_data():
    reader = csv.DictReader(open("pga.csv"))

    matches = {}

    for row in reader:
        #all players withdrew except one? skipping
        #https://www.owgr.com/events/5060
        if row['event_id'] == '5060':
            continue 
        key = row["event_id"] + f" (round {row['round']})"
        matches.setdefault(key,{
            "type": "match",
            "yyyymmdd": row["start_date"],
            "event": key,
        })
        matches[key].setdefault("results",[]).append({
            "player_id": row["player_id"],
            "player_name": row["player_name"],
            "league_id": "pga",
            "league_name": "pga",
            "opp_id": "",
            "opp_name": "",
            "is_home": "NEUTRAL",
            "raw_score": int(row["score"]),
            "score_type": "default"
        })

    return list(matches.values())

if __name__ == "__main__":
    all_match_data = sorted([*load_liv_data(), *load_owgr_data()], key = lambda x: x["yyyymmdd"])
    # all_match_data = [x for x in all_match_data if x["yyyymmdd"] < "20060827"]
    all_events = elo.add_year_ends(all_match_data, lambda x: "1231")

    config = {
        "name": "golf",
        "basic_elo": False,
        "print_new": False,
        "modern_era_start": "20070101",
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
                "new_k_mult": 24,
                "sigmoid_max": 10,
                "sigmoid_max_neg": 6,
                "raw_to_elo_mult": 1,
                "player": {
                    "k": 0.045,
                    "update_max": 3,
                    "year_end_shrinkage_frac": 0.00,
                }
            },
        },
        "sign": -1,
        "normalize": True,
        "normalize_cnt": 125, #number of tour pros
        "record_scores": True,
        "has_binary_result": False,
    }
    
    elo_calc = elo.Elo(all_events, config)
    elo_calc.generate_elos()
    elo_calc.print_elos()

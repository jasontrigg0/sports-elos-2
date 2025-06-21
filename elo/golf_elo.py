import sys
sys.path.append(".")
import elo
import csv
import glob
import datetime

def load_pga_data():
    matches = {}

    history_file = "../data/pga/history.csv"
    
    all_files = [history_file] + glob.glob("../data/pga/pga_*.csv")

    tournaments_from_history_file = set()
    
    for f in all_files:
        reader = csv.DictReader(open(f))

        for row in reader:
            #some tournaments may be covered in both history.csv and pga_{year}.csv
            #in which case use history.csv which seems more reliable, see scraper for details
            if f == history_file:
                tournaments_from_history_file.add(row["tournament_id"])
            elif row["tournament_id"] in tournaments_from_history_file:
                continue
        
            #only PGA events for now
            #Senior Tour isn't properly normalizing
            if row["tournament_id"][0] != "R": continue
        
            key = row["tournament_id"] + f" (round {row['round']})"
            matches.setdefault(key,{
                "type": "match",
                "yyyymmdd": datetime.datetime.strptime(row["date"],"%m.%d.%Y").strftime("%Y%m%d"),
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

    singletons = [key for key in matches if len(matches[key]["results"]) == 1]
    for x in singletons:
        del matches[x]
            
    return list(matches.values())

def load_liv_data(fieldname):
    liv_owgr_id_map = {}
    for row in csv.DictReader(open("../scrape/liv_owgr_map.csv")):
        liv_owgr_id_map[row["liv_id"]] = row[fieldname]

    matches = {}

    for f in glob.glob("../data/liv/*"):
        reader = csv.DictReader(open(f))

        for row in reader:
            if not row["player_id"] in liv_owgr_id_map:
                print(row["player_id"])
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
    matches = {}

    for f in glob.glob("../data/owgr/*"):
        reader = csv.DictReader(open(f))

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

def load_liv_owgr():
    return sorted([*load_liv_data("owgr_id"), *load_owgr_data()], key = lambda x: x["yyyymmdd"])

def load_liv_pga():
    return sorted([*load_liv_data("pga_id"), *load_pga_data()], key = lambda x: x["yyyymmdd"])

if __name__ == "__main__":
    all_match_data = load_liv_pga()
    #all_match_data = [x for x in all_match_data if x["yyyymmdd"] < "20230401"]
    all_events = elo.add_year_ends(all_match_data, lambda x: "1231")

    config = {
        "name": "golf",
        "basic_elo": False,
        "print_new": False,
        "output_dir": "../",
        "modern_era_start": "19600101", #"20070101",
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
                "new_k_mult": 28,
                "sigmoid_max": 6,
                "sigmoid_max_neg": 6,
                "raw_to_elo_mult": 1,
                "player": {
                    "k": 0.018,
                    "update_max": 3,
                    "year_end_shrinkage_frac": 0.00,
                }
            },
        },
        "sign": -1,
        "normalize": True,
        "normalize_cnt": 125, #number of tour pros
        "alltime_window": 10000,
        "record_scores": True,
        "has_binary_result": False,
    }
    
    elo_calc = elo.Elo(all_events, config)
    elo_calc.generate_elos()
    elo_calc.print_elos()

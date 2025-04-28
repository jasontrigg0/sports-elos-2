import sys
sys.path.append(".")
import elo
import csv

def load_data():
    reader = csv.DictReader(open("f1db_csv/results.csv"))
    
    #first group by race
    results = [row for row in reader]

    
    reader = csv.DictReader(open("f1db_csv/races.csv"))
    race_details = {row["raceId"]:row for row in reader}
    
    reader = csv.DictReader(open("f1db_csv/drivers.csv"))
    driver_details = {row["driverId"]:row for row in reader}

    reader = csv.DictReader(open("f1db_csv/constructors.csv"))
    constructor_details = {row["constructorId"]:row for row in reader}
    
    all_race_results = {}
    for row in results:
        all_race_results.setdefault(row["raceId"],[]).append(row)

    #add one match for each pair of drivers in each race
    for race in all_race_results:

        all_race_matches = []
        
        rows = [x for x in all_race_results[race] if x["position"] != "\\N"]
        for i in range(len(rows)):
            r1 = rows[i]
            for j in range(i+1,len(rows)):
                r2 = rows[j]
                r1_score = None
                if r1["position"] == r2["position"]:
                    r1_score = 0.5
                elif int(r1["position"]) < int(r2["position"]):
                    r1_score = 1
                else:
                    r1_score = 0

                #if float(r1["position"]) > float(r2["position"])
                key = (r1["raceId"],r1["driverId"],r2["driverId"])

                league = "f1"

                def get_driver_name(id_):
                    return " ".join([driver_details[id_]["forename"], driver_details[id_]["surname"]])
                
                match_results = [
                    {
                        "player_id": r1["driverId"],
                        "player_name": get_driver_name(r1["driverId"]),
                        "constructor_id": r1["constructorId"],
                        "constructor_name": constructor_details[r1["constructorId"]]["name"],
                        "league_id": league,
                        "league_name": league,
                        "opp_id": r2["driverId"],
                        "opp_name": get_driver_name(r2["driverId"]),
                        "is_home": "NEUTRAL",
                        "score": r1_score,
                        "raw_score": r1_score
                    },
                    {
                        "player_id": r2["driverId"],
                        "player_name": get_driver_name(r2["driverId"]),
                        "constructor_id": r2["constructorId"],
                        "constructor_name": constructor_details[r2["constructorId"]]["name"],
                        "league_id": league,
                        "league_name": league,
                        "opp_id": r1["driverId"],
                        "opp_name": get_driver_name(r1["driverId"]),
                        "is_home": "NEUTRAL",
                        "score": 1-r1_score,
                        "raw_score": 1-r1_score
                    }
                ]
                all_race_matches.append(match_results)
        yield {
            "type": "match_group",
            "yyyymmdd": race_details[r1["raceId"]]["date"].replace("-",""),
            "event": race_details[r1["raceId"]]["name"],
            "matches": all_race_matches,
        }
                

if __name__ == "__main__":
    all_match_data = list(load_data())
    all_match_data.sort(key=lambda x: x["yyyymmdd"])
    all_match_data = elo.add_year_ends(all_match_data, lambda x: "1231")

    config = {
        "name": "f1",
        "basic_elo": True,
        "print_new": False,
        "home_adv": 0,
        "elo_components": [
            {
                "name": "player",
                "external_id": "player_id",
                "external_name": "player_name",
                "event_subtype": False,
                "primary": True,
            },
            {
                "name": "constructor",
                "external_id": "constructor_id",
                "external_name": "constructor_name",
                "event_subtype": False,
                "primary": False,
            }
        ],
        "elo_settings": {
            "default": {
                "new_k_mult": 1,
                "player": {
                    "k": 7.5,
                    "update_max": 50,
                    "year_end_shrinkage_frac": 0.05,
                },
                "constructor": {
                    "k": 6,
                    "update_max": 50,
                    "year_end_shrinkage_frac": 0.05,
                }
            }
        },
        "normalize": True,
        "normalize_cnt": 20,
        "alltime_window": 10000, #240
        "record_scores": True,
        "score_metric": lambda info: info["comp"]["player"],
    }

    elo_calc = elo.Elo(all_match_data, config)
    elo_calc.generate_elos()
    elo_calc.print_elos()

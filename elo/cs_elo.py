import glob
import csv
import sys
sys.path.append(".")
import elo

def load_data():
    all_files = glob.glob("/files/git/esports-elos/csgo/csgo_match_info.csv")
    
    all_rows = []

    for filename in all_files:
        reader = csv.DictReader(open(filename))
        all_rows += [row for row in reader]

    team_to_league = {}

    def is_female_event(url):
        if "esl-impact-league" in url.lower(): return True
        if "female" in url.lower(): return True
        if "feminina" in url.lower(): return True
        return False
        
    for row in all_rows:
        team_to_league.setdefault(row["team0"],"open")
        team_to_league.setdefault(row["team1"],"open")
        if is_female_event(row["event"]):
            team_to_league[row["team0"]] = "female"
            team_to_league[row["team1"]] = "female"

            
        
        for i in range(5):
            map_name = row[f"map{i}"]

            if row[f"map{i}_score0"].replace("-","") == "" or row[f"map{i}_score1"].replace("-","") == "":
                continue
            
            map_score0 = int(row[f"map{i}_score0"])
            map_score1 = int(row[f"map{i}_score1"])

            if (map_score0 > map_score1):
                score = 1
            elif (map_score0 == map_score1):
                score = 0.5
            else: 
                score = 0
                
            total_rounds = map_score0 + map_score1
            if total_rounds == 0:
                rounds_frac = 0.5
                raise
            else:
                rounds_frac = map_score0 / total_rounds

            yield {
                "type": "match",
                "yyyymmdd": row["yyyymmdd"],
                "event": row["event"],
                "results": [
                    {
                        "player_id": row["team0"],
                        "player_name": row["team0"].split("/")[-1],
                        "league_id": team_to_league[row["team0"]],
                        "league_name": team_to_league[row["team0"]],
                        "opp_id": row["team1"],
                        "opp_name": row["team1"].split("/")[-1],
                        "is_home": "NEUTRAL",
                        "map": map_name,
                        "score": score,
                        "raw_score": rounds_frac,
                        "weight": total_rounds,
                        "score_type": "default",
                    },
                    {
                        "player_id": row["team1"],
                        "player_name": row["team1"].split("/")[-1],
                        "league_id": team_to_league[row["team1"]],
                        "league_name": team_to_league[row["team1"]],
                        "opp_id": row["team0"],
                        "opp_name": row["team0"].split("/")[-1],
                        "is_home": "NEUTRAL",
                        "map": map_name,
                        "score": 1 - score,
                        "raw_score": 1 - rounds_frac,
                        "weight": total_rounds,
                        "score_type": "default",
                    }
                ]
            }
            

if __name__ == "__main__":
    all_match_data = sorted(list(load_data()),key=lambda x: x["yyyymmdd"])
    all_events = elo.add_year_ends(all_match_data, lambda x: "1231")
    # all_events = [x for x in all_events if x["yyyymmdd"] <= "20190510"]

    config = {
        "name": "cs",
        "basic_elo": False,
        "print_new": False,
        "output_dir": "../",
        "home_adv": 0,
        "elo_components": [
            {
                "name": "team",
                "external_id": "player_id",
                "external_name": "player_name",
                "event_subtype": False,
                "primary": True
            },
            {
                "name": "league",
                "external_id": "league_id",
                "external_name": "league_name",
                "event_subtype": False,
                "primary": False
            },
            {
                "name": "map",
                "external_id": "map",
                "external_name": "map",
                "event_subtype": True,
                "primary": False
            },
        ],
        "elo_settings": {
            "default": {
                "new_k_mult": 4,
                "sigmoid_max": 0.75,
                "raw_to_elo_mult": 1100,
                "team": {
                    "k": 0.0020,
                    "update_max": 10000,
                    "year_end_shrinkage_frac": 0.0,
                },
                "league": {
                    "k": 0.0020,
                    "update_max": 10000,
                    "year_end_shrinkage_frac": 0.0,
                },
                "map": {
                    "k": 0.00030,
                    "update_max": 10000,
                    "year_end_shrinkage_frac": 0.0,
                }
            }
        },
        "normalize": True,
        "normalize_cnt": 32, #number of teams at the major
        "record_scores": True,
    }

    elo_calc = elo.Elo(all_events, config)
    elo_calc.generate_elos()
    elo_calc.print_elos()

import sys
sys.path.append(".")
import elo
import csv
import glob
import re

def result_to_games(result):
    result = result.replace("RET","").replace("ABD","").replace("NA","").replace("DEF","").replace("?-?","")
    result = re.sub("\d-\d\?","",result)
    result = result.replace("Played and unfinished","").replace("Played and abandoned","")
    result = result.replace("Default","").replace("Def.","")
    result = re.sub("\[\d+-\d+\]","",result) #tiebreak game
    if result.strip() in ["W/O","UNK","","Walkover"]:
        return {
            "winner_games": 0,
            "loser_games": 0,
        }
    sets = result.split()
    winner_games = 0
    loser_games = 0
    for s in sets:
        s = re.sub("\(\d+\)","",s)
        winner_games += int(s.split("-")[0])
        loser_games += int(s.split("-")[1])
    return {
        "winner_games": winner_games,
        "loser_games": loser_games,
    }

def result_to_points(row):
    if row["w_svpt"] and row["w_1stWon"] and row["w_2ndWon"] and row["l_svpt"] and row["l_1stWon"] and row["l_2ndWon"]:
        return {
            "winner_points": int(row["w_1stWon"]) + int(row["w_2ndWon"]) + (int(row["l_svpt"]) - int(row["l_1stWon"]) - int(row["l_2ndWon"])),
            "loser_points":  int(row["l_1stWon"]) + int(row["l_2ndWon"]) + (int(row["w_svpt"]) - int(row["w_1stWon"]) - int(row["w_2ndWon"])),
        }
    else:
        return None

def gen_results(info):
    return [
        {
            "player_id": info["winner_name"],
            "player_name": info["winner_name"],
            "league_id": info["league"],
            "league_name": info["league"],
            "opp_id": info["loser_name"],
            "opp_name": info["loser_name"],
            "is_home": "NEUTRAL",
            "event_type": info["surface"],
            "score": 1,
            "raw_score": info["winner_raw_score"],
            "score_type": info["score_type"],
            "weight": info["weight"],
        },
        {
            "player_id": info["loser_name"],
            "player_name": info["loser_name"],
            "league_id": info["league"],
            "league_name": info["league"],
            "opp_id": info["winner_name"],
            "opp_name": info["winner_name"],
            "is_home": "NEUTRAL",
            "event_type": info["surface"],
            "score": 0,
            "raw_score": info["loser_raw_score"],
            "score_type": info["score_type"],
            "weight": info["weight"],
        },
    ]
    
def load_data():
    all_match_data = []
    
    for filename in sorted(glob.glob("../tennis_atp/atp_matches_????.csv")):
        reader = csv.DictReader(open(filename))
        all_match_data += sorted([row for row in reader], key = lambda x: (x["tourney_date"],x["match_num"]))

    for row in all_match_data:
        games = result_to_games(row["score"])
        total_games = (games["winner_games"] + games["loser_games"])
        if total_games == 0:
            games_frac = 0.5
        else:
            games_frac = (games["winner_games"] / total_games)

        score = {
            "winner_raw_score": games_frac,
            "loser_raw_score": 1-games_frac,
            "score_type": "games_frac",
            "weight": total_games / 10
        }
            
        #if we have points data use that instead
        points = result_to_points(row)
        if points: 
            total_points = (points["winner_points"] + points["loser_points"])
            if total_points == 0:
                points_frac = 0.5
            else:
                points_frac = (points["winner_points"] / total_points)

            score = {
                "winner_raw_score": points_frac,
                "loser_raw_score": 1-points_frac,
                "score_type": "points_frac",
                "weight": total_points / 60
            }

        yield {
            "type": "match",
            "yyyymmdd": row["tourney_date"],
            "event": row["tourney_name"],
            "results": gen_results({
                "winner_name": row["winner_name"],
                "loser_name": row["loser_name"],
                "surface": row["surface"],
                "league": "atp",
                **score
            })
        }

if __name__ == "__main__":
    all_match_data = list(load_data())
    
    basic_config = {
        "basic_elo": True,
        "print_new": False,
        "home_adv": 0,
        "new_k_mult": 1.5,
        "year_end_shrinkage_frac": None,
        "sigmoid_max": None,
        "raw_to_elo_mult": None,
        "elo_components": [
            {
                "name": "player",
                "external": "player_id",
                "k": 30,
                "update_max": 500,
                "baseline_elo": 1000,
                "starting_elo": 1000,
                "primary_modifier": False,
                "primary": True
            },
            # {
            #     "name": "event_type",
            #     "external": "event_type",
            #     "k": 15,
            #     "update_max": 1000,
            #     "baseline_elo": 0,
            #     "starting_elo": 0,
            #     "primary_specific": True,
            #     "primary": False
            # }
        ],
        "normalize": False,
        "normalize_cnt": 128
    }


    #unweighted
    games_config = {
        "basic_elo": False,
        "print_new": False,
        "home_adv": 0,
        "new_k_mult": 16,
        "year_end_shrinkage_frac": None,
        "sigmoid_max": 0.65,
        "raw_to_elo_mult": 2200,
        "elo_components": [
            {
                "name": "player",
                "external": "player_id",
                "k": 0.055,
                "update_max": 0.022,
                "baseline_elo": 0,
                "starting_elo": 0,
                "primary_modifier": False,
                "primary": True,
            },
            # {
            #     "name": "event_type",
            #     "external": "event_type",
            #     "k": 15,
            #     "update_max": 1000,
            #     "baseline_elo": 0,
            #     "starting_elo": 0,
            #     "primary_specific": True,
            #     "primary": False
            # }
        ],
        "normalize": False,
        "normalize_cnt": 128,
    }



    #TODO: try dominance ratio
    games_config = {
        "basic_elo": False,
        "print_new": False,
        "home_adv": 0,
        "new_k_mult": 20,
        "year_end_shrinkage_frac": None,
        "sigmoid_max": 1000,
        "raw_to_elo_mult": 2600,
        "elo_components": [
            {
                "name": "player",
                "external": "player_id",
                "k": 0.013,
                "update_max": 91,
                "baseline_elo": 0,
                "starting_elo": 0,
                "primary_modifier": False,
                "primary": True
            },
            {
                "name": "event_type",
                "external": "event_type",
                "k": 0.0044,
                "update_max": 20.8,
                "baseline_elo": 0,
                "starting_elo": 0,
                "primary_modifier": True,
                "primary": False
            }
        ],
        "normalize": False,
        "normalize_cnt": 128,
        "alltime_window": 365
    }

    
    points_config = {
        "name": "atp",
        "basic_elo": False,
        "print_new": False,
        "home_adv": 0,
        "elo_components": [
            {
                "name": "player",
                "external_id": "player_id",
                "external_name": "player_id",
                "event_subtype": False,
                "primary": True
            },
            {
                "name": "event_type",
                "external_id": "event_type",
                "external_name": "event_type",
                "event_subtype": True,
                "primary": False
            }
        ],
        "elo_settings": {
            "default": {
                "player": {
                    "year_end_shrinkage_frac": 0.0,
                },
                "event_type": {
                    "year_end_shrinkage_frac": 0.0,
                }
            },
            "games_frac": {
                "new_k_mult": 20,
                "sigmoid_max": 1000,
                "raw_to_elo_mult": 2600,
                "player": {
                    "k": 0.013,
                    "update_max": 91,
                },
                "event_type": {
                    "k": 0.0044,
                    "update_max": 20.8,
                }
            },
            "points_frac": {
                "new_k_mult": 11,
                "sigmoid_max": 1000,
                "raw_to_elo_mult": 5500,
                "player": {
                    "k": 0.014,
                    "update_max": 180,
                },
                "event_type": {
                    "k": 0.0060,
                    "update_max": 35,
                }
            }
        },
        "normalize": False,
        "normalize_cnt": 128,
        "alltime_window": 10000, #240
        "record_scores": True,
        "year_round": False,
    }
    
    #all_match_data = [x for x in all_match_data if x["yyyymmdd"] < "20000101"]
    all_events = elo.add_year_ends(all_match_data, lambda x: "1231")
    
    config = points_config
    elo_calc = elo.Elo(all_events, config)
    elo_calc.generate_elos()
    elo_calc.print_elos()

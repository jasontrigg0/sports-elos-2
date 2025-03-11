import sys
sys.path.append(".")
import elo
import csv

def get_id(name, date):
    name_to_id = {
        "CAL": "ANA",
        "LAA": "ANA",
        "MLN": "ATL",
        "BSN": "ATL",
        "BRO": "LAD",
        "KCA": "OAK",
        "PHA": "OAK",
        "SLB": "BAL",
        "MLA": "BAL",
        "MON": "WSN",
        "NYG": "SFG",
        "SEP": "MIL",
        "WSH": "MIN",
        "WSA": "TEX",
        "TBR": "TBD",
        "MIA": "FLA",
        "SEP": "MIL",
    }

    #sometimes baseball reference boxscore names mismatch
    #standardized team names. using the latter, found at eg
    #https://www.baseball-reference.com/teams/LGR/
    if date < "18800101" and name == "LOU":
        return "LGR"
    elif date < "18800101" and name == "CIN":
        return "CNR"
    elif date < "18800101" and name == "STL":
        return "SBS"
    elif date < "18800101" and name == "IND":
        return "IBL"
    elif date < "18810101" and name == "CIN":
        return "CNS"
    elif "18790101" < date < "18830101" and name == "TRO":
        return "TRT"
    elif date < "18850101" and name == "IND":
        return "IHO"
    elif date < "18850101" and name == "COL":
        return "CBK"
    elif date < "18850101" and name == "WHS":
        return "WNA"
    elif date < "18850101" and name == "BOS":
        return "BRD"
    elif date < "18850101" and name == "WAS":
        return "WST"
    elif date < "18850101" and name == "CLV":
        return "CBL"
    elif date < "18850101" and name == "KCC":
        return "KCU"
    elif date < "18850101" and name == "MIL":
        return "MLU"
    elif date < "18900101" and name == "WHS":
        return "WNL"
    elif date < "18900101" and name == "IND":
        return "IND"
    elif date < "18910101" and name == "PHA":
        return "PHA"
    elif date < "18910101" and name == "CHI":
        return "CHP"
    elif date < "18920101" and name == "COL":
        return "CLS"
    elif date < "18920101" and name == "BOS":
        return "BRS"
    elif date < "18920101" and name == "PHA":
        return "PHQ"
    elif date < "18920101" and name == "MIL":
        return "MLA"
    elif date < "19000101" and name == "CLE":
        return "CLV"
    elif date < "19000101" and name == "WHS":
        return "WAS"
    elif date < "19000101" and name in ["BAL","BLN"]:
        return "BLO"
    elif date < "19150101" and name == "IND":
        return "NEW"

    return name_to_id.get(name, name)

def load_data():
    reader = csv.DictReader(open("mlb.csv"))

    league = "mlb"

    for row in reader:
        yield {
            "type": "match",
            "yyyymmdd": row["date"],
            "event": league,
            "results": elo.get_simple_match_res({
                "home_id": get_id(row["home_team"], row["date"]),
                "home_name": row["home_team"],
                "away_id": get_id(row["away_team"], row["date"]),
                "away_name": row["away_team"],
                "home_score": row["home_score"],
                "away_score": row["away_score"],
                "league_id": league,
                "league_name": league,
                "is_neutral": 0,
            })
        }
    
if __name__ == "__main__":
    all_match_data = list(load_data())

    get_cutoff = lambda year: "1201"
    all_events = elo.add_year_ends(all_match_data, get_cutoff)

    
    config = {
        "name": "mlb",
        "basic_elo": False,
        "print_new": False,
        "home_adv": 30,
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
                "new_k_mult": 75,
                "sigmoid_max": 11,
                "raw_to_elo_mult": 80,
                "player": {
                    "k": 0.0090,
                    "update_max": 30,
                    "year_end_shrinkage_frac": 0.25,
                },
            }
        },
        "normalize": True,
        "normalize_cnt": 32,
        "record_scores": True,
        "modern_era_start": "19470101",
    }

    elo_calc = elo.Elo(all_events, config)
    elo_calc.generate_elos()
    elo_calc.print_elos()
    

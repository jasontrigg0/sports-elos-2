import sys
sys.path.append(".")
import elo
import csv
import re
import glob

RECOGNIZED_LEAGUES = [
    "LDL",
    "LPL",
    "LCK",
    "TCL",
    "VCS",
    "LCS",
    "LEC",
    "CBLOL",
    "LJL",
    "LCK CL", #parent: LCK
    "LMS",
    "PCS",
    "NACL",
    "EUCS",
    "LLA",
    "GPL",
    "LCP",
    "LCL",
    "LFL",
    "LIT",
    "Arabian League",
    "PRM 1st Division",
    "PRM 2nd Division",
    "PCL",
    "NLC",
    "LFL Division 2",
    "LVP SL", #top spanish league
    "LJL Academy",
    "DDH", #mexican league
    "GL", #colombian league
    "Rift Legends", #eastern european, formerly Ultraliga
    "LRN", #latin north parent: LLA
    "LRS", #latin south parent: LLA
    "ESLM", #german + austrian
    "EL", #caribbean, parent: LRN
    "LPLOL", #portugal
    "CBLOL Academy", #parent: CBLOL
    "UKLC", #UK league, parent: NLC
    "EBL", #balkan league
    "Hitpoint Masters", #czech + slovakia league
    "HLL", #greek
    "HCC", #greek second league parent GLL
    "LVP SL 2nd Division", #parent: LVP SL
    "LMF", #argentina, parent ??
    "NLC 2nd Division", #parent NLC
    "VL", #volcano league: ecuador
    "LLN", #old latin america north, combine to LLA
    "CLS", #old latin america south, combine to LLA
    "LH", #chile
    "LTL", #costa rica
    "SL", #peru
    "TCL Division 2", #parent TCL
    "Belgian League",
    "ECS", #parent: LMS
    "LCO", #australia
    "Arabian League 2nd Division", #parent: Arabian League
    "ACL", #parent: NACL
    "Dutch League",
    "Road Of Legends", #combined from Dutch and Belgian leagues -> Elite Series -> Road of Legends
    "Liga Nexo", #spanish third league
    "LCK AS", #parent: LCK CL
    "LST", #philippines and thailand
]

def team_name_to_id(name):
    name_to_id = {
        "DAMWON Gaming": "Dplus KIA",
        "DWG KIA": "Dplus KIA",
        "SK Telecom T1": "T1",
        "Vici Gaming": "Rare Atom",
        "Incredible Miracle": "DRX",
        "Longzhu Gaming": "DRX",
        "Kingzone DragonX": "DRX",
        "DragonX": "DRX",
        "Samsung Ozone": "Samsung White",
        "HUYA Tigers": "ROX Tigers",
        "GE Tigers": "ROX Tigers",
        "Rogue (European Team)": "Rogue",
        "Team Dynamics": "Nongshim RedForce",
        "Liiv SANDBOX": "BNK FEARX",
        "SANDBOX Gaming": "BNK FEARX",
        "FearX": "BNK FEARX",
        "SinoDragon Gaming": "ThunderTalk Gaming",
        "Dominus Esports": "ThunderTalk Gaming",
        "Kwangdong Freecs": "DN Freecs",
        "Afreeca Freecs": "DN Freecs",
        "Rogue Warriors": "Anyone's Legend",
        "Snake Esports": "LNG Esports",
        "KSV eSports": "Gen.G",
        "Topsports Gaming": "Top Esports",
        "PSG Talon": "TALON (Hong Kong Team)",
        "Brion Blade": "OKSavingsBank BRION",
        "hyFresh Blade": "OKSavingsBank BRION",
        "Fredit BRION": "OKSavingsBank BRION",
        "BRION": "OKSavingsBank BRION",
        "MAD Lions": "MAD Lions KOI",
    }

    return name_to_id.get(name, name)

def event_to_league_name(event):
    league_name = None
    
    if ("Promotion" not in event and "Qualifier" not in event and "Expansion" not in event and "Pro-Am" not in event):
        match = re.findall("^(.*) 20\d{2}",event)
        if match:
            league_name = match[0]

    if re.findall("^LJL 20\d{2} Academy League",event):
        league_name = "LJL Academy"

    if re.findall("^Korea Regional Finals",event):
        league_name = "LCK"

    if re.findall("^Ultraliga",event):
        league_name = "Ultraliga"
            
    if re.findall("^Premier Tour",event):
        league_name = "ESLM"

    return league_name


def league_name_to_id(league_name):
   name_to_id = {
       "NA LCS": "LCS",
       "EU LCS": "LEC",
       "LSPL": "LDL",
       "NLB": "LCK CL",
       "CK": "LCK CL",
       "NACS": "NACL",
       "NA Academy": "NACL",
       "Champions": "LCK",
       "PRM Pro Division": "PRM 1st Division",
       "PG Nationals": "LIT",
       "Ultraliga": "Rift Legends",
       "LVP SLO": "LVP SL",
       "VDL": "VL",
       "LHE": "LH",
       "LAS": "CLS",
       "TPL": "TCL Division 2",
       "TCS": "TCL Division 2",
       "Turkey Academy": "TCL Division 2",
       "OPL": "LCO",
       "Elite Series": "Road Of Legends",
       "BRCC": "CBLOL Academy",
       "FCS": "EBL",
       "UPL": "ACL",
       "GL2D": "HCC",
       "GLWL": "HCC",
       "GLL": "HLL",
   }
 
   league_id = name_to_id.get(league_name,league_name)

   return league_id

def load_data():
    all_rows = []
    for f in glob.glob("../data/lol/*"):
        reader = csv.DictReader(open(f))
        all_rows += [row for row in reader]

    team_to_league_name = {}
    for row in all_rows:
        team1_name = row["Team1"]
        team1_id = team_name_to_id(team1_name)

        team2_name = row["Team2"]
        team2_id = team_name_to_id(team2_name)

        winner_name = row["WinTeam"]
        winner_id = team_name_to_id(winner_name)

        league_name = event_to_league_name(row["Tournament"])
        league_id = league_name_to_id(league_name)

        if league_id in RECOGNIZED_LEAGUES:
            team_to_league_name[team1_id] = league_name
            team_to_league_name[team2_id] = league_name

        team1_league_name = team_to_league_name.get(team1_id, "unknown")
        team1_league_id = league_name_to_id(team1_league_name)

        team2_league_name = team_to_league_name.get(team2_id, "unknown")
        team2_league_id = league_name_to_id(team2_league_name)
        
        yyyymmdd = row["DateTime UTC"].split()[0].replace("-","")

        yield {
            "type": "match",
            "yyyymmdd": yyyymmdd,
            "event": row["Tournament"],
            "results": [
                {
                    "player_id": team1_id,
                    "player_name": team1_name,
                    "league_id": team1_league_id,
                    "league_name": team1_league_name,
                    "opp_id": team2_id,
                    "opp_name": team2_name,
                    "is_home": "NEUTRAL",
                    "score": 1*(team1_name == winner_name),
                    "raw_score": 1*(team1_name == winner_name)
                },
                {
                    "player_id": team2_id,
                    "player_name": team2_name,
                    "league_id": team2_league_id,
                    "league_name": team2_league_name,
                    "opp_id": team1_id,
                    "opp_name": team1_name,
                    "is_home": "NEUTRAL",
                    "score": 1*(team2_name == winner_name),
                    "raw_score": 1*(team2_name == winner_name)
                }
            ]
        }
    
if __name__ == "__main__":
    all_match_data = sorted(list(load_data()),key=lambda x: x["yyyymmdd"])

    def get_cutoff(year):
        all_year_ends = {
            "2011": "0620",
            "2012": "1014",
            "2013": "1005",
            "2014": "1019",
            "2015": "1031",
            "2016": "1030",
            "2017": "1104",
            "2018": "1103",
            "2019": "1110",
            "2020": "1031",
            "2021": "1106",
            "2022": "1106",
            "2023": "1119",
            "2024": "1102",
            "2025": "1201", #placeholder
        }
        if year > max(all_year_ends.keys()):
            print(f"need to add new year end for {year}")
            raise
        return all_year_ends[year]
        
    all_events = elo.add_year_ends(all_match_data, get_cutoff)

    config = {
        "name": "lol",
        "basic_elo": True,
        "print_new": False,
        "output_dir": "../",
        "home_adv": 0,
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
                "new_k_mult": 2.5,
                "player": {
                    "k": 35,
                    "update_max": 1000,
                    "year_end_shrinkage_frac": 0.5,
                },
                "league": {
                    "k": 15,
                    "update_max": 1000,
                    "year_end_shrinkage_frac": 0.05,
                },
            }
        },
        "normalize": True,
        "normalize_cnt": 2*16, #2x number of worlds teams
        "record_scores": True,
    }

    elo_calc = elo.Elo(all_events, config)
    elo_calc.generate_elos()
    elo_calc.print_elos()

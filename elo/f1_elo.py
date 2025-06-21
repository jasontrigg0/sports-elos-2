import sys
sys.path.append(".")
import elo
import csv
import glob

def load_data():
    all_files = glob.glob("../data/f1/f1_*.csv")

    all_rows = []
    for filename in all_files:
        reader = csv.DictReader(open(filename))
        all_rows += [row for row in reader]

    all_race_results = {}

    def preprocess_team_name(team_name):
        #https://en.wikipedia.org/wiki/1957_German_Grand_Prix
        #"To increase participation, the organizers opened the field to Formula 2 cars. The two races were run at the same time but the Formula 2 entries (shown in yellow) were not eligible for World Championship points and some sources do not consider these starts in career stats."
        #these are included for now, including this "Porsche (F2)" row
        if team_name == "Porsche (F2)":
            team_name = "Porsche"

        #typos / inconsistencies
        team_name = team_name.replace("Mclaren","McLaren")
        team_name = team_name.replace("Iso Marlboro","Iso-Marlboro")
        team_name = team_name.replace("Offerhauser", "Offenhauser")

        if team_name == "Frank Williams Racing Cars/Williams":
            team_name = "Frank Williams Racing Ford"

        if team_name == "Wolf-Williams":
            team_name = "Wolf-Williams Ford"

        if team_name == "Maserati-Offenhauser":
            team_name = "Maserati Offenhauser"

        if team_name == "Thin Wall Ferrari": #special ferrari
            team_name = "Ferrari"


        #potential prefix issues
        team_name = team_name.replace("Red Bull Racing", "Red Bull")
        team_name = team_name.replace("Aston Martin Aramco", "Aston Martin")
        team_name = team_name.replace("Alfa Romeo Racing", "Alfa Romeo")
        return team_name

    def split_team_name(team_name):
        chassis_constructors = ["McLaren", "Williams", "Lotus", "Sauber", "Kick Sauber", "Tyrrell", "Arrows", "Ferrari", "Alfa Romeo", "Red Bull", "RBR", "Aston Martin", "Mercedes-Benz", "Mercedes", "Matra", "March", "Renault", "Brabham", "Footwork", "Minardi", "Ligier", "Scuderia Toro Rosso", "STR", "Toro Rosso", "Benetton", "Jordan", "Force India", "BRM", "Lola", "Toyota", "Osella", "Cooper", "Surtees", "BAR", "Fittipaldi", "Shadow", "Haas", "Alpine", "Ensign", "ATS", "Honda", "Jaguar", "Prost", "Dallara", "Marussia", "Maserati", "Caterham", "HRT", "Zakspeed", "Toleman", "Hesketh", "Stewart", "Wolf", "Penske", "Super Aguri", "Racing Point", "Virgin", "Theodore", "Gordini", "Porsche", "AGS", "Larrousse", "RAM", "Leyton House", "Vanwall", "Eagle", "Forti", "Spirit", "Pacific", "MRT", "Rial", "Simtek", "Fondmetal", "MF1", "Spyker", "Brawn", "Connaught", "Onyx", "Parnelli", "Venturi", "Euro Brun", "HWM", "Simca-Gordini", "BRP", "Coloni", "Talbot-Lago", "Kurtis Kraft", "Hill", "Tecno", "Kuzma", "Phillips", "Stevens", "Pankratz", "Pawl", "Nichels", "Schroeder", "Bromme", "Klenk", "Lancia", "Scirocco", "Derrington-Francis", "De Tomaso", "Bellasi", "Merzario", "Martini", "Frank Williams Racing", "Lyncar", "Lambo", "Veritas", "Sherman", "Moore", "Deidt", "Hall", "Marchese", "Trevis", "Lesovsky", "Watson", "ERA", "Alta", "OSCA", "LEC", "Boro", "Kojima", "Iso-Marlboro", "Trojan", "Amon", "Token", "Behra-Porsche", "Epperly", "Meskowski", "Christensen", "Ewing", "Scarab", "JBW", "Frazer Nash", "AFM", "Aston Butterworth", "BMW", "AlphaTauri", "Langley", "Rae", "Olson", "Wetteroth", "Snowberger", "Adams", "Dunn", "Elder", "Sutton", "Tec-Mec", "Turner", "Del Roy", "EMW", "RB", "Shannon", "LDS", "Gilby", "Stebro", "Ferguson", "Rebaque", "Moda", "Emeryson", "ENB", "Bugatti", "Wolf-Williams", "Racing Bulls", "Protos", "Eifelland", "Politoys", "Connew"]

        for cc in chassis_constructors:
            if team_name == cc:
                return {
                    "chassis": cc,
                    "engine": ""
                }
            elif team_name.startswith(cc + " "):
                #if there chassis and engine constructors are different
                #then both may be listed eg: "McLaren Mercedes" means
                #chassis is McLaren and the engine is Mercedes
                return {
                    "chassis": cc,
                    "engine": team_name.split(cc,1)[1].strip()
                }

        print("chassis constructor not found")
        print(team_name, year)
        raise

    
    def get_chassis(chassis, year):
        #working largely off of this
        #https://www.reddit.com/r/formula1/comments/lp0qru/a_timeline_of_every_constructor_in_formula_1/#lightbox
        if chassis == "Alfa Romeo" and year in [2019,2020,2021,2022,2023]:
            #Alfa Romeo was the sponsor, Sauber the constructor
            chassis = "Sauber"
        if chassis == "Honda" and year in [2006,2007,2008]:
            chassis = "Mercedes"
        if chassis == "Renault" and year >= 2002 and year <= 2011:
            chassis = "Alpine"
        if chassis == "Lotus" and year in [2012,2013,2014,2015]:
            chassis = "Alpine"
        if chassis == "Lotus" and year in [2010,2011]:
            chassis = "Caterham"

        chassis_map = {
            "Kick Sauber": "Sauber", #2024 - 2025
            "Mercedes-Benz": "Mercedes",
            "Tyrrell": "Mercedes",
            "BAR": "Mercedes",
            "Brawn": "Mercedes",
            "Toleman": "Alpine",
            "Benetton": "Alpine",
            "Jordan": "Aston Martin",
            "MF1": "Aston Martin",
            "Spyker": "Aston Martin",
            "Force India": "Aston Martin",
            "Racing Point": "Aston Martin",
            "Ligier": "Prost",
            "RAM": "March",
            "Leyton House": "March",
            "Frank Williams Racing": "Wolf",
            "Wolf-Williams": "Wolf",
            "Footwork": "Arrows",
            "Osella": "Fondmetal",
            "Minardi": "Scuderia Toro Rosso", #1985 - 2005
            "STR": "Scuderia Toro Rosso", #2006 - 2015
            "Toro Rosso": "Scuderia Toro Rosso", #2016 - 2017
            "AlphaTauri": "Scuderia Toro Rosso", #2020 - 2023
            "RB": "Scuderia Toro Rosso", #2024
            "Racing Bulls": "Scuderia Toro Rosso", #2025
            "Coloni": "Moda", #1988
            "Venturi": "Larrousse", #1992
            "Stewart": "Red Bull", #1997 - 1999
            "Jaguar": "Red Bull", #2000 - 2004
            "RBR": "Red Bull", #2005 - 2006, 2009 - 2010
            "Virgin": "MRT", #2010 - 2011
            "Marussia": "MRT", #2012 - 2015
        }
        chassis = chassis_map.get(chassis,chassis)
        return chassis
        
    def get_engine(chassis, engine, year):
        engine_constructors = ["Mercedes", "Renault", "Ferrari", "Honda", "Cosworth", "BMW", "Toyota", "Petronas", "Ford", "Lamborghini", "Yamaha", "Judd", "Porsche", "Ilmor", "Mugen Honda", "Hart", "Peugeot", "Mecachrome", "TAG", "Zakspeed", "Alfa Romeo", "Motori Moderni", "Matra", "BRM", "Pratt & Whitney", "Tecno", "Repco", "Maserati", "Climax", "ATS", "Serenissima", "Weslake", "OSCA", "Gordini", "Offenhauser", "Mercedes-Benz", "Alta", "Bristol", "Lea Francis", "Vanwall", "Lancia", "Talbot-Lago", "Veritas", "Novi", "Milano", "ERA", "Scarab", "Aston Martin", "Plate", "Kuchen", "Cummins", "Aston Butterworth", "JAP", "Jaguar", "Borgward", "EMW", "Bugatti"]

        if engine == "":
            if chassis in engine_constructors:
                engine = chassis
            elif chassis == "Arrows":
                engine = "Hart"
            elif chassis == "Simca-Gordini":
                engine = "Gordini"

        if chassis == "Toro Rosso" and year == 2017:
            engine = "Renault"
        if chassis == "Sauber" and year == 1993:
            engine = "Ilmor"
        if chassis == "Osella" and year == 1988:
            engine = "Alfa Romeo"
        if chassis == "Behra-Porsche" and year == 1960:
            engine = "Porsche"
        if chassis == "Frazer Nash" and year == 1952:
            engine = "Bristol"
        if chassis == "McLaren" and year == 2025:
            engine = "Mercedes"
        if chassis == "Red Bull" and year == 2025:
            engine = "Honda"
        if chassis == "Racing Bulls" and year == 2025:
            engine = "Honda"
        if chassis == "Williams" and year == 2025:
            engine = "Mercedes"
        if chassis == "Kick Sauber" and year == 2025:
            engine = "Ferrari"
        if chassis == "Haas" and year == 2025:
            engine = "Ferrari"
        if chassis == "Alpine" and year == 2025:
            engine = "Renault"
        if chassis == "Aston Martin" and year == 2025:
            engine = "Mercedes"
        
        engine_map = {
            "BWT Mercedes": "Mercedes",
            "Honda RBPT": "Honda",
            "Acer": "Ferrari",
            "Asiatech": "Peugeot", #bought the assets of Peugeot
            "European": "Ford",
            "Fondmetal": "Ford",
            "Playlife": "Mecachrome",
            "Supertec": "Mecachrome",
            "Megatron": "BMW",
            "Castellotti": "Ferrari",
        }
        if engine == "RBPT" and year == 2022:
            #"Red Bull-branded Honda engines"
            engine = "Honda"
        if engine == "TAG Heuer" and year in [2016,2017,2018]:
            #Red Bull have announced they will continue to use Renault engines
            #next season, but with the power unit branded TAG Heuer, after the
            #team's new timing partner
            engine = "Renault"
            
        engine = engine_map.get(engine, engine)
        
        if engine not in engine_constructors:
            print(chassis, engine, year)
            raise
        
        return engine

    def team_name_to_chassis_engine(team_name, year):
        if team_name == "":
            return {
                "chassis": "",
                "engine": ""
            }
        team_name = preprocess_team_name(team_name)
        raw_chassis = split_team_name(team_name)["chassis"]
        raw_engine = split_team_name(team_name)["engine"]

        chassis = get_chassis(raw_chassis, year)
        engine = get_engine(raw_chassis, raw_engine, year)
        
        return {
            "chassis": chassis,
            "engine": engine
        }
        
    for row in all_rows:
        year = int(row["year"])
        constructor = row["constructor"].strip()
        row["chassis"] = team_name_to_chassis_engine(constructor,year)["chassis"]
        row["engine"] = team_name_to_chassis_engine(constructor,year)["engine"]
        all_race_results.setdefault(row["event_id"],[]).append(row)

    league = "f1"
    #add one match for each pair of drivers in each race
    for race in all_race_results:
        all_race_matches = []
        
        rows = [x for x in all_race_results[race] if x["position"] not in ["NC","DQ","EX","DNS"] and x["time"] != "DNF"]
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

                key = (r1["event_id"],r1["driver"],r2["driver"])

                match_results = [
                    {
                        "player_id": r1["driver"],
                        "player_name": r1["driver"],
                        "chassis_id": r1["chassis"],
                        "chassis_name": r1["chassis"],
                        "engine_id": r1["engine"],
                        "engine_name": r1["engine"],
                        "league_id": league,
                        "league_name": league,
                        "opp_id": r2["driver"],
                        "opp_name": r2["driver"],
                        "is_home": "NEUTRAL",
                        "score": r1_score,
                        "raw_score": r1_score
                    },
                    {
                        "player_id": r2["driver"],
                        "player_name": r2["driver"],
                        "chassis_id": r2["chassis"],
                        "chassis_name": r2["chassis"],
                        "engine_id": r2["engine"],
                        "engine_name": r2["engine"],
                        "league_id": league,
                        "league_name": league,
                        "opp_id": r1["driver"],
                        "opp_name": r1["driver"],
                        "is_home": "NEUTRAL",
                        "score": 1-r1_score,
                        "raw_score": 1-r1_score
                    }
                ]
                all_race_matches.append(match_results)
        yield {
            "type": "match_group",
            "yyyymmdd": r1["date"],
            "event": r1["event_id"],
            "matches": all_race_matches,
        }
                

if __name__ == "__main__":
    all_match_data = sorted(list(load_data()),key=lambda x: x["yyyymmdd"])
    all_match_data = elo.add_year_ends(all_match_data, lambda x: "1231")

    config = {
        "name": "f1",
        "basic_elo": True,
        "print_new": False,
        "output_dir": "../",
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
                "name": "chassis",
                "external_id": "chassis_id",
                "external_name": "chassis_name",
                "event_subtype": False,
                "primary": False,
            },
            {
                "name": "engine",
                "external_id": "engine_id",
                "external_name": "engine_name",
                "event_subtype": False,
                "primary": False,
            }
        ],
        "elo_settings": {
            "default": {
                "new_k_mult": 26,
                "player": {
                    "k": 11,
                    "update_max": 16,
                    "year_end_shrinkage_frac": 0.20,
                },
                "chassis": {
                    "k": 4.5,
                    "update_max": 6,
                    "year_end_shrinkage_frac": 0.10,
                },
                "engine": {
                    "k": 2.5,
                    "update_max": 3,
                    "year_end_shrinkage_frac": 0.40,
                }
            }
        },
        "normalize": True,
        "normalize_cnt": 20,
        "alltime_window": 10000, #240
        "record_scores": True,
        #"score_metric": lambda info: info["comp"]["player"],
    }

    elo_calc = elo.Elo(all_match_data, config)
    elo_calc.generate_elos()
    elo_calc.print_elos()

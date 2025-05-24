import datetime
import math
import random
import bisect
import itertools
import csv

def pairwise(iterable):
    "s -> (s0,s1), (s1,s2), (s2, s3), ... (sN, None)"
    a, b = itertools.tee(iterable)
    next(b, None)
    return itertools.zip_longest(a,b)

def add_year_ends(all_match_data, get_cutoff):
    for prev,next_ in pairwise(all_match_data):
        year = prev["yyyymmdd"][:4]
        following_year = str(int(year)+1)

        mmdd = prev["yyyymmdd"][4:]
        mmdd_cutoff = get_cutoff(year)
        
        if mmdd <= mmdd_cutoff:
            year_end = year + mmdd_cutoff
        else:
            year_end = following_year + mmdd_cutoff
            
        yield prev
        if prev["yyyymmdd"] <= year_end and next_ and next_["yyyymmdd"] > year_end:
            yield {
                "type": "year_end",
                "yyyymmdd": year_end
            }
    

def get_simple_match_res(info):
    home_score = float(info["home_score"])
    away_score = float(info["away_score"])
    score = 1 * (home_score > away_score) + 0.5 * (home_score == away_score)

    if int(info["is_neutral"]):
        home1 = "NEUTRAL"
        home2 = "NEUTRAL"
    else:
        home1 = "HOME"
        home2 = "AWAY"
        
    return [
        {
            "player_id": info["home_id"],
            "player_name": info["home_name"],
            "league_id": info.get("home_league_id",info.get("league_id")),
            "league_name": info.get("home_league_name", info.get("league_name")),
            "opp_id": info["away_id"],
            "opp_name": info["away_name"],
            "is_home": home1,
            "score": score,
            "raw_score": home_score,
            "score_type": "default",
        },
        {
            "player_id": info["away_id"],
            "player_name": info["away_name"],
            "league_id": info.get("away_league_id",info.get("league_id")),
            "league_name": info.get("away_league_name",info.get("league_name")),
            "opp_id": info["home_id"],
            "opp_name": info["home_name"],
            "is_home": home2,
            "score": 1 - score,
            "raw_score": away_score,
            "score_type": "default",
        }

    ]

def diff_days(yyyymmdd1, yyyymmdd2):
    return (datetime.datetime.strptime(yyyymmdd1,"%Y%m%d") - datetime.datetime.strptime(yyyymmdd2,"%Y%m%d")).days

def compute_expected_from_elo(elo_diff):
    return (1.0 / (1.0 + 10**(-1 * elo_diff / 400.)))

def sigmoid(x, max_val, slope_at_zero=1):
    if abs(-x * 2 * slope_at_zero / max_val) > 100:
        return max_val if x > 0 else -1 * max_val
    return max_val * (2 / (1 + math.exp(-x * (2 * slope_at_zero / max_val))) - 1)

class BestNeighborList:
    def __init__(self, max_size, filter_fn, neighbor_fn):
        self.list_ = []
        self.max_size = max_size
        self.filter_fn = filter_fn
        self.neighbor_fn = neighbor_fn
    def _test(self, input_):
        if self.filter_fn and not self.filter_fn(input_[2]):
            return False
        
        #abort if not in the top self.max_size
        if len(self.list_) == self.max_size and input_ > self.list_[-1]:
            return False

        neighbors = [x for x in self.list_ if self.neighbor_fn(input_[2], x[2])]

        #abort if not the best neighbor
        if neighbors and input_ > neighbors[0]:
            return False

        return True
    def clear(self):
        self.list_ = []
    def push(self, elt, prio, if_pass_fn=None):
        #use random as a tiebreak
        input_ = (prio, random.random(), elt)

        if not self._test(input_): return

        if if_pass_fn:
            if_pass_fn()
        
        #remove existing neighbors
        for i,x in enumerate(self.list_):
            if self.neighbor_fn(input_[2], x[2]):
                self.list_.pop(i)

        #add input

        # print("---")
        # print([x[0] for x in self.list_], input_[0])
        
        bisect.insort(self.list_, input_)

        # print([x[0] for x in self.list_], input_[0])
        
        #restrict whole list to max_size
        self.list_ = self.list_[:self.max_size]
        
    def to_list(self):
        return [x[2] for x in self.list_]

class AllTimeList(BestNeighborList):
    def __init__(self, config):
        key = config["key"]
        cnt = config["cnt"]
        window = config["window"]
        start = config["start"]
        filter_fn = lambda x: (not start) or (start < x["yyyymmdd"])
        is_recent = lambda x,y: x[key] == y[key] and diff_days(x["yyyymmdd"], y["yyyymmdd"]) < window
        super().__init__(cnt, filter_fn, is_recent)
    
class Elo:
    def __init__(self, all_match_info, config):
        self.all_match_info = all_match_info

        self.basic_elo = config["basic_elo"]
        self.print_new = config["print_new"]
        self.output_dir = config["output_dir"]
        
        self.home_adv = config.get("home_adv")
        
        self.elo_components = config["elo_components"]
        self.elo_settings = config["elo_settings"]
        self.has_slow = config.get("has_slow")
        
        for comp in self.elo_components:
            comp["starting_elo"] = 0
        
        self.normalize = config["normalize"]
        self.normalize_cnt = config["normalize_cnt"]

        self.record_scores = config["record_scores"]
        self.modern_era_start = config.get("modern_era_start")
        self.name = config["name"]
        self.year_round = config.get("year_round",False)
        self.has_binary_result = config.get("has_binary_result",True)
        
        #standard variables
        self.primary_component = [comp for comp in self.elo_components if comp["primary"]][0]
        self.primary_key = self.primary_component["name"]
        self.primary_external_id = self.primary_component["external_id"]
        self.alltime_cnt = 100
        self.sign = config.get("sign",1) #higher elo is better
        self.alltime_window = config.get("alltime_window",180)
        self.score_metric = config.get("score_metric", lambda info: info["raw"])
        self.inactive_window = config.get("inactive_window",300) #set long enough to include the whole offseason!

        self.hard_coded_league_elos = config.get("hard_coded_league_elos")
        self.print_elo_by_date = config.get("print_elo_by_date",False)
        
        self.data = self.init_data()
    def generate_elos(self):
        self.data["last_active"] = {}
        self.data["latest_match_date"] = None
        
        stats = {
            "err": 0,
        }

        with open("output.csv","w") as f_out:
            writer = csv.DictWriter(f_out, fieldnames=["yyyymmdd","player_id","player","elo"])
            writer.writeheader()
            for info, next_ in pairwise(self.all_match_info):
                if info["type"] == "year_end":
                    self.update_year_end()
                else:
                    if info["type"] == "match_group":
                        match_group = info
                    elif info["type"] == "match":
                        match_group = {
                            "type": "match_group",
                            "yyyymmdd": info["yyyymmdd"],
                            "event": info["event"],
                            "matches": [info["results"]]
                        }
                    else:
                        raise

                    match_stats = self.update_elos_from_match_group(match_group, "main")
                    
                    if self.has_slow:
                        self.update_elos_from_match_group(match_group, "slow")

                    if self.print_elo_by_date: #TODO: fix
                        if (next_ is None) or (info["yyyymmdd"] != next_["yyyymmdd"]):
                            all_sorted_elos = self.get_sorted_active_elos(self.data["latest_match_date"])
                            for x in all_sorted_elos["total"][:100]:
                                writer.writerow({
                                    "yyyymmdd": info["yyyymmdd"],
                                    "player_id": x[0],
                                    "player": x[1],
                                    "elo": x[2],
                                })
                        
                stats["err"] += match_stats["err"]

        self.normalize_elos(info["yyyymmdd"])
        print(f"Error: {stats}")
    def update_elos_from_match_group(self, match_group, version="main"):
        stats = {
            "err": 0,
        }

        update_info = []

        if version == "main":
            self.data["latest_match_date"] = match_group["yyyymmdd"]

        for match_results in match_group["matches"]:
            match_results = [self.get_full_result(x, match_group) for x in match_results]

            if version == "main":
                for res in match_results:
                    self.run_match_setup(res, match_results)
                    
            player_to_relative_score = self.get_relative_score(match_results)
            player_to_relative_skill = self.get_relative_skill(match_results, version)

            for res in match_results:
                relative_skill = player_to_relative_skill[res["player_id"]]
                relative_score = player_to_relative_score[res["player_id"]]
                delta, err = self.calc_delta_err(res, relative_skill, relative_score, version)

                stats["err"] += err**2

                if version == "main":
                    #update the all time upsets before updating elos
                    self.update_upsets(res, err)

                update_info.append({
                    "res": res,
                    "delta": delta,
                })

        for update in update_info:
            if version == "slow":
                self.update_slow(update["res"], update["delta"])
            elif version == "main":
                self.update_comp_raw(update["res"],update["delta"])
            else:
                raise

        # print(res["yyyymmdd"])
        # print(self.data[self.primary_key].get("1",None), self.data["constructor"].get("131",None))

        if version == "main":
            for update in update_info:
                self.update_alltime(update["res"])

        return stats
    def run_match_setup(self, res, match_results):
        for comp in self.elo_components:
            self.data["most-recent-res"].setdefault(comp["name"],{})
            self.data["most-recent-res"][comp["name"]][res[comp["external_id"]]] = res
        
        #initialize relevant fields
        self.update_match_cnts(res, match_results)

        #eg initialize elo for a new league
        #and track the current league for a team
        self.update_comp_info(res)

        self.data["last_active"][res["player_id"]] = res["yyyymmdd"]
            
    def update_match_cnts(self, res, match_results):
        player = res[self.primary_external_id]
        for comp in self.elo_components:
            value = res[comp["external_id"]]
            self.data["match_cnts"].setdefault(comp["name"],{})
            self.data["match_cnts"][comp["name"]].setdefault("_overall",{})
            if comp["event_subtype"]:
                self.data["match_cnts"][comp["name"]].setdefault(player,{})
                self.data["match_cnts"][comp["name"]][player].setdefault(value,0)
                self.data["match_cnts"][comp["name"]][player][value] += 1
                
                self.data["match_cnts"][comp["name"]]["_overall"].setdefault(value,0)

                #maintain weighted average
                for x in self.data["match_cnts"][comp["name"]]["_overall"]:
                    self.data["match_cnts"][comp["name"]]["_overall"][x] *= 0.9999
                self.data["match_cnts"][comp["name"]]["_overall"][value] += 1
            else:
                self.data["match_cnts"].setdefault(comp["name"],{})
                self.data["match_cnts"][comp["name"]].setdefault(value,0)
                
                distinct_contestants = list(set([x[comp["external_id"]] for x in match_results]))
                #don't update match_cnts for a component if it's playing itself
                #eg two teams from the same league playing each other doesn't
                #count as a match for that league
                if len(distinct_contestants) > 1:
                    self.data["match_cnts"][comp["name"]][value] += 1
                    
    def update_comp_info(self, res):
        player_id = res[self.primary_external_id]
        player_info = self.data["primary_info"].setdefault(player_id,{})
        for comp in self.elo_components:
            name = comp["name"]
            prior_value = player_info.get(name)

            value = res[comp["external_id"]]
            display = res[comp["external_name"]]
            
            self.data["id_to_name"].setdefault(comp["name"],{})
            self.data["id_to_name"][comp["name"]][value] = display
            
            #update player_info for this component
            if not comp["event_subtype"]:
                player_info[name] = value
        
            #initialize elo if needed
            starting_elo = comp["starting_elo"]
            if value not in self.data[name] and self.print_new:
                print(name, value, res["yyyymmdd"], starting_elo)

            if comp["event_subtype"]:
                self.data[name].setdefault(player_id,{}).setdefault(value,starting_elo)
            else:
                self.data[name].setdefault(value,starting_elo)

            if self.has_slow and name == self.primary_component["name"]:
                self.data["_slow"].setdefault(value,starting_elo)
                
            #if changing leagues then update elos accordingly
            if name == "league" and prior_value and value != prior_value and prior_value != "unknown":
                # print(f"league change! {player}, {prior_value}, {value}")
                if self.hard_coded_league_elos:
                    if self.hard_coded_league_elos[prior_value] is not None and self.hard_coded_league_elos[value] is not None:
                        elo_change = self.hard_coded_league_elos[prior_value] - self.hard_coded_league_elos[value]
                        # print(elo_change)
                    else:
                        elo_change = 0
                else:
                    elo_change = self.data[name][prior_value] - self.data[name][value]
                self.data[self.primary_key][player_id] += elo_change
    def calc_delta_err(self, res, relative_skill, relative_score, version):
        if self.has_binary_result:
            wdl_outcome = res["score"] #1 for win, 0.5 for draw 0 for loss
            wdl_prediction = compute_expected_from_elo(relative_skill)
            
        if self.basic_elo:
            delta = wdl_outcome - wdl_prediction
        else:
            if version == "main":
                raw_to_elo_mult = self.elo_settings[res["score_type"]]["raw_to_elo_mult"]
            elif version == "slow":
                raw_to_elo_mult = self.elo_settings["slow"]["raw_to_elo_mult"]
            else:
                raise

            # delta = raw_to_elo_mult * sigmoid(res["raw_score"], sigmoid_max) - raw_diff
            sigmoid_max = self.elo_settings[res["score_type"]]["sigmoid_max"]

            sigmoid_max_neg = self.elo_settings[res["score_type"]].get("sigmoid_max_neg")
            if self.sign * relative_score < 0 and (sigmoid_max_neg is not None):
                sigmoid_max = sigmoid_max_neg

            tapered_score = sigmoid(relative_score, sigmoid_max)
            delta = raw_to_elo_mult * tapered_score - relative_skill

        if self.has_binary_result:
            err = (wdl_outcome - wdl_prediction)
        else:
            err = (relative_score - relative_skill)
            
        return delta, err

    def calculate_update(self, res, delta, comp, k=None):
        player_id = res[self.primary_external_id]
        score_type = res.get("score_type","default")

        update_max = self.elo_settings[score_type][comp["name"]]["update_max"]

        if not k:
            k = self.elo_settings[score_type][comp["name"]]["k"]

        value = res[comp["external_id"]]
        if comp["event_subtype"]:
            match_cnt = max(self.data["match_cnts"][comp["name"]][player_id][value],1)
        else:
            match_cnt = max(self.data["match_cnts"][comp["name"]][value],1)

        new_k_mult = self.elo_settings[score_type]["new_k_mult"]
        k *= 1 + (new_k_mult/(match_cnt))

        return sigmoid(k * delta * res.get("weight",1), update_max)

    def update_slow(self, res, delta):
        comp = self.primary_component
        k = self.elo_settings["slow"]["k"]
        update = self.calculate_update(res, delta, comp, k)
        value = res[comp["external_id"]]
        self.data["_slow"][value] += update
        
    def update_comp_raw(self, res, delta):
        player_id = res[self.primary_external_id]
        
        for comp in self.elo_components:
            update = self.calculate_update(res, delta, comp)
            value = res[comp["external_id"]]
            if comp["event_subtype"]:
                self.data[comp["name"]][player_id][value] += update
            else:
                self.data[comp["name"]][value] += update

        #renormalize for event_subtype components
        for comp in self.elo_components:
            if comp["event_subtype"]:
                total_cnt = 0
                for x in self.data["match_cnts"][comp["name"]]["_overall"]:
                    total_cnt += self.data["match_cnts"][comp["name"]]["_overall"][x]

                event_subtype_total = 0
                for x in self.data["match_cnts"][comp["name"]]["_overall"]:
                    frac = self.data["match_cnts"][comp["name"]]["_overall"][x] / total_cnt
                    self.data[comp["name"]][player_id].setdefault(x,comp["starting_elo"])
                    event_subtype_total += frac * self.data[comp["name"]][player_id][x]

                for x in self.data["match_cnts"][comp["name"]]["_overall"]:
                    self.data[comp["name"]][player_id][x] -= event_subtype_total

                self.data[self.primary_component["name"]][player_id] += event_subtype_total
                

    def normalize_elos(self, yyyymmdd):
        if not self.normalize:
            return

        #reset so the average elo among the
        #self.normalize_cnt is self.baseline_elo
        all_sorted_active_elos = self.get_sorted_active_elos(yyyymmdd)
        
        #want top player cnt of total elo
        top_elos = all_sorted_active_elos["total"][:self.normalize_cnt]
        # print(top_elos)
        # print(top_elos_new)
        
        for comp in self.elo_components:
            if comp["event_subtype"]: continue
            sorted_active_elos = all_sorted_active_elos[comp["name"]]
            avg_elo = sum([self.data[comp["name"]][self.data["primary_info"][info[self.primary_external_id]][comp["name"]]] for info in top_elos]) / len(top_elos)
            comp["starting_elo"] -= avg_elo

            for id_ in self.data[comp["name"]]:
                self.data[comp["name"]][id_] -= avg_elo
        if self.has_slow:
            avg_elo = sum([self.data["_slow"][info[self.primary_external_id]] for info in top_elos]) / len(top_elos)
            for id_ in self.data["_slow"]:
                self.data["_slow"][id_] -= avg_elo
    def get_aggregate_raw(self, res, include_modifiers):
        total = 0
        for comp in self.elo_components:
            if comp["event_subtype"]:
                if include_modifiers:
                    total += self.data[comp["name"]][res[self.primary_external_id]][res[comp["external_id"]]]
            else:
                total += self.data[comp["name"]][res[comp["external_id"]]]
        return total
    def get_relative_score(self, match_results):
        sum_score = sum([x["raw_score"] for x in match_results])
        player_cnt = len(match_results)

        player_to_relative_score = {}
        for res in match_results:
            cur_score = res["raw_score"]
            avg_opp_score = (sum_score - cur_score) / (player_cnt - 1)
            player_to_relative_score[res["player_id"]] = cur_score - avg_opp_score
        return player_to_relative_score
            
    def get_relative_skill(self, match_results, version="main"):
        if version == "main":
            skill_fn = lambda res: self.get_aggregate_raw(res, True)
        elif version == "slow":
            skill_fn = lambda res: self.data["_slow"][res["player_id"]]
        else:
            raise

        # leagues = set([x["league_id"] for x in match_results])
        # if len(leagues) > 1 and "LFL" in leagues:
        #     print(match_results)
        #     raise
        
        #for each contestant the difference between their skill and the opponent's
        sum_raw = sum([skill_fn(x) for x in match_results])
        player_cnt = len(match_results)

        player_to_relative_skill = {}
        
        for res in match_results:
            cur_raw = skill_fn(res)
            avg_opp_raw = (sum_raw - cur_raw) / (player_cnt - 1)

            total_raw = cur_raw + avg_opp_raw

            #record best ever matches as measured by the strength of the weaker player
            if (version == "main") and res.get("score") and res["score"] > 0:
                info = self.get_result_summary(res)
                info = {
                    # "total": round(total_raw,1),
                    "min": min(cur_raw, avg_opp_raw),
                    **info
                }

                self.data["all-time-matches"].push(info, -1 * self.sign * info["min"])

            home_mult = {
                "HOME": 1,
                "NEUTRAL": 0,
                "AWAY": -1
            }

            raw_diff = cur_raw - avg_opp_raw
            
            if home_mult[res["is_home"]]:
                if self.home_adv is None:
                    raise
                home_adv = self.home_adv * home_mult[res["is_home"]]
                raw_diff += home_adv

            player_to_relative_skill[res["player_id"]] = raw_diff

        return player_to_relative_skill
    def update_year_end(self):
        for res in self.get_sorted_active_elos(self.data["latest_match_date"])[self.primary_key]:
            info = self.get_result_summary(res)
            metric = self.score_metric(info)
            self.data["all-time-top-eoy"].push(info, -1 * self.sign * metric)
            self.data["this-year-top-eoy"].push(info, -1 * self.sign * metric)

        this_year_top = self.data["this-year-top"].to_list()[:2]
        self.data["annual-top"].append(this_year_top)
        self.data["this-year-top"].clear()

        this_year_top_eoy = self.data["this-year-top-eoy"].to_list()[:2]
        self.data["annual-top-eoy"].append(this_year_top_eoy)
        self.data["this-year-top-eoy"].clear()
            
        self.normalize_elos(self.data["latest_match_date"])
        for comp in self.elo_components:
            starting_elo = comp["starting_elo"]
            for player in self.data[comp["name"]]:
                shrinkage_frac = self.elo_settings["default"][comp["name"]]["year_end_shrinkage_frac"]
                if comp["event_subtype"]:
                    for value in self.data[comp["name"]][player]:
                        curr_elo = self.data[comp["name"]][player][value]
                        self.data[comp["name"]][player][value] = shrinkage_frac * starting_elo + (1-shrinkage_frac) * curr_elo
                else:
                    curr_elo = self.data[comp["name"]][player]
                    if self.has_slow:
                        baseline_elo = self.data["_slow"][player]
                    else:
                        baseline_elo = starting_elo
                    # if player == "Alabama":
                    # if player == "Michigan":
                    #     print(self.data["latest_match_date"], player, curr_elo, baseline_elo)
                        
                    self.data[comp["name"]][player] = shrinkage_frac * baseline_elo + (1-shrinkage_frac) * curr_elo
    def update_upsets(self, res, err):
        info = {
            "err": round(err,3),
            **self.get_result_summary(res)
        }
        self.data["all-time-upsets"].push(info, -1 * info["err"])
    def update_alltime(self, res):
        info = self.get_result_summary(res)
            
        if_pass_fn = lambda: self.normalize_elos(res["yyyymmdd"])

        metric = self.score_metric(info)

        self.data["all-time-top"].push(info, -1 * self.sign * metric, if_pass_fn)
        self.data["this-year-top"].push(info, -1 * self.sign * metric)
        
    def get_comp_info(self, res):
        player_id = res[self.primary_external_id]
        info = {}
        for comp in self.elo_components:
            name = comp["name"]
            if comp["event_subtype"]:
                val = self.data[comp["name"]][player_id][res[comp["external_id"]]]
            else:
                val = self.data[comp["name"]][res[comp["external_id"]]]
            info[name] = round(val,1)
        return info
    def get_full_result(self, res, match_group):
        return {
            **res,
            "yyyymmdd": match_group["yyyymmdd"],
            "event": match_group["event"],
        }
    def get_result_summary(self, res):
        output = {
            "name": res["player_name"],
            "yyyymmdd": res["yyyymmdd"],
            "league": res["league_name"],
            "event": res["event"],
            "opp": res["opp_name"],
            "raw": round(self.get_aggregate_raw(res, False),1),
            "comp": self.get_comp_info(res),
            "score": res.get("score",""),
        }

        if not self.basic_elo:
            output["raw_score"] = res["raw_score"]

        #testing:
        output = {
            **res,
            "raw": round(self.get_aggregate_raw(res, False),1),
            "comp": self.get_comp_info(res),
        }
        
        return output 
    def init_data(self):
        list_config = {
            "key": self.primary_external_id,
            "cnt": self.alltime_cnt,
            "window": self.alltime_window,
            "start": self.modern_era_start,
        }

        annual_best_config = {
            "key": self.primary_external_id,
            "cnt": 2,
            "window": math.inf,
            "start": None
        }
        
        data = {
            "match_cnts": {},
            "all-time-top": AllTimeList(list_config),
            "all-time-top-eoy": AllTimeList(list_config),
            "this-year-top": AllTimeList(annual_best_config),
            "annual-top": [],
            "this-year-top-eoy": AllTimeList(annual_best_config),
            "annual-top-eoy": [],
            "all-time-matches": AllTimeList(list_config),
            "all-time-upsets": AllTimeList(list_config),
            "primary_info": {},
            "id_to_name": {},
            "most-recent-res": {},
        }

        data["_slow"] = {}
        for comp in self.elo_components:
            data[comp["name"]] = {}
        
        return data
    def write_scores(self):
        if self.record_scores:
            import statistics
            import scipy.stats
            is_modern = lambda res: (not self.modern_era_start) or (res["yyyymmdd"] > self.modern_era_start)

            #NOTE: this was self.data["annual-top"] before but think people care more about
            #team end of year performance vs mid-season peaks
            annual_list = "annual-top" if self.year_round else "annual-top-eoy"
            alltime_list = "all-time-top" if self.year_round else "all-time-top-eoy"
            
            all_bests = [{"res": x[0], "score": self.score_metric(x[0])} for x in self.data[annual_list] if is_modern(x[0])]
            all_runnerups = [{"res": x[1], "score": self.score_metric(x[1])} for x in self.data[annual_list] if is_modern(x[0])]

            if len(all_bests) <= 1: return

            avg_gap = statistics.mean([x["score"] - y["score"] for x,y in zip(all_bests,all_runnerups)])
            sd_best = statistics.stdev([x["score"] for x in all_bests])
            
            rolling_mean = {}
            rolling_std = {}

            def get_stats(year):
                if year not in rolling_mean:
                    runnerups_in_range = [x["score"] for x in all_runnerups if int(year)-10 < int(x["res"]["yyyymmdd"][:4]) < int(year) + 10]
                    rolling_mean[year] = statistics.mean(runnerups_in_range) + avg_gap
                    rolling_std[year] = sd_best #statistics.stdev(runnerups_in_range)

                #print(year, rolling_mean[year], rolling_std[year])
                return rolling_mean[year], rolling_std[year]
                    
            # print(self.data[annual_list])
            # print(mean, std)
            all_sorted_elos = self.get_sorted_active_elos(self.data["latest_match_date"])
            
            fieldnames = ["category","name","date","score"]

            raw_fieldnames = fieldnames
            if len(all_sorted_elos["total"][0]["comp"]) > 1:
                raw_fieldnames += [x for x in all_sorted_elos["total"][0]["comp"]]
            
            best_raw_file = self.output_dir + f"scores/{self.name}_best_raw.csv"
            writer_best_raw = csv.DictWriter(open(best_raw_file,'w'),fieldnames=raw_fieldnames)
            writer_best_raw.writeheader()
            
            best_adj_file = self.output_dir + f"scores/{self.name}_best_adj.csv"
            writer_best_adj = csv.DictWriter(open(best_adj_file,'w'),fieldnames=fieldnames)
            writer_best_adj.writeheader()

            curr_raw_file = self.output_dir + f"scores/{self.name}_curr_raw.csv"
            writer_curr_raw = csv.DictWriter(open(curr_raw_file,'w'),fieldnames=raw_fieldnames)
            writer_curr_raw.writeheader()
            
            curr_adj_file = self.output_dir + f"scores/{self.name}_curr_adj.csv"
            writer_curr_adj = csv.DictWriter(open(curr_adj_file,'w'),fieldnames=fieldnames)
            writer_curr_adj.writeheader()

            #convert score to a scale from 0-100. The best team in the average year will score 50.
            adjust_score = lambda score, mean, std: 1 - scipy.stats.norm.cdf(-1 * self.sign * (float(score) - mean) / std)

            for i, res in enumerate(all_sorted_elos["total"]):
                year = res["yyyymmdd"][:4]
                mean, std = get_stats(year)

                raw_obj = {
                    "category": self.name,
                    "name": res[self.primary_component["external_name"]],
                    "date": self.data["latest_match_date"],
                    "score": self.score_metric(res),
                }

                #add subcomponents to the score if they exist
                if len(res["comp"].keys()) > 1:
                    for x in res["comp"]:
                        raw_obj[x] = res["comp"][x]
                
                writer_curr_raw.writerow(raw_obj)

                writer_curr_adj.writerow({
                    "category": self.name,
                    "name": res[self.primary_component["external_name"]],
                    "date": self.data["latest_match_date"],
                    "score": adjust_score(self.score_metric(res),mean,std),
                })
            for i, res in enumerate(self.data[alltime_list].to_list()):
                year = res["yyyymmdd"][:4]
                mean, std = get_stats(year)

                raw_obj = {
                    "category": self.name,
                    "name": res[self.primary_component["external_name"]],
                    "date": res["yyyymmdd"],
                    "score": self.score_metric(res),
                }
                
                if len(res["comp"].keys()) > 1:
                    for x in res["comp"]:
                        raw_obj[x] = res["comp"][x]
                        
                writer_best_raw.writerow(raw_obj)
                writer_best_adj.writerow({
                    "category": self.name,
                    "name": res[self.primary_component["external_name"]],
                    "date": res["yyyymmdd"],
                    "score": adjust_score(self.score_metric(res),mean,std),
                })
    
    def print_elos(self):
        self.write_scores()

        sorted_active_elos = self.get_sorted_active_elos(self.data["latest_match_date"])
        
        for comp_name in sorted_active_elos:
            print("---")
            print("---")
            print("---")
            print(comp_name)
            for x in sorted_active_elos[comp_name][:100]:
                print(x)
                
        print("---")
        print("greatest eoy")
        for x in self.data["all-time-top-eoy"].to_list():
            print(x)
            
        print("---")
        print("greatest peaks")
        for x in self.data["all-time-top"].to_list():
            print(x)
            
        print("---")
        print("annual")
        for x in self.data["annual-top"]:
            print(x)
            
        print("---")
        print("greatest matches")
        for x in self.data["all-time-matches"].to_list():
            print(x)
            
        print("---")
        print("greatest upsets")
        for x in self.data["all-time-upsets"].to_list():
            print(x)
    def get_sorted_active_elos(self, yyyymmdd):
        output = {}
        active_elos = self.get_active_elos(yyyymmdd)
        for comp_name in active_elos:
            comp = [x for x in self.elo_components if x["name"] == comp_name][0]
            if comp["event_subtype"]: continue
            sort_fn = lambda x: self.sign * x["comp"][comp_name]
            sorted_elos = sorted(active_elos[comp_name], key=sort_fn, reverse=True)
            output[comp_name] = sorted_elos

            if comp_name == self.primary_key:
                #add an extra "total" entry
                sort_fn = lambda x: self.sign * x["raw"]
                sorted_elos = sorted(active_elos[comp_name], key=sort_fn, reverse=True)
                output["total"] = sorted_elos
                
        return output
                
    def get_active_elos(self, yyyymmdd):
        active_elos = {}
        for comp in self.elo_components:
            comp_name = comp["name"]
            active_elos[comp_name] = []
            comp_info = self.data["most-recent-res"][comp_name]
            for id_ in comp_info:
                res = comp_info[id_]
                last_active = res["yyyymmdd"]
                if diff_days(yyyymmdd, last_active) > self.inactive_window:
                    continue
                info = self.get_result_summary(res)
                info = {
                    **info,
                    comp_name: self.data["id_to_name"][comp_name][id_],
                }
                active_elos[comp_name].append(info)
        return active_elos

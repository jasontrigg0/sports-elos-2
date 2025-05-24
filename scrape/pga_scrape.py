import requests
import time
import os
import re
import csv
import base64
import gzip
import json

#NOTE: not a secret
#this is set normally when browsing the pgatour.com site
API_KEY = 'da2-gsrx5bibzbb4njvhl7t37wqyl4' 

RESULTS_FIELD_NAMES = ["year", "tour_code", "tournament_id", "tournament_name", "course_id", "course_name", "date", "player_id", "player_name", "position", "round", "score"]

def get_all_players():
    url = 'https://orchestrator.pgatour.com/graphql'
    
    headers = {
        'x-api-key': API_KEY,
    }

    payload = {
        "operationName": "PlayerDirectory",
        "variables": {
            "tourCode": "S", #"R" #TODO: add more?
        },
        "query": "query PlayerDirectory($tourCode: TourCode!, $active: Boolean) {\n  playerDirectory(tourCode: $tourCode, active: $active) {\n    tourCode\n    players {\n      id\n      isActive\n      firstName\n      lastName\n      shortName\n      displayName\n      alphaSort\n      country\n      countryFlag\n      headshot\n      playerBio {\n        id\n        age\n        education\n        turnedPro\n      }\n    }\n  }\n}"
    }

    response = requests.post(url, headers=headers, json=payload)
    for player in response.json()["data"]["playerDirectory"]["players"]:
        yield {
            "player_id": player["id"],
            "player_name": player["displayName"]
        }

def get_player(player_id):
    url = 'https://orchestrator.pgatour.com/graphql'
    
    headers = {
        'x-api-key': API_KEY,
    }

    payload = {
        "operationName": "Player",
        "variables": {
            "playerId": player_id,
        },
        "query": "query Player($playerId: ID!) {\n  player(id: $playerId) {\n    bioLink\n    countryFlag\n    country\n    displayName\n    firstName\n    id\n    lastName\n    playerBio {\n      deceased\n      deceasedDate\n      age\n      birthplace {\n        countryCode\n        country\n        city\n        state\n        stateCode\n      }\n      born\n      bornAccessibilityText\n      degree\n      careerEarnings\n      family\n      graduationYear\n      heightImperial\n      heightImperialAccessibilityText\n      heightMeters\n      overview\n      personal\n      playsFrom {\n        city\n        country\n        countryCode\n        state\n        stateCode\n      }\n      pronunciation\n      residence {\n        city\n        country\n        state\n        countryCode\n        stateCode\n      }\n      school\n      social {\n        type\n        url\n      }\n      turnedPro\n      weightImperial\n      weightKilograms\n      websiteURL\n      exemptions {\n        tour\n        description\n        expirationDate\n      }\n    }\n    rank {\n      rank\n      statName\n    }\n    owgr\n  }\n}"
    }
    
    response = requests.post(url, headers=headers, json=payload)
    return response.json()
        
def get_player_history(player_id, tour_code, year):
    url = 'https://orchestrator.pgatour.com/graphql'
    
    headers = {
        'x-api-key': API_KEY,
    }

    payload = {
        "operationName": "PlayerProfileSeasonResults",
        "variables": {
            "playerId": player_id,
            "tourCode": tour_code,
            "year": year
        },
        "query": "query PlayerProfileSeasonResults($playerId: ID!, $tourCode: TourCode, $year: Int) {\n  playerProfileSeasonResults(\n    playerId: $playerId\n    tourCode: $tourCode\n    year: $year\n  ) {\n    playerId\n    tour\n    displayYear\n    year\n    events\n    wins\n    top10\n    top25\n    cutsMade\n    missedCuts\n    withdrew\n    runnerUp\n    seasonPills {\n      tourCode\n      years {\n        year\n        displaySeason\n      }\n    }\n    cupRank\n    cupPoints\n    cupName\n    cupLogo\n    cupLogoDark\n    cupLogoAccessibilityText\n    rankLogo\n    rankLogoDark\n    rankLogoAccessibilityText\n    officialMoney\n    tournaments {\n      linkable\n      tournamentId\n      tournamentEndDate\n      tournamentName\n      finishPosition\n      r1\n      r2\n      r3\n      r4\n      r5\n      total\n      toPar\n      pointsRank\n      points\n      money\n      tourcastURL\n      tourcastURLWeb\n      linkable\n      fedexFallRank\n      fedexFallPoints\n      courseName\n      courseId\n    }\n    seasonRecap {\n      tourCode\n      displayMostRecentSeason\n      mostRecentRecapYear\n      items {\n        year\n        displaySeason\n        items {\n          tournamentId\n          year\n          title\n          body\n        }\n      }\n    }\n    amateurHighlights\n    tourcastEligible\n    secondaryCup {\n      cupRank\n      cupPoints\n      cupName\n      cupLogo\n      cupLogoDark\n      cupLogoAccessibilityText\n      rankLogo\n      rankLogoDark\n      rankLogoAccessibilityText\n    }\n  }\n}"
    }

    response = requests.post(url, headers=headers, json=payload)
    return response.json()
    
def get_all_player_tournaments(player_id):
    tours_and_years = get_player_history(player_id,None,None)["data"]["playerProfileSeasonResults"]["seasonPills"]
    for t in tours_and_years:
        tour_code = t["tourCode"]
        for y in t["years"]:
            year = y["year"]
            results = get_player_history(player_id, tour_code, year)
            for tournament in results["data"]["playerProfileSeasonResults"]["tournaments"]:
                yield tournament["tournamentId"]
    
def get_all_tournaments_DEPRECATED():
    #iterate through list of all players to find all tournaments they've participated in
    all_players = list(get_all_players())
    all_tournaments = set()

    print(len(all_players))

    last_player_found = False
    last_player_id = None
    if os.path.exists("output.txt"):
        with open("output.txt") as f_in:
            data = f_in.read()
            last_player_id = data.split("|")[0]
            all_tournaments = set(data.split("|")[1].split(","))
        
    for player_id in all_players:
        if player_id == last_player_id:
            lastPlayerFound = True
        if last_player_id and not last_player_found:
            continue
        tourns = get_all_player_tournaments(player_id)
        all_tournaments.update(tourns)
        print(time.time())
        print(player_id)
        print(len(all_tournaments))
        with open("output.txt", "w") as f_out:
            f_out.write("|".join([player_id, ",".join(list(all_tournaments))]))

def get_tournament_past_results(tournamentId, year):
    url = 'https://orchestrator.pgatour.com/graphql'

    headers = {
        'x-api-key': API_KEY,
    }

    payload = {
        "operationName": "TournamentPastResults",
        "variables": {
            "tournamentPastResultsId": tournamentId,
            "year": year
        },
        "query": "query TournamentPastResults($tournamentPastResultsId: ID!, $year: Int) {\n  tournamentPastResults(id: $tournamentPastResultsId, year: $year) {\n    id\n    players {\n      id\n      position\n      player {\n        id\n        firstName\n        lastName\n        shortName\n        displayName\n        abbreviations\n        abbreviationsAccessibilityText\n        amateur\n        country\n        countryFlag\n        lineColor\n        seed\n        status\n        tourBound\n        assets {\n          ... on TourBoundAsset {\n            tourBoundLogo\n            tourBoundLogoDark\n          }\n        }\n      }\n      rounds {\n        score\n        parRelativeScore\n      }\n      additionalData\n      total\n      parRelativeScore\n    }\n    teams {\n      teamId\n      position\n      players {\n        id\n        firstName\n        lastName\n        shortName\n        displayName\n        abbreviations\n        abbreviationsAccessibilityText\n        amateur\n        country\n        countryFlag\n        lineColor\n        seed\n        status\n        tourBound\n        assets {\n          ... on TourBoundAsset {\n            tourBoundLogo\n            tourBoundLogoDark\n          }\n        }\n      }\n      additionalData\n      total\n      parRelativeScore\n      rounds {\n        score\n        parRelativeScore\n      }\n    }\n    rounds\n    additionalDataHeaders\n    availableSeasons {\n      year\n      displaySeason\n    }\n    winner {\n      id\n      firstName\n      lastName\n      totalStrokes\n      totalScore\n      countryFlag\n      countryName\n      purse\n      displayPoints\n      displayPurse\n      points\n      seed\n      pointsLabel\n      winnerIcon {\n        type\n        title\n        label\n        color\n      }\n    }\n    winningTeam {\n      id\n      firstName\n      lastName\n      totalStrokes\n      totalScore\n      countryFlag\n      countryName\n      purse\n      displayPoints\n      displayPurse\n      points\n      seed\n      pointsLabel\n      winnerIcon {\n        type\n        title\n        label\n        color\n      }\n    }\n    recap {\n      weather {\n        day\n        text\n      }\n      notes\n    }\n  }\n}"
    }

    response = requests.post(url, headers=headers, json=payload)
    return response.json()

def get_tournament_results(tournamentId):
    return get_tournament_past_results(tournamentId, None)
            
def get_tournament_results_by_year(tournamentId, year):
    results = get_tournament_past_results(tournamentId, year)
    for player in results["data"]["tournamentPastResults"]["players"]:
        player_map = {
            "05134": "01219",
            "59681": "66282",
        }
        player_id = player["player"]["id"]
        player_id = player_map.get(player_id, player_id)
            
        for i,rnd in enumerate(player["rounds"]):
            if rnd["score"] == "-": continue

            yield {
                "player_id": player_id,
                "player_name": player["player"]["displayName"],
                "position": player["position"],
                "round": f"r{i+1}",
                "score": rnd["score"],
            }

def get_tournament_details(tournament_id):
    url = 'https://orchestrator.pgatour.com/graphql'

    headers = {
        'x-api-key': API_KEY,
    }

    payload = {
        "operationName": "Tournaments",
        "variables": {
            "ids": [tournament_id]
        },
        "query": "query Tournaments($ids: [ID!]) {\n  tournaments(ids: $ids) {\n    ...TournamentFragment\n  }\n}\n\nfragment TournamentFragment on Tournament {\n  id\n  tournamentName\n  tournamentLogo\n  tournamentLocation\n  tournamentStatus\n  roundStatusDisplay\n  roundDisplay\n  roundStatus\n  roundStatusColor\n  currentRound\n  timezone\n  pdfUrl\n  seasonYear\n  displayDate\n  country\n  state\n  city\n  scoredLevel\n  infoPath\n  events {\n    id\n    eventName\n    leaderboardId\n  }\n  courses {\n    id\n    courseName\n    courseCode\n    hostCourse\n    scoringLevel\n  }\n  weather {\n    logo\n    logoDark\n    logoAccessibility\n    tempF\n    tempC\n    condition\n    windDirection\n    windSpeedMPH\n    windSpeedKPH\n    precipitation\n    humidity\n    logoAsset {\n      imageOrg\n      imagePath\n    }\n    logoDarkAsset {\n      imageOrg\n      imagePath\n    }\n  }\n  ticketsURL\n  tournamentSiteURL\n  formatType\n  features\n  conductedByLabel\n  conductedByLink\n  beautyImage\n  hideRolexClock\n  hideSov\n  headshotBaseUrl\n  rightRailConfig {\n    imageUrl\n    imageAltText\n    buttonLink\n    buttonText\n  }\n  shouldSubscribe\n  ticketsEnabled\n  useTournamentSiteURL\n  beautyImageAsset {\n    imageOrg\n    imagePath\n  }\n  disabledScorecardTabs\n  leaderboardTakeover\n  tournamentCategoryInfo {\n    type\n    logoLight\n    logoLightAsset {\n      imageOrg\n      imagePath\n    }\n    logoDark\n    logoDarkAsset {\n      imageOrg\n      imagePath\n    }\n    label\n  }\n  tournamentLogoAsset {\n    imageOrg\n    imagePath\n  }\n}"
    }

    response = requests.post(url, headers=headers, json=payload)

    if not len(response.json()["data"]["tournaments"]):
        return {}
    
    tournament_info = response.json()["data"]["tournaments"][0]
    return {
        "id": tournament_info["id"],
        "name": tournament_info["tournamentName"],
        "date": tournament_info["displayDate"],
        "course_id": "|".join([x["id"] for x in tournament_info["courses"]]),
        "course_name": "|".join([x["courseName"] for x in tournament_info["courses"]]),
    }

def get_full_tournament_history_DEPRECATED(tournament_id):
    details = get_tournament_details("R2020003") #tournament_id)
    print(details)
    
    #19840
    # results = get_tournament_results_by_year("R1993018","19380")
    results = get_tournament_results_by_year("R2015018","20150")
    print(results)
    raise
    # results = get_tournament_results_by_year("R2012016",2011)
    # print(results)
    pass
    
    results = get_tournament_results(tournament_id, None)
    all_years = [x["year"] for x in results["data"]["tournamentPastResults"]["availableSeasons"]]
    print(all_years)
    for year in all_years:
        results = get_tournament_results_by_year(tournament_id, year)
        print(results)
        raise


    
def player_tournament_results(player_id):
    print(player_id)
    history = get_player_history(player_id,None,None)
    if not history["data"]: return #rare errors
    tours_and_years = history["data"]["playerProfileSeasonResults"]["seasonPills"]
    for t in tours_and_years:
        tour_code = t["tourCode"]
        for y in t["years"]:
            year = y["year"]
            results = get_player_history(player_id, tour_code, year)
            tournaments = results["data"]["playerProfileSeasonResults"]["tournaments"]
            for tourn in tournaments:
                info = {
                    "year": year,
                    "tour_code": tour_code,
                    "tournament_id": tourn["tournamentId"],
                    "tournament_name": tourn["tournamentName"],
                    "date": tourn["tournamentEndDate"],
                    "course_name": tourn["courseName"],
                    "course_id": tourn["courseId"],
                    "position": tourn["finishPosition"],
                }
                for key in tourn:
                    if re.findall("^r\d+$",key) and tourn[key] != "-":
                        yield {
                            "round": key,
                            "score": tourn[key],
                            **info
                        }

def hidden_player_results():
    reader = csv.DictReader(open("results_tournament_history.csv"))
    new_players = {}
    for r in reader:
        new_players[r["player_id"]] = {"player_id": r["player_id"], "player_name": r["player_name"]}

    reader = csv.DictReader(open("results_tournament_leaderboard.csv"))
    for r in reader:
        new_players[r["player_id"]] = {"player_id": r["player_id"], "player_name": r["player_name"]}
    
    writer = csv.DictWriter(open("results_hidden_players.csv","w"), fieldnames = RESULTS_FIELD_NAMES)
    writer.writeheader()
    
    get_player_results(new_players.values(), writer, [])
                        
def all_player_results():
    reader = csv.DictReader(open("results_player_history.csv"))
    completed_players = set([row["player_id"] for row in reader])

    writer = csv.DictWriter(open("results_player_history.csv","a"),fieldnames = RESULTS_FIELD_NAMES)
    #writer.writeheader()
    get_player_results(get_all_players(), writer, completed_players)

def get_player_results(all_players, writer, completed_players = []):
    for player in all_players:
        if player["player_id"] in completed_players:
            continue
        for result in player_tournament_results(player["player_id"]):
            writer.writerow({
                **player,
                **result
            })
            
def get_leaderboard_results(tournament_id):
    url = 'https://orchestrator.pgatour.com/graphql'
    
    headers = {
        'x-api-key': API_KEY,
    }

    payload = {
        "operationName": "LeaderboardCompressedV3",
        "variables": {
            "leaderboardCompressedV3Id": tournament_id
        },
        "query": "query LeaderboardCompressedV3($leaderboardCompressedV3Id: ID!) {\n  leaderboardCompressedV3(id: $leaderboardCompressedV3Id) {\n    id\n    payload\n  }\n}"
    }

    response = requests.post(url, headers=headers, json=payload)
    if not response.json()["data"]:
        return
    payload = response.json()["data"]["leaderboardCompressedV3"]["payload"]
    data = json.loads(gzip.decompress(base64.b64decode(payload)))
    for player in data["players"]:
        if player["__typename"] == "InformationRow": continue
        for i,score in enumerate(player["scoringData"]["rounds"]):
            if score == "-": continue
            yield {
                "player_id": player["player"]["id"],
                "player_name": player["player"]["displayName"],
                "position": player["scoringData"]["position"],
                "round": f"r{i+1}",
                "score": score,
            }


def load_tournament_to_results():
    tournaments = {}
    reader = csv.DictReader(open("results_player_history.csv"))
    for r in reader:
        tournaments.setdefault(r["tournament_id"],[]).append(r)

    return tournaments
    
def calculate_tournament_hashes():
    tournaments = load_tournament_to_results()

    writer = csv.DictWriter(open("tournament_hashes.csv","w"), fieldnames = ["tournament","hash"])
    writer.writeheader()
    for t in tournaments:
        print(t)
        results = get_tournament_results(t, None)
        top_5 = [x["id"] for x in results["data"]["tournamentPastResults"]["players"][:5]]
        seasons = len(results["data"]["tournamentPastResults"]["availableSeasons"])
        hash_ = str(seasons) + "|" + ",".join(top_5)

        #for some reason some tournaments are pulling different results for the Zurich Classic
        #force map them to the same investment
        if hash_ == "76|":
            hash_ = "76|51997,54591,52453,52686,47420"
            
        writer.writerow({
            "tournament": t,
            "hash": hash_,
        })
    
def hash_year_to_tournament(hash_to_run = None):
    tournaments = load_tournament_to_results()
        
    reader = csv.DictReader(open("tournament_hashes.csv"))
    hash_to_tournaments = {}
    for r in reader:
        hash_to_tournaments.setdefault(r["hash"],[]).append(r["tournament"])

    writer = csv.DictWriter(open("hash_year_tournament.csv","w"), fieldnames = ["hash","year","tournament"])
    writer.writeheader()
    
    for hash_ in hash_to_tournaments:
        if hash_to_run and hash_ != hash_to_run: continue
        if hash_ == "0|": continue
        siblings = hash_to_tournaments[hash_]
        matched_siblings = []
        print(hash_, siblings)
        test_tourn = siblings[0]
        all_seasons = get_tournament_results(test_tourn, None)["data"]["tournamentPastResults"]["availableSeasons"]

        for season in all_seasons:
            year = season["year"]
            results = get_tournament_results_by_year(test_tourn, year)

            #find sibling tournament
            found = False
            for tourn in sorted(siblings, key = lambda x: -1*(x[1:5]+"0" == str(year))):
                existing_rows = tournaments[tourn]
                match = True
                for r in existing_rows:
                    position = r["position"].replace("P","") #think this is playoff related
                    player_matches = [p for p in results if p["id"] == r["player_id"]]
                    if not len(player_matches):
                        if tourn[1:5] == str(year)[:-1]:
                            print(str(year), r, player_matches)
                        match = False
                        break

                    if position != player_matches[0]["position"]:
                        if tourn[1:5] == str(year)[:-1]:
                            print(str(year), r, player_matches[0])
                        match = False
                        break

                    #more informational, usually the player level data is better here
                    round_matches = [p for p in player_matches if p["round"] == r["round"]]
                    
                    if not round_matches:
                        if tourn[1:5] == str(year)[:-1]:
                            # print("missing round", r, player_matches[0])
                            pass
                    else:
                        score = round_matches[0]["score"]
                        if score != r["score"]:
                            if tourn[1:5] == str(year)[:-1]:
                                # print("score mismatch", r, score)
                                pass

                if match == True:
                    found = True
                    print("match", hash_, year, tourn)
                    writer.writerow({
                        "hash": hash_,
                        "year": year,
                        "tournament": tourn
                    })
                    matched_siblings.append(tourn)
                    break
            if found == False:
                print("no match", hash_, year)
                writer.writerow({
                    "hash": hash_,
                    "year": year,
                    "tournament": ""
                })
        for t in siblings:
            if t not in matched_siblings:
                print("unmatched", t)
                writer.writerow({
                    "hash": hash_,
                    "year": "",
                    "tournament": t
                })
                
def all_tournament_leaderboards():
    tournaments = {}
    reader = csv.DictReader(open("results_player_history.csv"))
    for r in reader:
        tournaments.setdefault(r["tournament_id"],[]).append(r)

    writer = csv.DictWriter(open("results_tournament_leaderboard.csv","w"), fieldnames = RESULTS_FIELD_NAMES)
    writer.writeheader()
    
    for t in sorted(tournaments, key = lambda x: x[1:5], reverse=True):
        print(t)
        info = {
            "year": tournaments[t][0]["year"],
            "tour_code": tournaments[t][0]["tour_code"],
            "tournament_id": t,
            "tournament_name": tournaments[t][0]["tournament_name"],
            "date": tournaments[t][0]["date"],
            "course_name": tournaments[t][0]["course_name"],
            "course_id": tournaments[t][0]["course_id"],
        }
        for result in get_leaderboard_results(t):
            prior_results = [x for x in tournaments[t] if x["player_id"] == result["player_id"] and x["round"] == result["round"]]
            if not prior_results:
                writer.writerow({
                    **info,
                    **result,
                })
                
def all_tournament_history():
    tournaments = {}
    reader = csv.DictReader(open("results_player_history.csv"))
    for r in reader:
        tournaments.setdefault(r["tournament_id"],[]).append(r)

    reader = csv.DictReader(open("tournament_hashes.csv"))
    hash_to_tournaments = {}
    for r in reader:
        hash_to_tournaments.setdefault(r["hash"],[]).append(r["tournament"])

    writer = csv.DictWriter(open("results_tournament_history.csv","w"),fieldnames=RESULTS_FIELD_NAMES)
    writer.writeheader()
        
    reader = csv.DictReader(open("hash_year_tournament.csv"))
    for row in reader:
        if not row["year"]: continue

        if row["tournament"]:
            t = row["tournament"]
        else:
            t = hash_to_tournaments[row["hash"]][0]

        if row["tournament"]:
            tourn_info = {
                "year": tournaments[t][0]["year"],
                "tour_code": tournaments[t][0]["tour_code"],
                "tournament_id": t,
                "tournament_name": tournaments[t][0]["tournament_name"],
                "course_id": tournaments[t][0]["course_id"],
                "course_name": tournaments[t][0]["course_name"],
                "date": tournaments[t][0]["date"],
            }
        else:
            year = row["year"][:4]
            tourn_info = {
                "year": year,
                "tour_code": tournaments[t][0]["tour_code"],
                "tournament_id": t[0] + year + t[5:] + "s",
                "tournament_name": tournaments[t][0]["tournament_name"],
                "course_id": "",
                "course_name": "",
                "date": f'1.1.{row["year"][:4]}', #Jan 1 placeholder
            }
            print(tourn_info)

        for result in get_tournament_results_by_year(t, row["year"]):
            prior_results = [x for x in tournaments[t] if x["player_id"] == result["player_id"] and x["round"] == result["round"]]
            if not prior_results:
                writer.writerow({
                    **tourn_info,
                    **result
                })
            
        
    
def all_tournament_results():
    tournaments = {}
    reader = csv.DictReader(open("results_player_history.csv"))
    for r in reader:
        tournaments.setdefault(r["tournament_id"],[]).append(r)

    tournament_to_key = {}
    key_to_tournaments = {}
    key_year_to_id = {}

    keywriter = csv.DictWriter(open("keys.csv","w"), fieldnames = ["tournament","base_key"])
    keywriter.writeheader()
    for t in tournaments:
        print(t)
        results = get_tournament_results(t, None)
        top_5 = [x["id"] for x in results["data"]["tournamentPastResults"]["players"][:5]]
        seasons = len(results["data"]["tournamentPastResults"]["availableSeasons"])
        base_key = str(seasons) + "|" + ",".join(top_5)
        keywriter.writerow({
            "tournament": t,
            "base_key": base_key,
        })
        
        tournament_to_key[t] = base_key
        key_to_tournaments.setdefault(base_key,[]).append(t)

                # if match and len(existing_rows):
                #     print(base_key, year, tourn)

        
def deprecated():
    #believe not needed, pull from the player results instead of the tournament results?
    with open("output.txt") as f_in:
        data = f_in.read()
        lastPlayerId = data.split("|")[0]
        all_tournaments = set(data.split("|")[1].split(","))

    key_to_tournaments = {}
    for tournament_id in all_tournaments:
        #if tournament_id[0] + tournament_id[5:] != "R050": continue
        print(tournament_id)
        details = get_tournament_details(tournament_id)
        results = get_tournament_results(tournament_id,None)
        seasons = len(results["data"]["tournamentPastResults"]["availableSeasons"])
        podium = [x["id"] for x in results["data"]["tournamentPastResults"]["players"][:3]]
        key = str(seasons) + "|" + ",".join(podium)
        if not details and key == "0|":
            print(key)
            print(results)
            raise
    raise

    for key in key_to_tournaments:
        editions = sorted(key_to_tournaments[key], key=lambda x: x[1:5], reverse=True)
        print(editions)
        for tournament_id in editions:
            winner = results["data"]["tournamentPastResults"]["winner"]

            print(podium)
            raise
            
            print(results["data"]["tournamentPastResults"]["winner"].keys())
            raise
            if details:
                print(details)
            else:
                print(tournament_id[1:5])
        raise

def aggregate_results():
    all_results = {}
    
    for filename in ["results_player_history.csv","results_tournament_history.csv","results_tournament_leaderboard.csv","results_hidden_players.csv"]:
        reader = csv.DictReader(open(filename))
        for row in reader:
            key = "|".join([row["player_id"],row["position"],row["tournament_id"],row["round"]])
            if not key in all_results:
                all_results[key] = row

    writer = csv.DictWriter(open("pga.csv","w"), fieldnames = RESULTS_FIELD_NAMES)
    writer.writeheader()
    for r in all_results.values():
        writer.writerow(r)
    
if __name__ == "__main__":
    #NOTE: the pgatour site is complicated and inconsistent
    #results are stored both on the player's history and on the tournament's history
    #but those two records don't always match(!)
    #seems the player history is more reliable
    #there are also tournaments that seem only accessible from the player history
    #and players who are only accessible through tournament history

    #taking the player history as baseline
    #pull the list of all players and their results
    #needs 10-20 hours to run:
    #all_player_results()

    #there are two ways to pull tournament history:
    #through the "past results" tab on the tournament page
    #and through the tournament leaderboard call

    #first work on the "past results" tab
    #these are reached by visiting any year's edition of a tournament
    #and then specifying a year with an extra 0 or 1 at the end: eg "20080"
    #do the below work to map these historical years to existing tournament ids
    #calculate_tournament_hashes()
    #hash_year_to_tournament()

    #now for each tournament we can pull via the "past results" tab
    #or directly through the leaderboard call and see how data compares
    #with the player history data
    #all_tournament_leaderboards()
    #all_tournament_history()

    #this new tournament data uncovers some new players we didn't have 
    #previously, write their data
    #hidden_player_results()

    aggregate_results()

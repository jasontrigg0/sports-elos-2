import requests
import time
import os
import re
import csv
import base64
import gzip
import json
import datetime

#NOTE: not a secret
#this is set normally when browsing the pgatour.com site
API_KEY = 'da2-gsrx5bibzbb4njvhl7t37wqyl4' 

RESULTS_FIELD_NAMES = ["year", "tour_code", "tournament_id", "tournament_name", "course_id", "course_name", "date", "player_id", "player_name", "position", "round", "score"]

def get_tour_players():
    #note: this doesn't include all players, think better to just iterate through all ids
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


def get_schedule(tour_code, year):
    url = 'https://orchestrator.pgatour.com/graphql'

    headers = {
        'x-api-key': API_KEY,
    }

    payload = {
        "operationName":"Schedule",
        "variables": {
            "year": year,
            "tourCode": tour_code,
        },
        "query": "query Schedule($tourCode: String!, $year: String, $filter: TournamentCategory) {\n  schedule(tourCode: $tourCode, year: $year, filter: $filter) {\n    completed {\n      month\n      year\n      monthSort\n      ...ScheduleTournament\n    }\n    filters {\n      type\n      name\n    }\n    seasonYear\n    tour\n    upcoming {\n      month\n      year\n      monthSort\n      ...ScheduleTournament\n    }\n  }\n}\n\nfragment ScheduleTournament on ScheduleMonth {\n  tournaments {\n    tournamentName\n    id\n    beautyImage\n    champion\n    champions {\n      displayName\n      playerId\n    }\n    championEarnings\n    championId\n    city\n    country\n    countryCode\n    courseName\n    date\n    dateAccessibilityText\n    purse\n    sortDate\n    startDate\n    state\n    stateCode\n    status {\n      roundDisplay\n      roundStatus\n      roundStatusColor\n      roundStatusDisplay\n    }\n    tournamentStatus\n    ticketsURL\n    tourStandingHeading\n    tourStandingValue\n    tournamentLogo\n    display\n    sequenceNumber\n    tournamentCategoryInfo {\n      type\n      logoLight\n      logoDark\n      label\n    }\n    tournamentSiteURL\n    tournamentStatus\n    useTournamentSiteURL\n  }\n}"
    }

    response = requests.post(url, headers=headers, json=payload)
    return response.json()

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

    display_date = tournament_info["displayDate"]

    #different formats depending on whether the tournament runs past month-end:
    #May 25-28, 2025
    #May 31-Jun 3, 2025
    year_str = display_date.split(",")[1].strip()
    
    post_hyphen = display_date.split(",")[0].split("-")[1].strip()
    if re.findall("[a-z]",post_hyphen):
        month_str = post_hyphen.split()[0]
        day_str = post_hyphen.split()[1]
    else:
        month_str = display_date.split()[0]
        day_str = display_date.split(",")[0].split("-")[1].strip()

    month_num = datetime.datetime.strptime(month_str, '%b').month

    return {
        "tournament_id": tournament_info["id"],
        "tournament_name": tournament_info["tournamentName"],
        "course_id": "|".join([x["id"] for x in tournament_info["courses"]]),
        "course_name": "|".join([x["courseName"] for x in tournament_info["courses"]]),
        "date": f"{month_num}.{day_str}.{year_str}",
    }

def player_tournament_results(player_id):
    print(player_id)
    history = get_player_history(player_id,None,None)
    if not history["data"]: return #rare errors
    tours_and_years = history["data"]["playerProfileSeasonResults"]["seasonPills"]
    for t in tours_and_years:
        tour_code = t["tourCode"]
        for y in t["years"]:
            results = get_player_history(player_id, tour_code, y["year"])
            tournaments = results["data"]["playerProfileSeasonResults"]["tournaments"]
            for tourn in tournaments:
                info = {
                    "year": y["year"],
                    "tour_code": tour_code,
                    "tournament_id": tourn["tournamentId"],
                    "tournament_name": tourn["tournamentName"],
                    "date": tourn["tournamentEndDate"],
                    "course_name": tourn["courseName"],
                    "course_id": tourn["courseId"],
                    "position": tourn["finishPosition"],
                }
                for key in tourn:
                    if re.findall(r"^r\d+$",key) and tourn[key] != "-":
                        yield {
                            "round": key,
                            "score": tourn[key],
                            **info
                        }

def all_player_history():
    filename = "../data/pga/test.csv"

    if os.path.exists(filename):
        reader = csv.DictReader(open(filename))
        completed_players = set([row["player_id"] for row in reader])
        writer = csv.DictWriter(open(filename,"a"),fieldnames = RESULTS_FIELD_NAMES)
    else:
        completed_players = []
        writer = csv.DictWriter(open(filename,"w"),fieldnames = RESULTS_FIELD_NAMES)
        writer.writeheader()

    # for i in range(68380,100000): #current max around 70000
    for i in range(2000,100000): #current max around 70000
        player_id = str(i).zfill(5)
        if player_id in completed_players:
            continue
        player_info = get_player(player_id)
        if not player_info["data"]: continue
        
        for result in player_tournament_results(player_id):
            writer.writerow({
                "player_id": player_info["data"]["player"]["id"],
                "player_name": player_info["data"]["player"]["displayName"],
                **result
            })

def scrape_year(year):
    writer = csv.DictWriter(open(f"../data/pga/pga_{year}.csv","w"),fieldnames = RESULTS_FIELD_NAMES)
    writer.writeheader()
    
    for tour_code in "ICHMRSUY":
        res = get_schedule(tour_code, year)
        if not res["data"]: continue
        schedule = res["data"]["schedule"]
        tournament_ids = [x["id"] for month in schedule["completed"] for x in month["tournaments"]] + [x["id"] for month in schedule["upcoming"] for x in month["tournaments"]]

        # print(tournament_ids)
        # continue
        
        for tournament in tournament_ids:
            print(tournament)
            details = get_tournament_details(tournament)
            for result in get_leaderboard_results(tournament):
                writer.writerow({
                    "year": year,
                    "tour_code": tour_code,
                    **details,
                    **result
                })
    
            
if __name__ == "__main__":
    #NOTE: the pgatour site is complicated and inconsistent
    #can pull results by player or by tournament
    #but those two records don't always match(!)
    #seems the player history is generally more reliable
    #pulling by tournament includes some non-standard tournaments (eg teams or nonstandard scoring)
    #along with some qualifying tournaments that don't show up in the player history
    #on the other hand the tournaments are missing a few player results (is it players who missed the cut only?)
    #strategy: run the full player history for every player (10-30 hours or so)
    #when refreshing the current year pull by tournament

    #all_player_history()
    scrape_year(2025)


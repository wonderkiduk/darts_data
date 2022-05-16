import requests
import csv
import pandas as pd
import datetime
from os import path
# Data only goes back to november 17th. No data on nov 17th on 16th may

data_path = './data'

def get_tournaments_from_date(date):
    # Date format yyyy-MM-dd
    req = requests.get(f'https://widgets.fn.sportradar.com/pdcsrcardiff/en/Etc:UTC/gismo/sport_matches/22/{date}')
    real_categories = req.json().get('doc')[0].get('data').get('sport').get('realcategories')
    if real_categories == []:
        print(f'No tournaments on {date}.')
        return None
    tournaments = real_categories[0].get('tournaments')
    print(f"Tournaments on {date}: {', '.join(get_names_from_tournaments(tournaments))}")
    return tournaments

def get_names_from_tournaments(tournaments):
    if tournaments is None:
        return
    return [t.get('name') for t in tournaments]

def get_match_ids_from_tournament(tournament):
    tournament_matches = tournament.get('matches')
    matches = []
    for match in tournament_matches:
        matches.append(match.get('_id'))
    return matches

def get_relevant_rows_from_event(event):
    relevant_keys = ['team', 'points', 'segment', 'event_points', 'double_attempt']
    row = {}
    for k in relevant_keys:
        row[k] = event.get(k)
    return row

def get_info_from_match_id(match_id):
    req = requests.get(f'https://lmt.fn.sportradar.com/pdcsrcardiff/en/Etc:UTC/gismo/match_timeline/{match_id}')
    teams = req.json().get('doc')[0].get('data').get('match').get('teams')
    home_name = convert_to_camel_case(teams.get('home').get('name'))
    away_name = convert_to_camel_case(teams.get('away').get('name'))
    out_dict = {
        'home': home_name,
        'away': away_name
    }
    return out_dict 

def get_dart_throws_from_match_id(match_id):
    req = requests.get(f'https://lmt.fn.sportradar.com/pdcsrcardiff/en/Etc:UTC/gismo/match_timeline/{match_id}')
    events = req.json().get('doc')[0].get('data').get('events')
    all_dart_throws = []
    status = req.json().get('doc')[0].get('data').get('match').get('status').get('name')
    if status in ['Cancelled', 'Walkover']:
        print(f'No darts thrown for match {match_id}. Status: {status}')
        return None
    for event in events:
        if event.get('type') == 'single_throw_dart':
            all_dart_throws.append(get_relevant_rows_from_event(event))
    return(all_dart_throws)

def get_csv_of_match(match_id, tournament_name=None):
    print(f'Getting csv for match id {match_id}')
    all_throws = get_dart_throws_from_match_id(match_id)
    if all_throws is None:
        return 
    
    info = get_info_from_match_id(match_id)
    csv_keys = all_throws[0].keys()
    tournament_name = f"{convert_to_camel_case(tournament_name)}_"
    filename = f"{tournament_name}{info['home']}_v_{info['away']}.csv"
    with open(path.join(data_path, filename), 'w') as f:
        dict_writer = csv.DictWriter(f, csv_keys)
        dict_writer.writeheader()
        dict_writer.writerows(all_throws)

def convert_to_camel_case(s):
    return s.lower().replace(' ', '_')

def get_all_matches_from_tournament(tournament, tournament_name):
    print(f'Getting all matches from {tournament_name}.')
    match_ids = get_match_ids_from_tournament(tournament)
    for match_id in match_ids:
        get_csv_of_match(match_id, tournament_name)

def get_csv_of_all_matches_from_specific_day(date, specific_tournaments=None):
    print(f'Getting all matches from {date}.')
    tournaments = get_tournaments_from_date(date)
    named_tournaments = get_names_from_tournaments(tournaments)
    if tournaments is None:
        return

    if all(specific_tournament not in named_tournaments for specific_tournament in specific_tournaments):
        print(f"{','.join(specific_tournaments)} did not occur on 2022-05-15.")
        return
        
    for tournament in tournaments:
        tournament_name = tournament.get('name')
        # print(tournament_name)
        if specific_tournaments and tournament_name in specific_tournaments:
            get_all_matches_from_tournament(tournament, tournament_name)
        elif specific_tournaments is None:
            get_all_matches_from_tournament(tournament, tournament_name)

def get_valid_dates(start_date, end_date):
    start_date = pd.to_datetime(start_date)
    end_date = pd.to_datetime(end_date)
    today = pd.to_datetime(datetime.date.today())
    if start_date > end_date:
        print('Please enter an end date after the start date.')
        return None, today
    if start_date > today:
        print('Please enter a start date before today.')
        return None, today
    if end_date > today:
        end_date = today
    return start_date, end_date

def get_matches_from_range_of_dates(start_date, end_date, specific_tournaments=None):
    start_date, end_date = get_valid_dates(start_date, end_date)
    if start_date is None:
        return
    dr = pd.date_range(start=start_date, end=end_date)
    
    for date in dr:
        date = date.strftime('%Y-%m-%d')
        get_csv_of_all_matches_from_specific_day(date, specific_tournaments)

def get_tournaments_from_range_of_dates(start_date, end_date):
    start_date, end_date = get_valid_dates(start_date, end_date)
    if start_date is None:
        return
    dr = pd.date_range(start=start_date, end=end_date)
    tournaments = []
    for date in dr:
        date = date.strftime('%Y-%m-%d')
        tournaments_on_date = get_tournaments_from_date(date)
        if tournaments_on_date is not None:
            tournaments += get_names_from_tournaments(tournaments_on_date)
    return tournaments

# get_tournaments_from_range_of_dates('2022-05-15', '2022-05-16')
# get_csv_of_all_matches_from_specific_day('2021-12-29', specific_tournaments=['PDC World Championship 2022'])
get_matches_from_range_of_dates('2021-12-15', '2022-01-03', specific_tournaments=['PDC World Championship 2022'])

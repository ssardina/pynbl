import os
import datetime
import json
import pandas as pd
from urllib.request import urlopen


from config import *

def get_json_data(game_id: int) :
    """Load a game into a JSON object. 
        Data will be loaded from local file data-{game_id}.json if exists
        Otherwise will be fetched from server

    Args:
        game_id (int): id of the game

    Returns:
        json-object: An object with JSON structure dict/list
    """
    game_file = f"data-{game_id}.json"
    game_url = os.path.join(URL_LIVESTATS, str(game_id), "data.json")

    if os.path.exists(game_file):
        data_json = json.load(open(f'data-{game_id}.json'))
        print(f"Game data loaded from local file: {game_file}")
    else:   # get if from URL
        # store the response of URL
        response = urlopen(game_url)

        # storing the JSON response 
        # from url in data
        data_json = json.loads(response.read())
        print(f"Game data loaded from URL: {game_url}")

    return data_json

def get_team_names(data_json):
    """Extra team names from JSON game

    Args:
        data_json (json-object): JSON live data of a game

    Returns:
        list(tuple(string, string)): full and short names of both teams
    """
    name_1 = data_json['tm']['1']['name']
    name_2 = data_json['tm']['2']['name']
    short_name_1 = data_json['tm']['1']['shortName']
    short_name_2 = data_json['tm']['2']['shortName']

    return [(name_1, short_name_1), (name_2, short_name_2)]

# https://pandas.pydata.org/docs/reference/api/pandas.json_normalize.html
def get_game_players(game_json, tm):
    """Extract general players info of a JSON live game data for a team

    Args:
        game_json (json-object): live JSON data of a game
        tm (int: 1 or 2): the team number to extract the players' info

    Returns:
        json-object: a json object containing the players' general data
    """
    return pd.json_normalize(game_json['tm'][str(tm)]['pl'].values())

def get_stints(game_json, team_no: set):

    pbp_df = get_pbp_df(game_json)

    stints = {}
    current_team = set.union(*[get_starters(game_json, n) for n in team_no])
    current_team = frozenset(current_team)
    # print(f"Starter team: {current_team}")
    for period in range(1, 5):
        prev_clock = datetime.time.fromisoformat('00:10:00.000000')
        subs = pbp_df.loc[(pbp_df['actionType'] == 'substitution') &
                            (pbp_df['tno'].isin(team_no)) &
                            (pbp_df['period'] == period)]
        for sub_clock in subs['clock'].unique(): # loo on the sub times for the team
            # interval = pd.Interval(datetime.datetime.timestamp(prev_clock), datetime.datetime.timestamp(sub_clock), closed='left')
            interval = (period, prev_clock, sub_clock)
            if current_team in stints:
                stints[current_team].append(interval)
            else:
                stints[current_team] = [interval]

            players_in = set(subs.loc[(subs['clock'] == sub_clock) &
                                    (subs['subType'] == 'in'), 'player'].tolist())
            players_out = set(subs.loc[(subs['clock'] == sub_clock) &
                                    (subs['subType'] == 'out'), 'player'].tolist())
            current_team = current_team.difference(players_out).union(players_in)

            # print(f'Subs at time {sub_clock}: {players_in} for {players_out}')
            # print(f"\t New team: {current_team}")

    return stints


# https://pandas.pydata.org/docs/reference/api/pandas.json_normalize.html
def get_starters(game_json, tm) -> set:
    """Extract the starter players of a team

    Args:
        game_json (json-object): live JSON data of a game
        tm (int: 1 or 2): the team number to extract the players' info

    Returns:
        set(string): set of starter players name
    """
    # dataframe for players of the team
    pl_df = get_game_players(game_json, tm)

    # list of starters on each team
    starters = set(pl_df.loc[pl_df['starter'] == 1, 'name'].tolist())

    return starters

def get_raw_pbp_fibalivestats(game_id: int):
    data_json = get_json_data(game_id)

    return get_pbp_df(data_json)

def get_pbp_df(data_json):
    # Extract names of teams in the game
    team_names = get_team_names(data_json)
    team_name_1, team_short_name_1 = team_names[0]
    team_name_2, team_short_name_2 = team_names[1]

    print(f"Game {team_name_1} ({team_short_name_1}) vs {team_name_2} ({team_short_name_2})")


    # extract play-by-play data
    pbp_df = pd.json_normalize(data_json, record_path =['pbp'])

    # keep columns 1 to 17, drop all player info
    pbp_df = pbp_df.iloc[:, 1:17]

    # set type of time fields
    # pbp_df['gt'] = pd.to_datetime(pbp_df['gt'], format="%M:%S").dt.time
    pbp_df['clock'] = pd.to_datetime(pbp_df['clock'], format="%M:%S:%f").dt.time

    # change period id of OT
    #TODO: why is this change to a number 5??
    #periodType == 'OVERTIME'] = 5
    pbp_df.loc[pbp_df["periodType"] == 'OVERTIME', 'periodType'] = 5

    # #add teams names

    # pbp$team_name = ''
    # pbp$team_short_name = ''
    pbp_df.insert(0, 'team_name', '')
    pbp_df.insert(1, 'team_short_name', '')
    pbp_df.loc[pbp_df['tno'] == 1, 'team_name'] = team_name_1
    pbp_df.loc[pbp_df['tno'] == 2, 'team_name'] = team_name_2
    pbp_df.loc[pbp_df['tno'] == 1, 'team_short_name'] = team_short_name_1
    pbp_df.loc[pbp_df['tno'] == 2, 'team_short_name'] = team_short_name_2

    #TODO: Do we really need to remove numbers from players names?
    # pbp_df.loc[pbp_df['player'].str.contains('\d') | pbp_df['player'].str.contains(',')]
    #
    # old R code:
    # #remove numbers from players names
    # pbp$player = gsub('[0-9]', '', pbp$player)
    # pbp$player = gsub(', ','', pbp$player)

    # sort by period and clock
    pbp_df.sort_values(by=['period', 'clock'], ascending=[True, False], inplace=True)

    #TODO: do we need these new columns?
    # pbp$firstName = NULL
    # pbp$shirtNumber = NULL

    return pbp_df

import os
import json
import pandas as pd
from urllib.request import urlopen


from config import *

def get_json_data(game_id: int) :
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

def get_team_names_json(data_json):
    name_1 = data_json['tm']['1']['name']
    name_2 = data_json['tm']['2']['name']
    short_name_1 = data_json['tm']['1']['shortName']
    short_name_2 = data_json['tm']['2']['shortName']

    return [(name_1, short_name_1), (name_2, short_name_2)]

# https://pandas.pydata.org/docs/reference/api/pandas.json_normalize.html
def get_game_players_json(game_json, tm):
    return pd.json_normalize(game_json['tm'][str(tm)]['pl'].values())



def get_raw_pbp_fibalivestats(game_id: int):
    data_json = get_json_data(game_id)

    # Extract names of teams in the game
    team_names = get_team_names_json(data_json)
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
    pbp_df.loc[pbp_df['tno'] == 1, 'team_short_name'] = team_short_name_2
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

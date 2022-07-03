import os
import datetime
import json
import pandas as pd
from urllib.request import urlopen
from functools import reduce

from config import *

percent = lambda part, whole: round(100* (part / whole), 2)

# stats_df.merge(stints1_df)s
def time_to_datetime(time : datetime.time) -> datetime.datetime:
    """Convert datetime.time to datetime.datetime

    Args:
        time (datetime.time): time to convert

    Returns:
        datetime.datetime: converted object
    """
    try:
        return pd.to_datetime(time, format='%H:%M:%S.%f')
    except:
        return pd.to_datetime(time, format='%H:%M:%S')

def intervals_to_mins(intervals: list) -> float:
    """Convert a list of game intervals into number of minutes played

    Args:
        intervals (list): list of intervals (period, time end, time start)

    Returns:
        float: number of minutes in the intervals
    """
    minutes = 0
    for i in intervals:
        minutes += (time_to_datetime(i[1]) - time_to_datetime(i[2])).seconds /  60

    return minutes


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
        # print(f"Game data loaded from local file: {game_file}")
    else:   # get if from URL
        # store the response of URL
        response = urlopen(game_url)

        # storing the JSON response 
        # from url in data
        data_json = json.loads(response.read())
        # print(f"Game data loaded from URL: {game_url}")

    return data_json
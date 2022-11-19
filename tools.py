import os
import datetime
from urllib.request import urlopen
import json  # https://docs.python.org/3/library/json.html
import pandas as pd
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


def get_json_data(game_id: int, dir='.') :
    """Load a game into a JSON object.
        Data will be loaded from local file data-{game_id}.json if exists
        Otherwise will be fetched from server

    Args:
        game_id (int): id of the game
        dir (str): folder where to check and save a copy

    Returns:
        json-object: An object with JSON structure dict/list
    """
    file_json = os.path.join(dir, f"data-{game_id}.json")
    game_url = os.path.join(URL_LIVESTATS, str(game_id), "data.json")

    if os.path.exists(file_json):
        game_json = json.load(open(file_json))
        # print(f"Game data loaded from local file: {game_file}")
    else:   # get if from URL
        # store the response of URL
        response = urlopen(game_url)

        # storing the JSON response
        # from url in data
        game_json = json.loads(response.read())

        # assume no json file if game is not yet over!
        if not game_ended(game_json):
            raise ValueError('Game has not finished yet')

        with open(file_json, 'w') as f:
            json.dump(game_json, f)
        # print(f"Game data loaded from URL: {game_url}")

    return game_json

def game_ended(game_json) -> bool:
    """
    Checks if the game has ended
    """
    return game_json['pbp'] and game_json['pbp'][0]['actionType'] == "game"



def get_game_info(game_id : int) -> dict:
    import requests
    from bs4 import BeautifulSoup # https://stackabuse.com/guide-to-parsing-html-with-beautifulsoup-in-python/
    import re
    import datetime

    url = f"https://fibalivestats.dcd.shared.geniussports.com/u/NBL/{game_id}/"

    # get HTML text
    r = requests.get(url)
    html_text = r.text

    # parse to find and extract date
    soup = BeautifulSoup(html_text, "html.parser")
    # print(f"Parsing HTML with head title: {soup.head.title}\n")

    # init dict to collect all relevant info
    game_dict = {}

    match_detail_blocks = soup.find_all("div", class_="matchDetail")

    # collect venue
    venue = match_detail_blocks[1].text.strip().encode("ascii", "ignore").decode("ascii")
    # game_dict["venue"] = venue[39:]
    game_dict["venue"] = venue.splitlines()[2]

    # collect tip-off date
    tip_off = match_detail_blocks[2].text.strip().encode("ascii", "ignore").decode("ascii")
    date_txt = re.search('\d*/\d*/\d*', tip_off).group(0)   # extract date
    game_dict["date"] = datetime.datetime.strptime(date_txt, "%d/%m/%y")

    # for x in soup.find_all("div", class_="matchDetail"):
    #     x = x.text.strip().encode("ascii", "ignore").decode("ascii")
    #     print(x)
    #     print("==========")

    return game_dict


def build_player_names(x : pd.Series | pd.DataFrame) -> pd.Series | pd.DataFrame:
    """Output the standarized name of a player

    Args:
        x (pd.Series | pd.DataFrame): a serie or a dataframe with player information as per data json

    Returns:
        pd.Series | pd.DataFrame : a series with standarized names of each player
    """
    if isinstance(x, pd.Series):
    # return f"{x['internationalFirstNameInitial']}. {x['internationalFamilyName']}"
        return f"{x['internationalFirstName']} {x['internationalFamilyName']}"
    elif isinstance(x, pd.DataFrame):
        return x.apply(lambda x: f"{x['internationalFirstName']} {x['internationalFamilyName']}", axis=1)

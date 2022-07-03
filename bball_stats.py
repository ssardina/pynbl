# # BSS-AUS: Basketball Statistic System (AUS)
#
# This system tries to replicate [euRobasketAu](https://github.com/jgalowe/euRobasketAu?organization=jgalowe&organization=jgalowe) R scripts in Python.
#
# It scrapes the data and then converts the raw numbers into _advanced stats_.
#
# The data is provided live by [Genius Sports ](https://developer.geniussports.com/). The documentation for the Basketball feed can be found [here](https://developer.geniussports.com/livestats/tvfeed/index_basketball.html).
#
# Messages are sent in JSON structures and use UTF-8 format.
#
# An example of a raw JSON file:
#
# https://fibalivestats.dcd.shared.geniussports.com/data/2087737/data.json

# %%
# Let's first load all required packages...
import json  # https://docs.python.org/3/library/json.html
import os
import pandas as pd
import numpy as np
import datetime
import re

# Load constants
from config import *
import tools

from functools import reduce

# Load relevant game data
game_id = 742430
game_id = 2087737




def build_stint_stats_df(game_id : int) -> pd.DataFrame:
    game_json = tools.get_json_data(game_id)
    pbp_df = tools.get_pbp_df(game_json)
    actions = tools.pbp_get_actions(pbp_df)

    # Extract names of teams in the game
    team_names = tools.get_team_names(game_json)
    team_name_1, team_short_name_1 = team_names[0]
    team_name_2, team_short_name_2 = team_names[1]

    print(f"Game {team_name_1} ({team_short_name_1}) vs {team_name_2} ({team_short_name_2})")
    print(f"Play-by-play df for game {game_id}: {pbp_df.shape}")

    # Compute stints for each team
    starters_1 = tools.get_starters(game_json, 1)
    starters_2 = tools.get_starters(game_json, 2)
    for x in zip([team_name_1, team_name_2], [starters_1, starters_2]):
        print(f"Starters for {x[0]}:")
        print(f"\t {x[1]}")

    stints_1 = tools.pbp_stints_extract(pbp_df, starters_1, 1)
    stints_2 = tools.pbp_stints_extract(pbp_df, starters_2, 2)

    # Add stint info to pbp df
    stints1_df, pbp_aux_df = tools.pbp_add_stint_col(pbp_df, stints_1, "stint1")
    stints2_df, pbp_aux_df = tools.pbp_add_stint_col(pbp_aux_df, stints_2, "stint2")

    # drop plays that are not for statistics (game events, like start/end)
    pbp2_df = pbp_aux_df.loc[(~pbp_aux_df['actionType'].isin(ACT_NON_STATS))]
    pbp2_df = pbp2_df.loc[(~pbp_aux_df['subType'].isin(ACTSSUB_NON_STATS))]


    # KEY POINT: build stint stats for each team
    stats1_df = tools.build_stint_stats(pbp2_df, 1, "stint1")
    stats2_df = tools.build_stint_stats(pbp2_df, 2, "stint2")
    stats_df = pd.concat([stats1_df, stats2_df])
    stats_df.reset_index(inplace=True, drop=True)

    # reorder columns
    index_col = ['tno', 'stint']
    data_col = [ 'poss', 'ortg', 'drtg', 'net_rtg',
                'fga', 'fgm', 'fgp', 'pts',
                'patra', 'patrm', 'patrp',
                '3pt_fga', '3pt_fgm', '3pt_fgp',
                '2pt_fga', '2pt_fgm', '2pt_fgp',
                'fta', 'ftm', 'ftp', 'reb',
                'ast', 'ast_rate', 'fgm_astp',
                'stl', 'stl_rate',
                'blk', 'blk_rate',
                'tov', 'tov_rate',
                'dreb', 'drbp',
                'oreb', 'orbp',
                'trb',  'trbp',
                'ballhand', 'badpass',
                'ofoul',
                '3sec', '8sec', '24sec', 
                'opp_fga_blocked']

    stats_df = stats_df[index_col + data_col + [f'{x}_opp' for x in data_col]]

    # add stint info to stat df
    stints1_df['tno'] = 1
    stints2_df['tno'] = 2
    stints_df = pd.concat([stints1_df, stints2_df])
    stats_df = stats_df.merge(stints_df, left_on=['tno', 'stint'], right_on=['tno', 'id'])

    return stats_df
import os
import datetime
import json
import pandas as pd
from urllib.request import urlopen
from functools import reduce


from config import *

# class Game(object):
#     def __init__(self, id, file=None) -> None:
#         self.game_id = id
#         self.game_file = file

#         self.data_json = self.get_json_data(self.game_id)
#         self.pbp_df = 
#         pass

percent = lambda part, whole: round(100* (part / whole), 2)


##########################################################
# CODE USING JSON DATA
# ##########################################################

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


def get_raw_pbp_fibalivestats(game_id: int):
    data_json = get_json_data(game_id)

    return get_pbp_df(data_json)

def get_pbp_df(data_json):
    # Extract names of teams in the game
    team_names = get_team_names(data_json)
    team_name_1, team_short_name_1 = team_names[0]
    team_name_2, team_short_name_2 = team_names[1]

    # print(f"Game {team_name_1} ({team_short_name_1}) vs {team_name_2} ({team_short_name_2})")


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




##########################################################
# CODE USING P-B-P DATAFRAME
# ##########################################################


def pbp_get_actions(pbp_df: pd.DataFrame) -> pd.DataFrame:
    """Given a pbp dataframe, build a table wtih all possible actions and subactions

    Args:
        pbp_df (pd.DataFrame): play-by-play data

    Returns:
        pd.DataFrame: a table with all possible actions
    """
    actions = pbp_df[['actionType', 'subType']].sort_values('actionType').drop_duplicates()

    actions.set_index('actionType', inplace=True)

    return actions



def pbp_stints_extract(pbp_df : pd.DataFrame, starter_team: set, team_no: int) -> dict:
    """Extract stint information for a team

    A sting is a dict:
        the key is the set of players in the lineup
        the value is a list of interval tuples (period no, left datetime.time, right datetime.time)

    Args:
        game_json (json-obj): live JSON data of a game
        team_no (int): 1 or 2, the team to extract the stints

    Returns:
        dict: stint information extracted for team_no
    """
    stints = {} # here we will collect ther result as a dictionary!

    current_team = starter_team # lineup start
    current_team = frozenset(current_team)
    # print(f"Starter team: {current_team}")
    for period in range(1, 5):
        prev_clock = datetime.time.fromisoformat('00:10:00.000000')
        prev_clock = datetime.time(hour=0, minute=10, second=0)
        end_clock = datetime.time(hour=0, minute=0, second=0)
        subs = pbp_df.loc[(pbp_df['actionType'] == 'substitution') &
                            (pbp_df['tno'] == team_no) &
                            (pbp_df['period'] == period)]
        for sub_clock in list(subs['clock'].unique()) + [end_clock]: # loo on the sub times for the team
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

            # reset prev clock for next subs
            prev_clock = sub_clock

            # print(f'Subs at time {sub_clock}: {players_in} for {players_out}')
            # print(f"\t New team: {current_team}")
        

    return stints


def pbp_get_ranges_mask(pbp_df: pd.DataFrame, time_intervals: list) -> pd.Series:
    """Returns a boolean mask for a pbp df to filter time intervals on the clock/period

    Args:
        pbp_df (pd.DataFrame): the full play-by-play data
        time_interval (list(int, datetime.time, datetime.time)): list of time intervals

    Returns:
        pd.Series: a mask for a pbp df wrt time intervals given
    """

    mask = pd.Series([False]*pbp_df.shape[0]) # initial mask: all selected!
    for interval in time_intervals:
        period, end, start = interval
        # print(f"Period {period} between {start} and {end}")

        mask2 = (pbp_df['period'] == period)
        mask2 = mask2 & (pbp_df['clock'] > start) & (pbp_df['clock'] <= end)

        mask = (mask) | (mask2)

    return mask


def pbp_get_ranges_df(pbp_df: pd.DataFrame, time_intervals: list) -> pd.DataFrame:
    """Projects the pbp within a set of time intervals (e.g., when a stint played) 

    Args:
        pbp_df (pd.DataFrame): the full play-by-play data
        time_interval (list(int, datetime.time, datetime.time)): list of time intervals

    Returns:
        pd.DataFrame: filtered pbp wrt time intervals given
    """
    return pbp_df[pbp_get_ranges_mask(pbp_df, time_intervals)]

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



def pbp_add_stint_col(pbp_df: pd.DataFrame, stints: dict, col_name: str) -> tuple:
    pbp2_df = pbp_df.copy()
    pbp2_df[col_name] = -1  # integer columns cannot store NaN, so we use -1 (no stint)
    pbp2_df.astype({col_name: 'int32'})

    # build dataframe with teams and id
    stints_df = pd.DataFrame({'id': pd.Series(dtype='int'),
                   'lineup': pd.Series(dtype='object'),
                   'intervals': pd.Series(dtype='object')
                   })
    for lineup in enumerate(stints, start=1):
        row = {'id' : lineup[0], 'lineup' : lineup[1], 'intervals' : stints[lineup[1]]}
        stints_df = stints_df.append(row, ignore_index=True)

        # add column with stint id
        intervals_team = stints[lineup[1]]
        mask = pbp_get_ranges_mask(pbp_df, intervals_team)
        pbp2_df.loc[mask, col_name] = lineup[0]

    stints_df['mins'] = stints_df['intervals'].apply(intervals_to_mins)

    return stints_df, pbp2_df


def build_stint_basic_stats(pbp_df: pd.DataFrame, col_name: str) -> pd.DataFrame:
    """Builds stats table aggregated by column col_name (usually, a stint column, with stint id for a team)

    Args:
        pbp_df (pd.DataFrame): a play-by-play table with a column called col_name
        col_name (str): the column to aggregate data (e.g., stints of a team)

    Returns:
        pd.DataFrame: a table with various stats for each value in col_name
    """

    # tuples (name, default value, True if attemps/made/per, mask)
    stats = [ ('ast', 0, False, pbp_df['actionType'] == 'assist'),
             # points
            ('2pt_fg', 0, True, pbp_df['actionType'] == '2pt'),
            ('patr', 0, True, pbp_df['subType'].isin(['layup', 'drivinglayup', 'dunk'])),
            ('3pt_fg', 0, True, pbp_df['actionType'] == '3pt'),
            ('ft', 0, True, pbp_df['actionType'] == 'freethrow'),
            # others
            ('reb', 0, False, pbp_df['actionType'] == 'rebound'),
            ('oreb', 0, False, (pbp_df['actionType'] == 'rebound') & (pbp_df['subType'] == 'offensive')),
            ('dreb', 0, False, (pbp_df['actionType'] == 'rebound') & (pbp_df['subType'] == 'defensive')),
            ('stl', 0, False, pbp_df['actionType'] == 'steal'),
            ('blk', 0, False, pbp_df['actionType'] == 'block'),
             #turnover types
            ('tov', 0, False, pbp_df['actionType'] == 'turnover'),
            ('ballhand', 0, False, (pbp_df['actionType'] == 'turnover') &
                                    (pbp_df['subType'].isin(['ballhandling', 'doubledribble', 'travel'])) ),
            ('badpass', 0, False, (pbp_df['actionType'] == 'turnover') & (pbp_df['subType'] == 'badpass') ),
            ('ofoul', 0, False, (pbp_df['actionType'] == 'turnover') & (pbp_df['subType'] == 'offensive') ),
            ('3sec', 0, False, (pbp_df['actionType'] == 'turnover') & (pbp_df['subType'] == '3sec') ),
            ('8sec', 0, False, (pbp_df['actionType'] == 'turnover') & (pbp_df['subType'] == '8sec') ),
            ('24sec', 0, False, (pbp_df['actionType'] == 'turnover') & (pbp_df['subType'] == '24sec') )
    ]
    stats_dfs = [pd.DataFrame({col_name : pbp_df[col_name].unique()})] # dummy df for left join
    # compute a dataframe (and add it to stats_dfs) for each stat
    for stat in stats:
        name, default, rate, mask = stat
        name_a = f'{name}a' if rate else name
        name_m = f'{name}m'
        name_p = f'{name}p'

        # count no of plays that stat shows up (e.g., 2pt_fga)
        df = pbp_df.loc[mask].groupby(col_name).size().reset_index(name=name_a)

        if rate:
            df2 = pbp_df.loc[mask & (pbp_df['success'] == 1)].groupby(col_name).size().reset_index(name=name_m)
            df2.fillna(default, inplace=True)

            df = df.merge(df2, "left")
            df[name_p] = percent(df[name_m], df[name_a])

        df.fillna(default, inplace=True)    #TODO: seems not working, why?
        stats_dfs.append(df)

    # finally, join all dfs computed (one per stat)
    df = reduce(lambda df1, df2: df1.merge(df2, "left"), stats_dfs)

    # fill all NaN with 0 - These ones it is correct as they are just counting
    df.fillna(0, inplace=True)


    # Now, calculate complex stats from prev columns using the merged df
    # --------------------------------------------------
    # calculate shooting stats
    df['pts'] = 2*df['2pt_fgm'] + 3*df['3pt_fgm'] + df['ftm']
    df['fga'] = df['2pt_fga'] + df['3pt_fga']
    df['fgm'] = df['2pt_fgm'] + df['3pt_fgm']
    df['fgp'] = percent(df['fgm'], df['fga'])

    # # calculate home possessions (possessions only count change of hands, not offensive rebounds and new shots)
    df['poss'] = df['2pt_fga'] + df['3pt_fga'] + 0.44*df['fta'] + df['tov'] - df['oreb']
    df.loc[df['poss'] < 0, 'poss'] = 0

    # calculate ortg
    df['ortg'] = round(df['pts'] / df['poss'], 2)

    # playmaking stats
    df['fgm_astp'] = percent(df['ast'], df['2pt_fgm'] + df['3pt_fgm'])

    # total rebounds
    df['trb'] = df['dreb'] + df['oreb']

    #calculate rates
    df['blk_rate'] = percent(df['blk'], df['poss'])
    df['stl_rate'] = percent(df['stl'], df['poss'])
    df['ast_rate'] = percent(df['ast'], df['poss'])
    df['tov_rate'] = percent(df['tov'], df['poss'])

    # Fill all NaN with 0
    # This is not correct: NaN will arise when dividing by 0 (for %), and we want to keep NaN which is different from having 0
    # for example: orebs/rebs will give % of orebs, but if rebs = 0 (no rebounds taken), we don't want to have 0%!
    # df.fillna(0, inplace=True)


    return df


def build_stint_stats(pbp_df: pd.DataFrame, tno: int, stint_col: str) -> pd.DataFrame:
    ##############################################
    # Compute stint stat data for team 1
    ##############################################
    # basic stats for team's plays
    stint_team_stats_df = build_stint_basic_stats(pbp_df.loc[pbp_df['tno'] == tno], stint_col)
    stint_team_stats_df.rename(columns={stint_col : 'stint'}, inplace=True)
    stint_team_stats_df.insert(0, 'tno', tno)

    # basic stats for opponents' plays
    stint_opp_stats_df = build_stint_basic_stats(pbp_df.loc[pbp_df['tno'] == (2 if tno == 1 else 1)], stint_col)
    stint_opp_stats_df.rename(columns={stint_col : 'stint'}, inplace=True)
    stint_opp_stats_df.insert(0, 'tno', tno)
    stint_opp_stats_df

    stint_stats_df = stint_team_stats_df.merge(stint_opp_stats_df, how='left', on=['tno', 'stint'], suffixes = ("", "_opp"))

    # calculate stats that need both team and opp stats
    # first, let's do the team stats
    stint_stats_df['drtg'] = percent(stint_stats_df['pts_opp'], stint_stats_df['poss_opp'])
    stint_stats_df['net_rtg'] = stint_stats_df['ortg'] - stint_stats_df['drtg']

    stint_stats_df['drbp'] = percent(stint_stats_df['dreb'], stint_stats_df['dreb'] + stint_stats_df['oreb_opp'])
    stint_stats_df['orbp'] = percent(stint_stats_df['oreb'], stint_stats_df['oreb'] + stint_stats_df['dreb_opp'])
    stint_stats_df['trbp'] = percent(stint_stats_df['trb'],
                                    stint_stats_df['oreb'] +
                                    stint_stats_df['dreb'] +
                                    stint_stats_df['oreb_opp'] +
                                    stint_stats_df['dreb_opp'])
    # second, let's do the opp stats
    stint_stats_df['drtg_opp'] = percent(stint_stats_df['pts'], stint_stats_df['poss'])
    stint_stats_df['net_rtg_opp'] = stint_stats_df['ortg_opp'] - stint_stats_df['drtg_opp']

    stint_stats_df['drbp_opp'] = percent(stint_stats_df['dreb_opp'], stint_stats_df['dreb_opp'] + stint_stats_df['oreb'])
    stint_stats_df['orbp_opp'] = percent(stint_stats_df['oreb_opp'], stint_stats_df['oreb_opp'] + stint_stats_df['dreb'])
    stint_stats_df['trbp_opp'] = percent(stint_stats_df['trb_opp'],
                                    stint_stats_df['oreb_opp'] +
                                    stint_stats_df['dreb_opp'] +
                                    stint_stats_df['oreb'] +
                                    stint_stats_df['dreb'])

    # perc of opponent shots that were blocked
    stint_stats_df['opp_fga_blocked'] = percent(stint_stats_df['blk'], stint_stats_df['fga_opp'])
    stint_stats_df['opp_fga_blocked_opp'] = percent(stint_stats_df['blk_opp'], stint_stats_df['fga'])

    # `team_ts%` = round(100*(sum(lineup_dat$team_pts)/(2*(team_fga + 0.44*sum(lineup_dat$team_fta)))),2)

    return stint_stats_df





#########################################################
# AUX TOOLS
#########################################################

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
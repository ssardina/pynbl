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

import pandas as pd
import numpy as np
import datetime

# Load constants
from nbl.config import *
from nbl import tools

from functools import reduce

import logging

# LOGGING_LEVEL = 'INFO'
# # LOGGING_LEVEL = 'DEBUG'

# LOGGING_FMT = '%(asctime)s %(levelname)s %(message)s'
# LOGGING_FMT_DEBUG = "[%(asctime)s %(filename)s->%(funcName)s():%(lineno)s]%(levelname)s: %(message)s"

# import coloredlogs
# # Set format and level of debug
# coloredlogs.install(level=LOGGING_LEVEL, fmt=LOGGING_FMT)

# def set_logging(level):
#     coloredlogs.install(level=level, fmt=LOGGING_FMT_DEBUG if level == "DEBUG" else LOGGING_FMT)


import os
import json
from urllib.request import urlopen

class Game:
    def __init__(self, game_id, round_no=np.NaN) -> None:
        self.game_id = game_id
        self.round_no = round_no
        self.game_json = self.load_json()

        self.teams = dict()
        self.score = dict()
        self.players_df = dict()
        self.starters = dict()

        self.players_stats_df = None
        self.stints_df = None
        self.stints_stats_df = None
        self.pbp_df = None

        self._setup()


    def load_json(self, dir=None) -> bool:
        """Load a game into a JSON object.
            Data will be loaded from local file data-{game_id}.json if exists
            Otherwise will be fetched from server

        Args:
            game_id (int): id of the game
            dir (str): folder where to check and save a copy

        Returns:
            bool: true if successfully loaded
        """
        game_url = os.path.join(URL_LIVESTATS, str(self.game_id), "data.json")

        if dir is not None and os.path.exists(file_json):
            file_json = os.path.join(dir, f"data-{self.game_id}.json")
            game_json = json.load(open(file_json))
            # print(f"Game data loaded from local file: {game_file}")
        else:   # get if from URL
            # store the response of URL
            response = urlopen(game_url)

            # storing the JSON response
            # from url in data
            game_json = json.loads(response.read())

            # assume no json file if game is not yet over!
            game_ended = game_json['pbp'] and game_json['pbp'][0]['actionType'] == "game"
            if not game_ended:
                raise ValueError('Game has not finished yet')

            if dir is not None:
                with open(file_json, 'w') as f:
                    json.dump(game_json, f)
        return game_json

    def get_teams(self):
        return self.teams

    def _setup(self):
        """Extract team names from JSON game

        Args:
            data_json (json-object): JSON live data of a game

        Returns:
            list(tuple(string, string)): full and short names of both teams
        """
        for tm in [1, 2]:
            self.teams[tm] = (self.game_json['tm'][str(tm)]['name'], self.game_json['tm'][str(tm)]['shortName'])
            self.score[tm] = self.game_json['tm'][str(tm)]['full_score']

            # https://pandas.pydata.org/docs/reference/api/pandas.json_normalize.html
            self.players_df[tm] = pd.json_normalize(self.game_json['tm'][str(tm)]['pl'].values())
            self.starters[tm] = set(tools.build_player_names(self.players_df[tm].query("starter == 1")).to_list())

        self.pbp = PBP(self.game_json, self.teams)
        self.pbp_df = self.pbp.get_df()

        return True

    def _compute_stats(self):
        self.players_stats_df = self._extract_players_stats()
        self.stints_df, self.stints_stats_df = self._extract_stints_stats_df()


    def _extract_players_stats(self) -> pd.DataFrame:
        """Extract game stats for each player form game JSOn data

        Args:
            game_json (json dict): the json data of a game

        Returns:
            pd.DataFrame: a table with stats per player in the game for both teams
        """
        players_dfs = []
        for tno in [1, 2]:
            players_df = pd.json_normalize(self.game_json['tm'][str(tno)]['pl'].values())
            players_df.insert(0, 'tno', tno)
            players_df.insert(1, 'player', tools.build_player_names(players_df))
            players_df.insert(2, 'shirtNumber', players_df.pop('shirtNumber'))
            players_df['captain'] = (players_df.captain == 1.0)

            players_df['sMinutes'] = pd.to_datetime(players_df['sMinutes'], format="%M:%S").dt.time
            players_df.drop(players_df[players_df.sMinutes < datetime.time(0, 0, 1)].index, inplace=True)   # drop players with no minutes on court
            players_dfs.append(players_df)

        players_df = pd.concat(players_dfs)
        players_df.reset_index(drop=True, inplace=True)

        return players_df


    def _extract_stints_stats_df(self) -> dict:
        """Build dataframe with stint statistics for a game, by extracting play-by-play data

        Args:
            game_json (dict): json dict data of the game
            game_id (int) : game id of the game, if any

        Returns:
            dict: contains various data and df for the game (including pbp and stint stats dfs)
        """
        # 1. Extract names of teams and scores in the game
        team_name_1, _ = self.teams[1]
        team_name_2, _ = self.teams[2]
        score_1, score_2 = self.score[1], self.score[2]

        # 2. Read game JSON file
        logging.debug(f"Extracting stint stats for game {self.game_id} [{team_name_1} ({score_1}) vs {team_name_2} ({score_2})] - No of PBP: {self.pbp_df.shape[0]}.")

        # print(f"====> Game {team_name_1} ({team_short_name_1}) vs {team_name_2} ({team_short_name_2})")
        # print(f"Play-by-play df for game {game_id}: {pbp_df.shape}")

        # 3. Compute stints (dictionaries) for each team
        logging.debug(f"Starters for each team computed: {self.starters[1]} / {self.starters[2]}")
        stints_1 = pbp_stints_extract(self.pbp_df, self.starters[1], 1)
        stints_2 = pbp_stints_extract(self.pbp_df, self.starters[2], 2)
        logging.debug(f"Stints for each team computed: {len(stints_1)} / {len(stints_2)}")

        # 4. Add stint columns to pbp df, one column per team having stint id number
        stints1_df, self.pbp_df = pbp_add_stint_col(self.pbp_df, stints_1, "stint1")
        stints2_df, self.pbp_df = pbp_add_stint_col(self.pbp_df, stints_2, "stint2")
        logging.debug(f"Stints columns added to pbp df for both teams")


        # 5. Drop plays that are not for statistics (game events, like start/end)
        # Why do we drop plays? Just leave them, who cares..
        # pbp_df = pbp_df.loc[(~pbp_df['actionType'].isin(ACT_NON_STATS))]
        # pbp_df = pbp_df.loc[(~pbp_df['subType'].isin(ACTSSUB_NON_STATS))]
        # pbp_df.reset_index(inplace=True, drop=True)     # re-index as we may have dropped rows

        # 6. Build single stint stats dataframe containing both teams
        stint_stats1_df = self.pbp.build_stats_df(1, "stint1") # full stats for team 1
        stint_stats2_df = self.pbp.build_stats_df(2, "stint2") # full stats for team 2

        # unify stint column name to just "stint"
        stint_stats1_df.rename(columns={'stint1' : 'stint'}, inplace=True)
        stint_stats2_df.rename(columns={'stint2' : 'stint'}, inplace=True)

        # put both stint stats together into a single dataframe
        stint_stats_df = pd.concat([stint_stats1_df, stint_stats2_df])
        stint_stats_df.reset_index(inplace=True, drop=True)
        logging.debug(f"Stint lineup stats df computed (for both teams)")

        # finally, re-order columns (_opp at the end)
        index_col = ['tno', 'stint']
        stint_stats_df = stint_stats_df[index_col + STATS_COLS + [f'{x}_opp' for x in STATS_COLS]]

        # 7. Put together the final stint df
        stints1_df['tno'] = 1
        stints1_df['team'] = team_name_1
        stints2_df['tno'] = 2
        stints2_df['team'] = team_name_2
        stints_df = pd.concat([stints1_df, stints2_df])
        stints_df.reset_index(inplace=True, drop=True)
        index_col = ['id', 'tno', 'team']   # re-order cols
        stints_df = stints_df[index_col + list(filter(lambda x: x not in index_col, stints_df.columns))]

        # 8. Merge stint stats table with stint table to get stint info to stints stats (e.g., intervals and stint players)
        stint_stats_df = stint_stats_df.merge(stints_df, left_on=['tno', 'stint'], right_on=['tno', 'id'])
        stint_stats_df.drop('id', axis=1, inplace=True) # we don't need it, already in stint col
        team_name_col = stint_stats_df.pop('team')
        stint_stats_df.insert(1, "team", team_name_col)

        return stints_df, stint_stats_df


class PBP:
    def __init__(self, game_json, teams) -> None:
        self.game_json = game_json
        self.teams = teams

        self.pbp_df = self._extract_pbp_df()

    def get_df(self):
        return self.pbp_df

    def _extract_pbp_df(self):
        team_name_1, team_short_name_1 = self.teams[1]
        team_name_2, team_short_name_2 = self.teams[2]

        logging.debug(f"Will extract PBP df for game {team_name_1} ({team_short_name_1}) vs {team_name_2} ({team_short_name_2})")

        # extract play-by-play data
        pbp_df = pd.json_normalize(self.game_json, record_path =['pbp'])

        # standarize player's name to be used all over
        pbp_df['player'] = pbp_df.apply(lambda x: tools.build_player_names(x), axis=1)
        pbp_df.loc[pbp_df['periodType'] == "OVERTIME", 'period'] = pbp_df['period'] + 4 # make overtime periods start at 5

        # keep columns 1 to 17, drop all player info
        # This is what is kept ['clock', 's1', 's2', 'lead', 'tno', 'period', 'periodType', 'pno',
        #    'player', 'success', 'actionType', 'actionNumber', 'previousAction',
        #    'qualifier', 'subType', 'scoring']
        # pbp_df = pbp_df.iloc[:, 1:17]
        pbp_df = pbp_df[['clock', 's1', 's2', 'lead', 'tno', 'period', 'periodType', 'pno', 'player', 'success', 'actionType', 'actionNumber', 'previousAction', 'qualifier', 'subType', 'scoring']]

        # set type of time fields
        # pbp_df['gt'] = pd.to_datetime(pbp_df['gt'], format="%M:%S").dt.time
        pbp_df['clock'] = pd.to_datetime(pbp_df['clock'], format="%M:%S:%f").dt.time

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
        pbp_df.sort_values(by=['period', 'clock', 'actionNumber'], ascending=[True, False, True], inplace=True)

        logging.debug(f"PBP df extracted for game {team_name_1} ({team_short_name_1}) vs {team_name_2} ({team_short_name_2})")


        return pbp_df


    def pbp_get_actions(self) -> pd.DataFrame:
        """Given a pbp dataframe, build a table wtih all possible actions and subactions

        Args:
            pbp_df (pd.DataFrame): play-by-play data

        Returns:
            pd.DataFrame: a table with all possible actions
        """
        actions = self.pbp_df[['actionType', 'subType']].sort_values('actionType').drop_duplicates()

        actions.set_index('actionType', inplace=True)

        return actions



    def pbp_stints_extract(self, starter_team: set, team_no: int) -> dict:
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
        stints = {} # here we will collect the result as a dictionary!

        # start with the starting lineup of the team
        current_team = starter_team
        current_team = frozenset(current_team)
        logging.debug(f"Start computing stints for team {team_no} with starters: {current_team}")

        for period in range(1, self.pbp_df['period'].max()+1):
            # first, get the substitutions plays for the team number in the period
            subs_df = self.pbp_df.query("actionType == 'substitution' and tno == @team_no and period == @period")
            # subs_df = pbp_df.loc[(pbp_df['actionType'] == 'substitution') &    # all subs done in period
            #                     (pbp_df['tno'] == team_no) &
            #                     (pbp_df['period'] == period)]

            # keep the last sub of a player that appears more than once in one clock
            # very strange, but it happens. There could be odd or even number of rep per player!
            #   1976446: OVERTIME 17.80secs - player McVeigh comes in, makes 3pt, and gets out. no time passes! :-)
            #   2004608: Period 2 05.600 - B. Kuol (team 2) come out, but then in and out
            #   2116381: Period 4 00:01:36 - Bul Kuol goes out and then in again!
            subs_df = subs_df.drop_duplicates(subset=['clock', 'player'], keep='last')

            # initialize tracking clocks
            prev_clock = datetime.time(hour=0, minute=10 if period < 5 else 5, second=0)
            end_clock = datetime.time(hour=0, minute=0, second=0)

            # loop on the sub times for the team until end of the clock (end of period)
            for sub_clock in list(subs_df['clock'].unique()) + [end_clock]:
                # interval = pd.Interval(datetime.datetime.timestamp(prev_clock), datetime.datetime.timestamp(sub_clock), closed='left')
                interval = (period, prev_clock, sub_clock)
                logging.debug(f"=====> Substitution in period {period} @ {sub_clock}")

                if current_team in stints:
                    stints[current_team].append(interval)   # append intervals of existing stint
                else:
                    stints[current_team] = [interval]   # new stint found!
                    logging.debug(f"New stint was found: {current_team}")

                players_in = set(subs_df.query("clock == @sub_clock and subType == 'in'")['player'].tolist())
                players_out = set(subs_df.query("clock == @sub_clock and subType == 'out'")['player'].tolist())

                dummy_sub = False
                if players_in.intersection(current_team):
                    logging.warning(f"Sub team {team_no} @ {sub_clock} in period {period}: incoming players already in court: {players_in.intersection(current_team)}")
                    dummy_sub = True
                if players_out.difference(current_team):
                    logging.warning(f"Sub team {team_no} @ {sub_clock} in period {period}: outcoming players not in court: {players_out.difference(current_team)}")
                    dummy_sub = True

                # Try to fix the in/out sets (sometimes player goes out and in again at the same time)
                players_in = players_in.difference(current_team)    # keep just those who are not on court (and are coming in)
                players_out = players_out.intersection(current_team)    # keep just those who are on court (and are coming out)

                # Hopefully we have a 1-to-1 substitution, otherwise report!
                if len(players_in) != len(players_out):
                    logging.warning(f"Sub team {team_no} @ {sub_clock} in period {period}: number of in-subs ({len(players_in)}) different from numbers out-subs ({len(players_out)})")
                elif dummy_sub:
                    logging.info("Dummy subs fixed, good subs....")

                logging.debug(f"Current team: {current_team}")
                logging.debug(f"Players out: {players_out}")
                logging.debug(f"Players in: {players_in}")
                current_team = current_team.difference(players_out).union(players_in)
                logging.debug(f"New team: {current_team}")

                # reset prev clock for next subs
                prev_clock = sub_clock

        logging.debug(f"Number of sints extracted for team {team_no}: {len(stints)}")

        return stints


    def pbp_get_ranges_mask(self, time_intervals: list) -> pd.Series:
        """Returns a boolean mask for a pbp df to filter time intervals on the clock/period

        Args:
            pbp_df (pd.DataFrame): the full play-by-play data
            time_interval (list(int, datetime.time, datetime.time)): list of time intervals

        Returns:
            pd.Series: a mask for a pbp df wrt time intervals given
        """

        mask = pd.Series([False]*self.pbp_df.shape[0]) # initial mask: all selected!
        for interval in time_intervals:
            # e.g., [(4, datetime.time(0, 8), datetime.time(0, 5, 50))]
            #   period 4, from 08:00 left to 05:50 left
            period, end, start = interval
            # print(f"Period {period} between {start} and {end}")

            mask2 = (self.pbp_df['period'] == period)
            mask2 = mask2 & (self.pbp_df['clock'] >= start) & (self.pbp_df['clock'] < end)

            mask = (mask) | (mask2)

        return mask


    def pbp_get_ranges_df(self, time_intervals: list) -> pd.DataFrame:
        """Projects the pbp within a set of time intervals (e.g., when a stint played) 

        Args:
            pbp_df (pd.DataFrame): the full play-by-play data
            time_interval (list(int, datetime.time, datetime.time)): list of time intervals

        Returns:
            pd.DataFrame: filtered PBP df wrt time intervals given
        """
        mask = self.pbp_get_ranges_mask(time_intervals)
        return self.pbp_df[mask]


    def pbp_add_stint_col(self, stints: dict, stint_col: str) -> tuple:
        """Extend a PBP df with a stint column denoting the lineup stint in each play

        Args:
            pbp_df (pd.DataFrame): the PBP df to annotate with stints
            stints (dict): the set of stint lineups, each containing a set of interval times
            col_name (str): the column name to use for stint identification of each play

        Returns:
            tuple(pd.DataFrame, pd.DataFrame):
                stint data as a dataframe + PBP df extended with stint id in stint_col column
        """
        pbp2_df = self.pbp_df.copy()
        pbp2_df[stint_col] = -1  # integer columns cannot store NaN, so we use -1 (no stint)
        pbp2_df.astype({stint_col: 'int32'})

        # fill col sint_col in php2_df with stint number and build stint data for df
        stints_rows = []
        for lineup in enumerate(stints, start=1):
            # to build stint df later
            row = {'id' : lineup[0], 'lineup' : sorted(lineup[1]), 'intervals' : stints[lineup[1]]}
            stints_rows.append(row)

            # add column with stint id
            intervals_team = stints[lineup[1]]
            mask = self.pbp_get_ranges_mask(intervals_team)
            pbp2_df.loc[mask, stint_col] = lineup[0]

        # now build the stint df from rows
        # stints_df = pd.DataFrame({'id': pd.Series(dtype='int'),
        #                'lineup': pd.Series(dtype='object'),
        #                'intervals': pd.Series(dtype='object')
        #                })
        stints_df = pd.DataFrame(stints_rows)
        stints_df['mins'] = stints_df['intervals'].apply(tools.intervals_to_mins)

        return stints_df, pbp2_df


    def get_overtimes(self) -> list:
        return self.pbp_df.loc[(self.pbp_df['periodType'] == "OVERTIME"), ['period', 'periodType']].drop_duplicates().to_records(index=False).tolist()


    def build_stats_df(self, tno: int, agg_col = (lambda x: True)) -> pd.DataFrame:
        """Build a dataframe with full statistics for a team

        Args:
            pbp_df (pd.DataFrame): play-by-play data for a game
            tno (int): team number to extract stats for
            agg_col (str): the column to group by (if any)

        Returns:
            pd.DataFrame: _description_
        """
        def build_core_stats(pbp_df: pd.DataFrame, agg_col = (lambda x: True)) -> pd.DataFrame:
            """Build the core stats table aggregated by column agg_col (usually, a stint column, with stint id for a team)

            Args:
                pbp_df (pd.DataFrame): a play-by-play table with a column called agg_col
                agg_col (str): the column to aggregate data (e.g., stints of a team), if any

            Returns:
                pd.DataFrame: a table with various stats for each value in agg_col
            """

            # tuples (name, default value, True if attemps/made/per, mask)
            stats = [ (F_AST, 0, False, pbp_df['actionType'] == 'assist'),
                    # points
                    (F_2PTFG, 0, True, pbp_df['actionType'] == '2pt'),
                    (F_PATR, 0, True, pbp_df['subType'].isin(['layup', 'drivinglayup', 'dunk'])),
                    (F_3PTFG, 0, True, pbp_df['actionType'] == '3pt'),
                    (F_FT, 0, True, pbp_df['actionType'] == 'freethrow'),
                    # others
                    (F_REB, 0, False, pbp_df['actionType'] == 'rebound'),
                    (F_OREB, 0, False, (pbp_df['actionType'] == 'rebound') & (pbp_df['subType'] == 'offensive')),
                    (F_ODREB, 0, False, (pbp_df['actionType'] == 'rebound') & (pbp_df['subType'] == 'offensivedeadball')),
                    (F_DREB, 0, False, (pbp_df['actionType'] == 'rebound') & (pbp_df['subType'] == 'defensive')),
                    (F_STL, 0, False, pbp_df['actionType'] == 'steal'),
                    (F_BLK, 0, False, pbp_df['actionType'] == 'block'),
                    #turnover types
                    (F_TOV, 0, False, pbp_df['actionType'] == 'turnover'),
                    (F_BALLHAND, 0, False, (pbp_df['actionType'] == 'turnover') &
                                            (pbp_df['subType'].isin(['ballhandling', 'doubledribble', 'travel'])) ),
                    (F_BADPASS, 0, False, (pbp_df['actionType'] == 'turnover') & (pbp_df['subType'] == 'badpass') ),
                    (F_OFOUL, 0, False, (pbp_df['actionType'] == 'turnover') & (pbp_df['subType'] == 'offensive') ),
                    (F_3SEC, 0, False, (pbp_df['actionType'] == 'turnover') & (pbp_df['subType'] == '3sec') ),
                    (F_8SEC, 0, False, (pbp_df['actionType'] == 'turnover') & (pbp_df['subType'] == '8sec') ),
                    (F_24SEC, 0, False, (pbp_df['actionType'] == 'turnover') & (pbp_df['subType'] == '24sec') )
            ]
            # start with a dummy df for full left join with one row per stint number: 1,2,3,...,N
            stats_dfs = [pd.DataFrame({agg_col : pbp_df[agg_col].unique()})] 

            for stat in stats:  # for each stat, compute a dataframe df (and add it to stats_dfs)
                name, default, rate, mask = stat
                name_a = f'{name}a' if rate else name
                name_m = f'{name}m'
                name_p = f'{name}p'

                # df with the count no of plays that stat shows up (e.g., 2pt_fga) via the stat's mask
                df = pbp_df.loc[mask].groupby(agg_col).size().reset_index(name=name_a)

                if rate:    # if the stat also has rate stats (e.g, shots made), then compute them
                    df2 = pbp_df.loc[mask & (pbp_df['success'] == 1)].groupby(agg_col).size().reset_index(name=name_m)
                    df2.fillna(default, inplace=True)

                    df = df.merge(df2, "left")
                    df[name_p] = tools.percent(df[name_m], df[name_a])

                df.fillna(default, inplace=True)    #TODO: seems not working, why?
                stats_dfs.append(df)

            # finally, join all dfs computed (one per stat)
            df = reduce(lambda df1, df2: df1.merge(df2, "left"), stats_dfs)

            # fill all NaN with 0 - These ones it is correct as they are just counting
            df.fillna(0, inplace=True)


            # Now, calculate complex stats from prev columns using the merged df
            # --------------------------------------------------
            # calculate shooting stats
            df[F_PTS] = 2*df[F_2PTFGM] + 3*df[F_3PTFGM] + df[F_FTM]
            df[F_FGA] = df[F_2PTFGA] + df[F_3PTFGA]
            df[F_FGM] = df[F_2PTFGM] + df[F_3PTFGM]
            df[F_FGP] = tools.percent(df[F_FGM], df[F_FGA])

            # # calculate home possessions (possessions only count change of hands, not offensive rebounds and new shots)
            df[F_POSS] = df[F_2PTFGA] + df[F_3PTFGA] + 0.44*df[F_FTA] + df[F_TOV] - df[F_OREB]
            df.loc[df[F_POSS] < 0, 'poss'] = 0

            # calculate offensive rating
            df[F_ORTG] = tools.percent(df[F_PTS], df[F_POSS])

            # playmaking stats
            df[F_FGMASTP] = tools.percent(df[F_AST], df[F_2PTFGM] + df[F_3PTFGM])

            # total rebounds
            df[F_TRB] = df[F_DREB] + df[F_OREB]

            #calculate rates
            df[F_BLKR] = tools.percent(df[F_BLK], df[F_POSS])
            df[F_STLR] = tools.percent(df[F_STL], df[F_POSS])
            df[F_ASTR] = tools.percent(df[F_AST], df[F_POSS])
            df[F_TOVR] = tools.percent(df[F_TOV], df[F_POSS])

            # TS% = true shooting percentage, combines 2pts, 3pts, ft
            df[F_TSP] = tools.percent(df[F_PTS], 2*(df[F_FGA] + 0.44*df[F_FTA]))

            # Fill all NaN with 0
            # This is not correct: NaN will arise when dividing by 0 (for %), and we want to keep NaN which is different from having 0
            # for example: orebs/rebs will give % of orebs, but if rebs = 0 (no rebounds taken), we don't want to have 0%!
            # df.fillna(0, inplace=True)

            return df

        ##############################################
        # Compute stint stat data for the team tno
        ##############################################
        # 1. compute core stats for team and its opponent
        team_core_stats_df = build_core_stats(pbp_df.loc[pbp_df['tno'] == tno], agg_col)
        opp_core_stats_df = build_core_stats(pbp_df.loc[pbp_df['tno'] == (2 if tno == 1 else 1)], agg_col)

        # 3. put both stats together (opponent columns get "_opp" suffix)
        #   we need this to calculate next set of stats that need both core stats
        stats_df = team_core_stats_df.merge(opp_core_stats_df, how='left', on=agg_col, suffixes = ("", "_opp"))
        stats_df.insert(0, 'tno', tno)    # these stats are for team tno

        # 4. calculate stats that need both team and opp stats
        # for the team
        stats_df[F_DRTG] = tools.percent(stats_df[f'{F_PTS}_opp'], stats_df[f'{F_POSS}_opp']) # drtg = defensive rating
        stats_df[F_NRTG] = stats_df[F_ORTG] - stats_df[F_DRTG]    # net rating: offensive rating - defensive rating

        stats_df[F_DREBC] = stats_df[F_DREB] + stats_df[f'{F_OREB}_opp']
        stats_df[F_DREBP] = tools.percent(stats_df[F_DREB], stats_df[F_DREB] + stats_df[f'{F_OREB}_opp'])
        stats_df[F_OREBC] = stats_df[F_OREB] + stats_df[f'{F_DREB}_opp']
        stats_df[F_OREBP] = tools.percent(stats_df[F_OREB], stats_df[F_OREB] + stats_df[f'{F_DREB}_opp'])
        stats_df[F_TRBR] = tools.percent(stats_df[F_TRB],
                                        stats_df[F_OREB] +
                                        stats_df[F_DREB] +
                                        stats_df[f'{F_OREB}_opp'] +
                                        stats_df[f'{F_DREB}_opp'])
        stats_df[F_OPPFGABLK] = tools.percent(stats_df[F_BLK], stats_df[f'{F_FGA}_opp'])

        # # for the opponent (same stats as team)
        stats_df[f'{F_DRTG}_opp'] = tools.percent(stats_df[F_PTS], stats_df[F_POSS])
        stats_df[f'{F_NRTG}_opp'] = stats_df[f'{F_ORTG}_opp'] - stats_df[f'{F_DRTG}_opp']

        stats_df[f'{F_DREBC}_opp'] = stats_df[f'{F_DREB}_opp'] + stats_df[F_OREB]
        stats_df[f'{F_DREBP}_opp'] = tools.percent(stats_df[f'{F_DREB}_opp'], stats_df[f'{F_DREB}_opp'] + stats_df[F_OREB])
        stats_df[f'{F_OREBC}_opp'] = stats_df[f'{F_OREB}_opp'] + stats_df[F_DREB]
        stats_df[f'{F_OREBP}_opp'] = tools.percent(stats_df[f'{F_OREB}_opp'], stats_df[f'{F_OREB}_opp'] + stats_df[F_DREB])
        stats_df[f'{F_TRBR}_opp'] = tools.percent(stats_df[f'{F_TRB}_opp'],
                                        stats_df[f'{F_OREB}_opp'] +
                                        stats_df[f'{F_DREB}_opp'] +
                                        stats_df[F_OREB] +
                                        stats_df[F_DREB])
        stats_df[f'{F_OPPFGABLK}_opp'] = tools.percent(stats_df[f'{F_BLK}_opp'], stats_df[F_FGA])


        return stats_df





# %%
if __name__ == "__main__":
    logging.info("reporting log....")

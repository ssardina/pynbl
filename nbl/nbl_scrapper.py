"""
pyNBL: Basketball Statistic System for Australian NBL

This script **incrementally** builds a set of tables from NBL Basketball Games:

1. A table of games played, with team names, points, venue, etc.
2. A table of players with their states across games.
3. A table of stints lineups per game, containing stints in the games and their time intervals on them.
4. A table of statistics for stint lineups (advance) for each game and each team. 

A stint is a lineup of players who play together in different interval periods across the game. 

Tables will be saved in CSV and Excel formats as well as in [Pickle format](https://docs.python.org/3/library/pickle.html) for later recovery as Panda DataFrames.

The data comes as a raw JSON file using the game id (e.g., `2087737`):

    https://fibalivestats.dcd.shared.geniussports.com/data/2087737/data.json
"""

##########################################
# LOGGING = START
##########################################
import coloredlogs, logging
# coloredlogs.install()
# logging.info("It works!")

# Create top level logger
log = logging.getLogger("main")

# Add console handler using our custom ColoredFormatter
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
cf = coloredlogs.ColoredFormatter("[%(name)s][%(levelname)s]  %(message)s (%(filename)s:%(lineno)d)")
ch.setFormatter(cf)
log.addHandler(ch)

# Add file handler
fh = logging.FileHandler('app.log')
fh.setLevel(logging.DEBUG)
ff = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh.setFormatter(ff)
log.addHandler(fh)

# Set log level
log.setLevel(logging.INFO)
# log.setLevel(logging.CRITICAL + 1)
##########################################
# LOGGING = END
##########################################

import os
import argparse
from pathlib import Path
import pandas as pd
import numpy as np

import datetime
import os
import shutil
from pathlib import Path
from urllib.error import HTTPError
import importlib

from nbl.config import *
from nbl import bball_stats, tools
# import tools
# from games_22_23 import GAMES

DATA_DIR_DEFAULT = 'test/'

# Set folder with data files and Pickle tables saved on disk
def get_save_files(dir):
    FILES = dict()
    FILES['stint_stats'] = Path(dir, "stint_stats_df").with_suffix('.pkl')
    FILES['stints'] = Path(dir, "stints_df").with_suffix('.pkl')
    FILES['games'] = Path(dir, "games_df").with_suffix('.pkl')
    FILES['players'] = Path(dir, "players_df").with_suffix('.pkl')

    return FILES

if __name__=="__main__":
    parser = argparse.ArgumentParser(
        description=
        'Statistics scrapper for  Australian NBL league. Computes players and stint lineups stats.\n'
        'Examples:\n\n'
        '\t python -m nbl.nbl_scrapper\n'
        '\t python -m nbl.nbl_scrapper --games games_22_23\n'
        '\t python -m nbl.nbl_scrapper --games games_22_23 --data-dir test --save\n',
        formatter_class=argparse.RawTextHelpFormatter
        # formatter_class = argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        '--data-dir',
        type=str,
        default=DATA_DIR_DEFAULT,
        help='Directory to read and write data (e.g., csv and json files) (default: %(default)s).'
    )
    parser.add_argument(
        '--games',
        type=str,
        default='games.py',
        help='File containing the games to scrape (defines list variable GAMES) (default: %(default)s).'
    )
    parser.add_argument(
        '--reload',
        action='store_true',
        default=False,
        help='Reload all games from scratch; do not use store files (default: %(default)s).'
    )
    parser.add_argument(
        '--save',
        action='store_true',
        default=False,
        help='Append games scraped to current set of games (default: %(default)s).'
    )


    args = parser.parse_args()
    log.debug(args)

    log.info(f"File to import game list: {args.games}")
    try:
        games_module = importlib.import_module(args.games)
        GAMES=games_module.GAMES
    except ModuleNotFoundError:
        log.error(f"Game module {args.games} not found. Cannot initialize GAMES variable.")
        exit(1)
    except AttributeError:
        log.error(f"Variable GAMES not defined in module {args.games}. Check format.")
        exit(1)

    if not os.path.exists(args.data_dir):
        log.error(f"Data folder *{args.data_dir}* does not exist! Exit...")
        exit(1)
    data_dir = args.data_dir

    log.info(f"Starting to scrape games on: {datetime.datetime.now().strftime('%m/%d/%Y, %H:%M:%S')}")
    # sort games by rounds (second component of tuple) and get min/max rounds
    GAMES.sort(key = lambda x: x[1])
    first_round = GAMES[0][1]
    last_round = GAMES[-1][1]   # last round to scrape (start with last of season)

    print(f"Number of games to scrape ({len(GAMES)}) - Rounds {first_round} to {last_round}")
    log.debug(f"Games to scrape ({len(GAMES)}): {GAMES}")
    print(f"Folder to be used: {data_dir}")
    print(f"Reload games? {args.reload}")

    # We start by loading all saved previous games, if any, as we want to append to that database (and we don't want to recompute them).
    saved_stint_stats_df = None
    saved_stints_df = None
    saved_games_df = None
    saved_players_df = None
    existing_games = []

    FILES = get_save_files(data_dir)

    if not args.reload:
        # load the stat dataframe already stored as a file
        log.debug(f"Loading recorded dataframes from files")
        try:
            saved_stint_stats_df = pd.read_pickle(FILES['stint_stats'])
            saved_stints_df = pd.read_pickle(FILES['stints'])
            saved_games_df = pd.read_pickle(FILES['games'])
            saved_players_df = pd.read_pickle(FILES['players'])
            # collect game ids of all games recovered from file
            existing_games = saved_games_df.game_id.unique()
        except FileNotFoundError as e:
            print("Error loading Pickle files: ", e)
            saved_stint_stats_df = None
            saved_stints_df = None
            saved_games_df = None
            saved_players_df = None
            existing_games = []
    else:
        existing_games = []

    print(f"Number of games recovered from previous saves: {len(existing_games)}")
    print()
    log.debug(f"Games recovered ({len(existing_games)}): {existing_games}")

    # initialize list of dataframes
    stint_stats_dfs = []
    stints_dfs = []
    players_dfs = []
    games_data = []

    # Go through every game and build data for each (if played); we'll put them together after.
    # stop in a round where there are missing games
    for game in GAMES:
        # game is beyond the last round to scrape, stop processing..
        if game[1] > last_round:
            break

        # get game_id and round no (if available)
        if isinstance(game, tuple):
            game_id, round_no = game
        else:
            game_id = game
            round_no = np.nan # no round info available

        # don't scrape game data if already loaded from file, skip it
        if game_id in existing_games:
            log.debug(f"Game {game_id} was already saved on file; no scrapping...")
            continue

        ##################################################################
        # !!! MAIN STEP: scrape and compute the actual stats for the game
        ##################################################################
        log.debug(f"Computing game {game_id} (round {round_no})...")

        # 1. Read game JSON file
        try:
            game_json = tools.get_json_data(game_id, dir=data_dir)
        except (HTTPError, ValueError) as e:
            last_round = round_no    # this is the last round to be processed!
            log.debug(f"Game {game_id} JSON data not available yet for round: {round_no}: ", type(e), e)
            print(f"Game {game_id} for round {round_no} not available yet!")
            continue

        result = bball_stats.build_game_stints_stats_df(game_json, game_id)
        game_stint_stats_df = result['stint_stats_df']   #  this is basically what we care, the stint stats
        game_stints_df = result['stints_df']
        game_team1, game_team2 = result['teams']

        # Add the game id column to game tables
        game_stint_stats_df.insert(0, 'game_id', game_id)
        game_stints_df.insert(0, 'game_id', game_id)

        # Extract players in the game
        players_df = bball_stats.get_players_stats(game_json)
        players_df.insert(0, 'game_id', game_id)

        # Add tables to collected set of tables, one per game
        stint_stats_dfs.append(game_stint_stats_df)
        stints_dfs.append(game_stints_df)
        players_dfs.append(players_df)

        # Next build the record for the game dataframe
        # first, extract date of game from HTML page
        try:
            game_info = tools.get_game_info(game_id)
        except:
            log.warning("No venue/date available")
            game_info = { "venue" : np.nan, "date": np.nan}

        print(f"Extracted game {game_id} for round {round_no}: {game_team1[0]} ({game_team1[1]}) vs {game_team2[0]} ({game_team2[1]}) on {game_info['date']}")

        games_data.append({"game_id": game_id,
                            "date" : game_info['date'],
                            "round": round_no,
                            "team1": game_team1[0],
                            "team2": game_team2[0],
                            "s1": game_team1[1],
                            "s2": game_team2[1],
                            "winner": 1 if game_team1[1] > game_team2[1] else 2,
                            "venue" : game_info["venue"]}
                        )


    #################################
    # All games have been processed, now put all data-frames together
    #################################
    if len(games_data) == 0:
        raise SystemExit("No new games scrapped! Finishing...")

    # First, build a dataframe with all the game data collected
    games_scrapped_df = pd.DataFrame(games_data)    # games that have been scrapped from web
    games_df =  games_scrapped_df if saved_games_df is None else pd.concat([saved_games_df, games_scrapped_df])
    games_df.reset_index(inplace=True, drop=True)

    # Build players dataframe
    players_df = pd.concat(players_dfs + ([saved_players_df] if saved_players_df is not None else []))
    players_df.reset_index(inplace=True, drop=True)

    # Build stint stats dataframe
    stint_stats_df = pd.concat(stint_stats_dfs + ([saved_stint_stats_df] if saved_stint_stats_df is not None else []))
    stint_stats_df.reset_index(inplace=True, drop=True)

    # Build stints dataframe
    stints_df = pd.concat(stints_dfs + ([saved_stints_df] if saved_stints_df is not None else []))
    stints_df.reset_index(inplace=True, drop=True)

    msg = f"""
    Number of total games collected: {games_df.shape[0]}
    Number of NEW collected: {games_df.shape[0] - len(existing_games)}
    Number of PENDING/FAILED games {len(GAMES) - games_df.shape[0]}
    {games_scrapped_df}
    """
    print(msg)
    log.info(msg)

    if args.save:
        # make a backup of existing tables on files
        for pkl_file in FILES.values():
            for ext in ['.csv', '.xlsx', '.pkl']:
                file = Path(pkl_file).with_suffix(ext)
                if os.path.exists(file):
                    # print("Backup file", file)
                    shutil.copy(file, str(file) + ".bak")

        # dump stint stats dataframe
        stint_stats_df.to_pickle(Path(data_dir, "stint_stats_df").with_suffix(".pkl"))
        stint_stats_df.to_csv(Path(data_dir, "stint_stats_df").with_suffix(".csv"), index=False)
        stint_stats_df.to_excel(Path(data_dir, "stint_stats_df").with_suffix(".xlsx"), index=False)

        # dump stint stats dataframe
        stints_df.to_pickle(Path(data_dir, "stints_df").with_suffix(".pkl"))
        stints_df.to_csv(Path(data_dir, "stints_df").with_suffix(".csv"), index=False)
        stints_df.to_excel(Path(data_dir, "stints_df").with_suffix(".xlsx"), index=False)

        # dump game dataframe
        games_df.to_pickle(Path(data_dir, "games_df").with_suffix(".pkl"))
        games_df.to_csv(Path(data_dir, "games_df").with_suffix(".csv"), index=False)
        games_df.to_excel(Path(data_dir, "games_df").with_suffix(".xlsx"), index=False)

        # dump players dataframe
        players_df.to_pickle(Path(data_dir, "players_df").with_suffix(".pkl"))
        players_df.to_csv(Path(data_dir, "players_df").with_suffix(".csv"), index=False)
        players_df.to_excel(Path(data_dir, "players_df").with_suffix(".xlsx"), index=False)

        now = datetime.datetime.now() # current date and time
        date_time = now.strftime("%m/%d/%Y, %H:%M:%S")

        print(f"Saved tables in folder {data_dir} @ {date_time}")
        log.info(f"Saved tables in folder {data_dir} @ {date_time}")
# Pynbl: Python AUS Bball Statistic System

[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/ssardina/pynbl/HEAD)

The scripts and notebooks in this repo allows to extract information and statistics from Basketball game data provided by [fibalivestats](http://www.fibaorganizer.com/) for the [NBL Australian Basketball](https://nbl.com.au/) competition. It is similar in functionality and is inspired in R-based system [euRobasketAu](https://github.com/jgalowe/euRobasketAu?organization=jgalowe&organization=jgalowe).

Game data (e.g., play-by-play information) is fetch (or provided offline) as a [JSON](https://www.w3schools.com/js/js_json_datatypes.asp) type structure via a game-id number (e.g., `1976446`).

The structure is processed to build various [Panda](https://pandas.pydata.org/) Dataframes (i.e., tables), which can then be saved as CSV or Excel files, or as [Pickle](https://docs.python.org/3/library/pickle.html) format for re-loading later on.

The **main system** is a Jupyter Notebook [bball_stats.ipynb](bball_stats.ipynb), which can be used to _incrementally_ construct (i.e., extend previous results) statistical tables as games are played along the season.

Currently, the system focuses on building _stint lineup_ statistics (but will be extended further to calculate other stats, like with/without or on/off). To do so, the system builds the following **main tables**:

- a Pandas table with _**games' information**_ (e.g., team names, scores, date, venue, etc.).
- a Pandas table with stats for each _**teams' stint lineup**_ (e.g., lineup of players who played together in different intervals during the game).

These Pandas Dataframes can then be saved in various formats, inclding CSV and Excel.

To compute the above tables, the system also extracts/computes, via various functions, the following information:

- **Game information**, including teams, scores, venue, and date.
- The **starting lineup** of a team.
- A **table of stints** for each team containing the lineup of players of each stint, the intervals and the number of minutes the stint was on court.
- A **play-by-play** DataFrame, with and without the stint id on each play for each team (denoting which lineups where on court at a play).

- [Pynbl: Python AUS Bball Statistic System](#pynbl-python-aus-bball-statistic-system)
  - [1. Pre-requisites](#1-pre-requisites)
  - [2. How to use the system](#2-how-to-use-the-system)
    - [Main functions](#main-functions)
  - [3. Development info](#3-development-info)
    - [Game number id](#game-number-id)
    - [Main game data](#main-game-data)
    - [Date and venue information](#date-and-venue-information)
    - [Date and time formats](#date-and-time-formats)
    - [Statistics Fields](#statistics-fields)
  - [Links & Resources](#links--resources)
  - [API Services](#api-services)
    - [Genius Sports](#genius-sports)
    - [Other APIs and pages](#other-apis-and-pages)
    - [Other similar basketball stat systems/pages](#other-similar-basketball-stat-systemspages)
    - [Data visualization](#data-visualization)
  - [Contact & Contributions](#contact--contributions)

## 1. Pre-requisites

The system runs in Python 3.8+ as a Jupyter notebook.

Assuming Python is installed, install the required modules by running:

```shell
$ pip install -r requirements.txt
```

The system has been developed with [VS Code](https://code.visualstudio.com/docs/datascience/jupyter-notebooks) and its [Jupyter extension](https://pypi.org/project/jupyter/).

Data is fetched from the [Genius Sports](https://news.geniussports.com/australian-national-basketball-league-extends-data-technology-partnership-with-genius-sports-group/) clould service via their link `https://livestats.dcd.shared.geniussports.com/data`. Some relevant documentation can be found [here](https://support.geniussports.com/en/support/solutions/articles/9000008009-api-feed-overview-and-documentation),although it does not seem to be exactly that REST API.

## 2. How to use the system

Open Jupyter notebook [bball_stats.ipynb](bball_stats.ipynb), via the browser (with a proper Juypter server running) or via an IDE like [VS Code](https://code.visualstudio.com/docs/datascience/jupyter-notebooks).

The data tables computed are the following Pandas dataframes:

- `stats_df`: all stint lineup statistics per team in games.
- `games_df`: basic information about each games.
- `pbp_df`: all play-by-play data.

The steps are as follows:

1. **Define variables** initial variables for the run:
   * `games`: a list of game tuples/ids representing the games to scrape and process. Each tuple should be of the form `(game_id, game1, round1, game2, round2)`. If only the `game_id` is given, all the other data will set to `np.NaN` ("missing").
   * `file_stats_df` and `games_stats_df` to point to the Pickle files storing the initial stat and ame tables that have already been computed (for previous games so far).
2. **Define the new games** to be scraped and computed, together with the files where existing previous data (stats and games) has been saved.
   * Each game needs a game-id, and the game numbers for each team.
3. **Run the system** to compute new stats and games and append them with the existing saved ones (if any).
4. **Save updated stats and games** to file (for later incremental extension).

To incrementally extend the existing database/tables as new games are played, the system starts by loading pre-saved tables (from files `file_stats_df` and `games_stats_df`), and then goes to scrape all new games defined in list `games`, one by one, and calculate the stint stats and game info.

At the end, the new tables `stats_df` and `games_df`  are the initial (loaded) tables plus the new stats and games data form the new games. These new tables can finally be materialized (i.e., saved) to file. This will avoid re-computing the stats for all the old games, next time the system is run.

### Main functions

* `bball_stats.build_game_stints_stats_df(game_id)`
* `tools.get_game_info(game_id)`
* `bball_stats.pbp_get_ranges_mask(pbp_df: pd.DataFrame, time_intervals: list) -> pd.Series`
* `bball_stats.get_starters(game_json, tm: int) -> set`
* `bball_stats.get_pbp_df(data_json)`

## 3. Development info

### Game number id

Each game has a number id, which is needed to scrape all the game data.

This game id can be obtained from the NBL link, for example for game id `2087737`:

https://nbl.com.au/games/2087737

### Main game data

Most of the game data comes as a JSON structure provided by Fibalivestats via the following link template:

https://fibalivestats.dcd.shared.geniussports.com/data/XXXXXXX/data.json

where `XXXXXXX` refers to the game id.

```json
{
    "clock": "00:00",
    "period": 4,
    "periodLength": 10,
    "periodType": "REGULAR",
    "inOT": 0,
    "tm": {
        ...
    },
    "pbp": [
        ...
    ],
    "leaddata": [
        ...
    ],
    "disableMatch": 0,
    "attendance": 4015,
    "periodsMax": 4,
    "periodLengthREGULAR": 10,
    "periodLengthOVERTIME": 5,
    "timeline": [],
    "scorers": {
        ...
    },
    "totalTimeAdded": 0,
    "totallds": {
        ...
    },
    "officials": {
        ...
    },
    "othermatches": [
        ...
    ]
}
```

The main key processed in `pbp`, which stores the play-by-play information of the game. The `tm` key (team information) is also used to extract the starting line of each team.

The API clould service is provided by [Genius Sports ](https://developer.geniussports.com/), which also provides _livestream data feed_, but seems to require an API key via registration. Developer info can be found [here](https://developer.geniussports.com/livestats/tvfeed/index_basketball.html); see also links below.

### Date and venue information

The _date_ and _venue_ of a game is not part of the JSON data, so it is scraped from HTML pages (via [request](https://requests.readthedocs.io/en/latest/) and [BeautifulSoup](https://www.crummy.com/software/BeautifulSoup/bs4/doc/) Python packages) using links of this form:

https://fibalivestats.dcd.shared.geniussports.com/u/NBL/1976446/

**NOTE:** Some other information seems to be available on other URLs, such as:

https://fibalivestats.dcd.shared.geniussports.com/data/competition/30249.json

Although it is not clear what `30249` means and how it can be obtained.

### Date and time formats

The _**game time**_ is tracked in format `MM:SS`, whereas the _**clock time**_ is tracked as `MM:SS:CC`, where `CC` is hundredths of a second. 

When a period starts, clock is "`10:00:00`" (that is, 10 min left).

### Statistics Fields

Various advanced statistics are calculated from play-by-play. These are used at this point for assessing **stint lineups**, but will be extended to do On/Off, Shooting, Splits, and other interesting statistical settings.

A good example of statistic fields and settings that can be done can be found here:

https://www.basketball-reference.com/players/a/antetgi01/lineups/2016

## Links & Resources

## API Services

### Genius Sports

- [Genius Sports Developer Centre](https://developer.geniussports.com/).
    - [Genius API - Overview and Documentation](https://support.geniussports.com/en/support/solutions/articles/9000008009-api-feed-overview-and-documentation).
  - [REST API Documentation](https://developer.geniussports.com/warehouse/rest/index_basketball.html).
  - Get all matches (but requires key!): https://api.wh.geniussports.com/v1/basketball/stream/matches

### Other APIs and pages

- Game information page: https://fibalivestats.dcd.shared.geniussports.com/u/NBL/<GAME_ID\>
- [NBL Game Fixture](https://nbl.com.au/fixture).
- [FIBA LiveStats V7](http://www.fibaorganizer.com/): a notebook-based software application to record basketball game statistics and webcast games in real time.
- [Best API](https://betsapi.com/l/1714/Australia-NBL): paid RESTful API.

### Other similar basketball stat systems/pages

* [euRobasketAu](https://github.com/jgalowe/euRobasketAu?organization=jgalowe&organization=jgalowe): a collection of R scripts to  scrape game data from [fibalivestats](http://www.fibaorganizer.com/) and calculate _advanced stats_. It is an adaptation of a system for European leagues and the system Py-nbl-stats is inspired on.
* [Basketball-reference.com](https://www.basketball-reference.com/players/g/ginobma01.html): here is an example of stats for each player, in this case Manu Ginobili.
* [Cleaning-the-glass](https://cleaningtheglass.com/stats/guide/player_onoff): Players on/off explained.

### Data visualization

* [Public Tableau](https://public.tableau.com) can be used to visualize the data produced by this system, for example [here](https://public.tableau.com/app/profile/john5460/viz/NBL2021-22/CompareOnOff?publish=yes)
* Special graphs and charts can be done using [seaborn](https://seaborn.pydata.org/) and [matplotlib](https://matplotlib.org/). **[INCOMPLETE - TO DEVELOP]**

## Contact & Contributions

Developed by Sebastian Sardina (ssardina@gmail.com, [ssardina @ GitHub](https://github.com/ssardina)) with support from [jgalowe @ GitHub](https://github.com/jgalowe).

Based on [euRobasketAu](https://github.com/jgalowe/euRobasketAu?organization=jgalowe&organization=jgalowe) R-based scripts.

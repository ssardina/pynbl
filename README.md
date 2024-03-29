# Pynbl: Python AUS Bball Statistic System

This repo contains scripts and notebooks to extract information and statistics for the [NBL Australian Basketball](https://nbl.com.au/) competition using the Basketball game data provided by [fibalivestats](http://www.fibaorganizer.com/). It is inspired and similar in functionalities to [euRobasketAu](https://github.com/jgalowe/euRobasketAu?organization=jgalowe&organization=jgalowe) R-based system.

Game data (e.g., play-by-play information) is fetch (or provided offline) as a [JSON](https://www.w3schools.com/js/js_json_datatypes.asp) type structure via a game-id number (e.g., `1976446`).

The structure is processed to build various [Panda](https://pandas.pydata.org/) DataFrames (i.e., tables), which can then be saved as CSV, Excel, or [Pickle](https://docs.python.org/3/library/pickle.html) formats.

The system is provided in two ways:

* A Jupyter Notebook [bball_stats.ipynb](bball_stats.ipynb), which can be used to _incrementally_ construct (i.e., extend previous results) statistical tables as games are played along the season.
* A script [nbl.nbl_scrapper](nbl/nbl_scrapper.py), which can be used a stand-alone script to scrape, build stats, and save tables.

Currently, the system focuses on building **_stint lineup_ statistics**, but the idea is to extended it further to calculate other stats, like with/without or on/off. To do so, the system builds the following tables:

1. **Games table**: contains data about games played (e.g., team names, scores, date, venue, etc.).
2. **Players table**: contains statistics on each player across games played.
3. **Stints table**: contains the stint lineups of each game for both teams (e.g., which players in each stint and the intervals played together).
4. **Stints stats table**: contains statistics per stints in games.

These Pandas Dataframes can then be saved in various formats, including CSV and Excel.

- [Pynbl: Python AUS Bball Statistic System](#pynbl-python-aus-bball-statistic-system)
  - [1. Pre-requisites \& setup](#1-pre-requisites--setup)
  - [2. How to use the notebook system](#2-how-to-use-the-notebook-system)
  - [3. How to use the standalone script](#3-how-to-use-the-standalone-script)
    - [Setting it as a cron job](#setting-it-as-a-cron-job)
  - [4. Development information](#4-development-information)
    - [Game number id](#game-number-id)
    - [Main game data](#main-game-data)
    - [Date and venue information](#date-and-venue-information)
    - [Date and time formats](#date-and-time-formats)
    - [Auxiliary data computed/extracted](#auxiliary-data-computedextracted)
    - [Unfished games](#unfished-games)
  - [Links \& Resources](#links--resources)
    - [API Services](#api-services)
    - [Other similar basketball stat systems/pages](#other-similar-basketball-stat-systemspages)
    - [Data visualization](#data-visualization)
  - [Contact \& Contributions](#contact--contributions)

## 1. Pre-requisites & setup

The system runs in Python 3.8+ as a Jupyter notebook or a standalone Python script.

Assuming Python is installed, install the required modules by running:

```shell
$ pip install -r requirements.txt
```

We also need the Firefox [Geckodriver](https://github.com/mozilla/geckodriver) to scrape web-pages (for extracting dates and venues of games):

```shell
$ sudo apt-get install firefox-geckodriver
```

This assumes you have the [Mozilla Team PPA](https://launchpad.net/~mozillateam/+archive/ubuntu/ppa) in your apt sources: `sudo add-apt-repository ppa:mozillateam/ppa`


The system has been developed with [VS Code](https://code.visualstudio.com/docs/datascience/jupyter-notebooks) and its [Jupyter extension](https://pypi.org/project/jupyter/).

Data is fetched from the [Genius Sports](https://news.geniussports.com/australian-national-basketball-league-extends-data-technology-partnership-with-genius-sports-group/) cloud service via their link `https://livestats.dcd.shared.geniussports.com/data`. Some relevant documentation can be found [here](https://support.geniussports.com/en/support/solutions/articles/9000008009-api-feed-overview-and-documentation),although it does not seem to be exactly that REST API.

The system will require:

1. setting the list `GAMES` with elements of the form `(game id, round number)`. Use [`extract_games`](extract_games.ipynb) notebook to extract those tuples from the NBL website. Define that variable in a separate file that will be imported into the system. Check examples `games_XX_YY.py` for various seasons.
2. a folder where files will be stored and read from. In particular, JSON files for each game scrapped will be saved in that folder as well as all the computed tables in various formats (i.e., CSV, Excel, Pickle).

## 2. How to use the notebook system

Open Jupyter notebook [bball_stats.ipynb](bball_stats.ipynb), via the browser (with a proper Juypter server running) or via an IDE like [VS Code](https://code.visualstudio.com/docs/datascience/jupyter-notebooks).

The notebook is self explanatory and the process is broken in steps.

The only section to set-up/change is **Section 1 (Configuration)** with the following information:

* `games`: list of games to scrape, by importing the corresponding game file defining variable `GAMES`.
* `DATA_DIR`: the folder where to save the output files (e.g., CSV files).
* `reload`: true if we want to re-load any games saved already from scratch.

After configuration, then notebook will scrape each game information (by downloading corresponding JSON files), compute the statistics, and finally save to file various tables (e.g., games, players, statistics).

The system will scrape all games available, stopping automatically in a round that is still incomplete (i.e., not all games available).

The saved tables can later be loaded so as to be further extended as new games are made available. This avoids re-computing past game stats.

## 3. How to use the standalone script

The system is also provided as a package module [nbl.nbl_scrapper](nbl/nbl_scrapper.py). To run it:

```shell
$ python -m nbl.nbl_scrapper --games games_22_23 --data data-22_23/ --save
```

Here `games_22_23.py` is the file defining the variable `GAMES` with the list of games to scrape, and `data-22_23/` is the folder used to read JSON files and store output tables. The option `--save` tells the script to update the new file tables.

### Setting it as a cron job

The script `run-scrape.sh` runs an update of the NBL stats and saves the corresponding files in a Google Drive folder. To do so it first mounts a Google Drive folder using [google-drive-ocamlfuse](https://github.com/astrada/google-drive-ocamlfuse/). To automate its running twice a week:

```cron
01 00 * * 7 /home/ssardina/ssardina-teaching/tools/pynbl.git/run-scrape.sh --save
01 00 * * 2 /home/ssardina/ssardina-teaching/tools/pynbl.git/run-scrape.sh --save
```

## 4. Development information

The process encoded in the Jupyter notebook and the modules under package `nbl` should be enough to understand the main functions implemented and the data computed, most of them as Pandas DataFrames. Script [`nbl.nbl_scrapper.py`](nbl/nbl_scrapper.py) basically implements the notebook offline.

We discuss below additional information that is useful to understand the system and may not be directly understandable from the source code.

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

The _date_ and _venue_ of a game is not part of the JSON data, so it is scraped from HTML pages (via [request](https://requests.readthedocs.io/en/latest/) and [BeautifulSoup](https://www.crummy.com/software/BeautifulSoup/bs4/doc/) Python packages, at the Firefox [geckodriver](https://github.com/mozilla/geckodriver)) using links of this form:

https://fibalivestats.dcd.shared.geniussports.com/u/NBL/1976446/

**NOTE:** Some other information seems to be available on other URLs, such as:

https://fibalivestats.dcd.shared.geniussports.com/data/competition/30249.json

Although it is not clear what `30249` means and how it can be obtained.

### Date and time formats

The _**game time**_ is tracked in format `MM:SS`, whereas the _**clock time**_ is tracked as `MM:SS:CC`, where `CC` is hundredths of a second. 

When a period starts, clock is "`10:00:00`" (that is, 10 min left).

### Auxiliary data computed/extracted

To compute the main tables, the system also extracts/computes, via various functions, the following information:

- **Game information**, including teams, scores, venue, and date.
- The **starting lineup** of a team.
- A **table of stints** for each team containing the lineup of players of each stint, the intervals and the number of minutes the stint was on court.
- A **play-by-play** DataFrame, with and without the stint id on each play for each team (denoting which lineups where on court at a play).

### Unfished games

Once in 2022-2023 league there was a game that has indeed finished but the play-by-play JSON files does not contain the last `game` event. Hence, when scrapping the JSON data file, the script believes the game is still being played. This is the final play-by-play recorded in the JSON file:

```json
    "pbp": [
        {
            "gt": "00:02",
            "clock": "00:02:40",
            "s1": 87,
            "s2": 84,
            "lead": 3,
            "tno": 1,
            "period": 4,
            "periodType": "REGULAR",
            "pno": 0,
            "player": "",
            "success": 1,
            "actionType": "rebound",
            "actionNumber": 835,
            "previousAction": 834,
            "qualifier": [
                "team"
            ],
            "subType": "defensive",
            "scoring": 0,
            "shirtNumber": ""
        },
        {
```

This is game `2224808` for the 2022-2023 season.

It is not clear what the best way to handle these buggy cases would be. For now, one can comment out the code recognising the end of the game (which looks for event "`game`"):

```python
        # assume no json file if game is not yet over!
        if not game_ended(game_json):
            raise ValueError('Game has not finished yet')
```


## Links & Resources

### API Services

- [Genius Sports Developer Centre](https://developer.geniussports.com/).
    - [Genius API - Overview and Documentation](https://support.geniussports.com/en/support/solutions/articles/9000008009-api-feed-overview-and-documentation).
  - [REST API Documentation](https://developer.geniussports.com/warehouse/rest/index_basketball.html).
  - Get all matches (but requires key!): https://api.wh.geniussports.com/v1/basketball/stream/matches
- Game information page: https://fibalivestats.dcd.shared.geniussports.com/u/NBL/<GAME_ID\>
- [NBL Game Fixture](https://nbl.com.au/fixture).
- [FIBA LiveStats V7](http://www.fibaorganizer.com/): a notebook-based software application to record basketball game statistics and webcast games in real time.
- [Best API](https://betsapi.com/l/1714/Australia-NBL): paid RESTful API.

### Other similar basketball stat systems/pages

* [euRobasketAu](https://github.com/jgalowe/euRobasketAu?organization=jgalowe&organization=jgalowe): a collection of R scripts to  scrape game data from [fibalivestats](http://www.fibaorganizer.com/) and calculate _advanced stats_. It is an adaptation of a system for European leagues and the system Py-nbl-stats is inspired on.
* [Basketball-reference.com](https://www.basketball-reference.com/players/g/ginobma01.html): an example of stats for each player, in this case Manu Ginobili. Can also check [Giannis Antetokounmpo](https://www.basketball-reference.com/players/a/antetgi01/lineups/2016) stats.


* [Cleaning-the-glass](https://cleaningtheglass.com/stats/guide/player_onoff): Players on/off explained.

### Data visualization

* [Public Tableau](https://public.tableau.com) can be used to visualize the data produced by this system, for example [here](https://public.tableau.com/app/profile/john5460/viz/NBL2021-22/CompareOnOff?publish=yes)
* Special graphs and charts can be done using [seaborn](https://seaborn.pydata.org/) and [matplotlib](https://matplotlib.org/). **[INCOMPLETE - TO DEVELOP]**

## Contact & Contributions

Developed by Sebastian Sardina (ssardina@gmail.com, [ssardina @ GitHub](https://github.com/ssardina)) with support from [jgalowe @ GitHub](https://github.com/jgalowe).

Based on [euRobasketAu](https://github.com/jgalowe/euRobasketAu?organization=jgalowe&organization=jgalowe) R-based scripts.

# Pynblstats: Python AUS Bball Statistic System

The scripts and notebooks in this repo allows to extract information and statistics from Basketball game data provided by [fibalivestats](http://www.fibaorganizer.com/) for the [NBL Australian Basketball](https://nbl.com.au/) competition.

The data is mostly provided as JSON files via a game-id number, and most of the information extracted is in the form of [Panda](https://pandas.pydata.org/) dataframes.

The **main system** is a Jupyter Notebook [bball_stats.ipynb](bball_stats.ipynb), which can be used to _incrementally_ construct (i.e., by extending previous results) statistical tables as games are played along the season. 

The output of this notebook is:

- a Pandas table with stats for each teams' _stint_ (e.g., lineup of players who played together in different intervals during the game).
- a Pandas table with games' information (e.g., team names, scores, date, venue, etc.).

The system can also extract, via various functions, the following information:

- A **table of stints** for each team containing the lineup of players of each stint, the intervals and the number of minutes the stint was on court.
- A **play-by-play** DataFrame, with and without the stint id on each play for each team (denoting which lineups where on court at a play).
- The **starting lineup** of a team.
- **Game information**, including teams, scores, venue, and date.

## 1. Pre-requisites

The system needs Python and Jupyter notebook, and requires at least `panda` and `dtale` packages:

```shell
$ pip install pandas dtale
```

For the doing plots and charts:

```shell
$ pip install matplotlib seaborn 
```

The system has been developed with [VS Code](https://code.visualstudio.com/docs/datascience/jupyter-notebooks) and its [Jupyter extension](https://pypi.org/project/jupyter/).

## 2. How to use it

The basic system is in Jupyter notebook [bball_stats.ipynb](bball_stats.ipynb). This can be opened and used via the browser (with a proper Juypter server running) or better via [VS Code](https://code.visualstudio.com/docs/datascience/jupyter-notebooks).

The data computed are:

- `stats_df`: a Pandas DataFrame (i.e., table) with all statistics per team stints in games.
- `games_df`: a Pandas DataFrame with games's scraped.
- `pbp_df`: a Pandas DataFrame containing all play-by-play data.

The steps are as follows:

1. **Define the new games** to be scraped and computed, together with the files where existing previous data (stats and games) has been saved.
   * Each game needs a game-id, and the game numbers for each team.
2. **Run the system** to compute new stats and games and append them with the existing saved ones (if any).
3. **Save updated stats and games** to file (for later incremental extension).

Note that, in order to be able to incrementally extend the existing database/tables as new games are played, the system starts by loading pre-saved tables, from files `file_stats_df` and `games_stats_df`.

It will then scrape all games defined in list `games`, one by one, will compute the stint stats and the game info.

The new tables are the initial tables plus the new games and stats.

Finally, it is possible to materialize (i.e., save) the new updated tables to file. This will avoid re-computing the stats for all the old games.

## 3. Development info

### JSON game data via Fibalivestats

**Game data** as JSON file is provided by link:

https://fibalivestats.dcd.shared.geniussports.com/data/XXXXXXX/data.json

where `XXXXXXX` refers to the game id. This game id can be obtained from the NBL link, for example for game id `2087737`:

https://nbl.com.au/games/2087737

The service seems to be provided by [Genius Sports ](https://developer.geniussports.com/), which also provides _livestream data feed_, but seems to require an API key via registration. Developer info can be found [here](https://developer.geniussports.com/livestats/tvfeed/index_basketball.html); see also links below.

The date and venue of a game is scraped from HTML pages (via [request](https://requests.readthedocs.io/en/latest/) and [BeautifulSoup](https://www.crummy.com/software/BeautifulSoup/bs4/doc/) Python packages) using links of this form:

https://fibalivestats.dcd.shared.geniussports.com/u/NBL/1976446/

**NOTE:** Some other information seems to be available on other URLs, such as:

https://fibalivestats.dcd.shared.geniussports.com/data/competition/30249.json

Although it is not clear what `30249` means and how it can be obtained.

### JSON Data format

**[INCOMPLETE]**

| ID            | Description | Format | Type |
| -----------   | ----------- | ------ | ---- |
| `gt`          | Game time | `datetime.time`  | `MM:SS`
| `clock`       | Clock time    | `datetime.time`   | `MM:SS:CC`
| `s1`       | Score team 1 | `int`
| `s2`       | Score team 2 | `int`

where:

- `MM:SS:CC`, where `CC` is hundredths of a second. When a period starts, lock is "`10:00:00`" (10 min left).

### Statistics Fields

Various advanced statistics are calculated from play-by-play. These are used at this point for assessing **stint lineups**, but will be extended to do On/Off, Shooting, Splits, and other interesting statistical settings.

A good example of statistic fields and settings that can be done can be found here:

https://www.basketball-reference.com/players/a/antetgi01/lineups/2016

## 4. API Services

### Genius Sports

- [Genius Sports Developer Centre](https://developer.geniussports.com/).
    - [Genius API - Overview and Documentation](https://support.geniussports.com/en/support/solutions/articles/9000008009-api-feed-overview-and-documentation).
  - [REST API Documentation](https://developer.geniussports.com/warehouse/rest/index_basketball.html).
  - Get all matches (but requires key!): https://api.wh.geniussports.com/v1/basketball/stream/matches

## Other APIs and pages

- Game information page: https://fibalivestats.dcd.shared.geniussports.com/u/NBL/\<GAME_ID\>
- [NBL Game Fixture](https://nbl.com.au/fixture).
- [FIBA LiveStats V7](http://www.fibaorganizer.com/): a notebook-based software application to record basketball game statistics and webcast games in real time.
- [Best API](https://betsapi.com/l/1714/Australia-NBL): paid RESTful API.

## Other similar systems

* [Rscript repo](https://github.com/jgalowe/euRobasketAu?organization=jgalowe&organization=jgalowe) that I use right now if it is of any use to you:

It scrapes the data and then converts the raw numbers into _advanced stats_.

And here is a link to the tableau dashboard (doesn't look very nice, I'm the only person who uses it):

https://public.tableau.com/app/profile/john5460/viz/NBL2021-22/CompareOnOff?publish=yes

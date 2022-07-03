# Pynblstats: Python AUS Bball Statistic System

These scripts will collect the data (as JSON data) from one more more games from [fibalivestats](http://www.fibaorganizer.com/) and produce:

- a [Panda](https://pandas.pydata.org/) Dataframe with stats for each teams' stint (e.g., lineup of players who played together in different intervals during the game).
- a [Panda](https://pandas.pydata.org/) Dataframe  with games' information (e.g., team names, scores).

The system can also provide:

- A **table of stints** for each team containing the lineup of players of each stint, the intervals and the number of minutes the stint was on court.
- A **play-by-play** DataFrame, with and without the stint id on each play for each team (denoting which lineups where on court at a play).
- The **starting lineup** of a team.

## Pre-requisites

The script runs on Python and requires `panda` and `dtale`:

```shell
$ pip install pandas dtale
```

For the doing plots and charts:

```shell
$ pip install matplotlib seaborn 
```

The system has been developed with [VS Code](https://code.visualstudio.com/docs/datascience/jupyter-notebooks) and its [Jupyter extension](https://pypi.org/project/jupyter/).

## How to use it

The basic system is in Jupyter notebook [bball_stats.ipynb](bball_stats.ipynb). This can be opened and used via the browser (with a proper Juypter server running) or better via [VS Code](https://code.visualstudio.com/docs/datascience/jupyter-notebooks).

The data computed are:

- `stats_df`: a Pandas DataFrame (i.e., table) with all statistics per team stints in games.
- `games_df`: a Pandas DataFrame (i.e., table) with games's scraped.

The steps are as follows:

1. **Define the new games** to be scraped and computed, together with the files where existing previous data (stats and games) has been saved.
   * Each game needs a game-id, and the game numbers for each team.
2. **Run the system** to compute new stats and games and append them with the existing saved ones (if any).
3. **Save updated stats and games** to file (for later incremental extension).

Note that, in order to be able to incrementally extend the existing database/tables as new games are played, the system starts by loading pre-saved tables, from files `file_stats_df` and `games_stats_df`.

It will then scrape all games defined in list `games`, one by one, will compute the stint stats and the game info.

The new tables are the initial tables plus the new games and stats.

Finally, it is possible to materialize (i.e., save) the new updated tables to file. This will avoid re-computing the stats for all the old games.

## Development info

### JSON game data via Fibalivestats

Game data is provided by link:

https://fibalivestats.dcd.shared.geniussports.com/data/XXXXXXX/data.json

where `XXXXXXX` refers to the game id. This game id can be obtained from the NBL link, for example for game id `2087737`:

https://nbl.com.au/games/2087737

The service seems to be provided by [Genius Sports ](https://developer.geniussports.com/), which also provides _livestream data feed_, but seems to require an API key via registration. Developer info can be found [here](https://developer.geniussports.com/livestats/tvfeed/index_basketball.html); see also links below.

### Data format

| ID            | Description | Format | Type |
| -----------   | ----------- | ------ | ---- |
| `gt`          | Game time | `datetime.time`  | `MM:SS`
| `clock`       | Clock time    | `datetime.time`   | `MM:SS:CC`
| `s1`       | Score team 1 | `int`
| `s2`       | Score team 2 | `int`

where:

- `MM:SS:CC`, where `CC` is hundredths of a second. When a period starts, lock is "`10:00:00`" (10 min left).

## Related links

### APIs

- [NBL Game Fixture](https://nbl.com.au/fixture).
- [FIBA LiveStats V7](http://www.fibaorganizer.com/): a notebook-based software application to record basketball game statistics and webcast games in real time.
  - [Genius Sports Developer Centre](https://developer.geniussports.com/).
    - [Genius API - Overview and Documentation](https://support.geniussports.com/en/support/solutions/articles/9000008009-api-feed-overview-and-documentation).
  - [REST API Documentation](https://developer.geniussports.com/warehouse/rest/index_basketball.html).
  - Get all matches (but requires key!): https://api.wh.geniussports.com/v1/basketball/stream/matches
- [Best API](https://betsapi.com/l/1714/Australia-NBL): paid RESTful API.

### Data analytic systems

Here is a link to the [Rscript repo](https://github.com/jgalowe/euRobasketAu?organization=jgalowe&organization=jgalowe) that I use right now if it is of any use to you:

It scrapes the data and then converts the raw numbers into _advanced stats_.

And here is a link to the tableau dashboard (doesn't look very nice, I'm the only person who uses it):

https://public.tableau.com/app/profile/john5460/viz/NBL2021-22/CompareOnOff?publish=yes

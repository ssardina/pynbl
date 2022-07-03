# Pynblstats: Python AUS Bball Statistic System

## JSON game data via Fibalivestats

Game data is provided by link:

https://fibalivestats.dcd.shared.geniussports.com/data/XXXXXXX/data.json

where `XXXXXXX` refers to the game id. This game id can be obtained from the NBL link, for example for game id `2087737`:

https://nbl.com.au/games/2087737

The service seems to be provided by [Genius Sports ](https://developer.geniussports.com/), which also provides _livestream data feed_, but seems to require an API key via registration. Developer info can be found [here](https://developer.geniussports.com/livestats/tvfeed/index_basketball.html); see also links below.

## Data format

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
- [Genius Sports Developmer Centre](https://developer.geniussports.com/).
  - [Genius API - Overview and Documentation](https://support.geniussports.com/en/support/solutions/articles/9000008009-api-feed-overview-and-documentation
  - [REST API Documentation](https://developer.geniussports.com/warehouse/rest/index_basketball.html).
  - Get all matches (but requires key!): https://api.wh.geniussports.com/v1/basketball/stream/matches
- [Best API](https://betsapi.com/l/1714/Australia-NBL): paid RESTful API.

### Data analytic systems

Here is a link to the [Rscript repo](https://github.com/jgalowe/euRobasketAu?organization=jgalowe&organization=jgalowe) that I use right now if it is of any use to you:

It scrapes the data and then converts the raw numbers into _advanced stats_.

And here is a link to the tableau dashboard (doesn't look very nice, I'm the only person who uses it):

https://public.tableau.com/app/profile/john5460/viz/NBL2021-22/CompareOnOff?publish=yes

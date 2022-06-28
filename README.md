# Basketball Statistics

## Data

The data is provided live by [Genius Sports ](https://developer.geniussports.com/).

The documentation for the Basketball feed can be found [here](https://developer.geniussports.com/livestats/tvfeed/index_basketball.html).

Messages are sent in JSON structures and use UTF-8 format.

An example of a raw JSON file:

https://fibalivestats.dcd.shared.geniussports.com/data/2087737/data.json

However that JSON files does not seem to match the above doc... :-)

## Data analytic systems

Here is a link to the [Rscript repo](https://github.com/jgalowe/euRobasketAu?organization=jgalowe&organization=jgalowe) that I use right now if it is of any use to you:

It scrapes the data and then converts the raw numbers into _advanced stats_.

And here is a link to the tableau dashboard (doesn't look very nice, I'm the only person who uses it):

https://public.tableau.com/app/profile/john5460/viz/NBL2021-22/CompareOnOff?publish=yes

## Data format

| ID            | Description | Format | Type |
| -----------   | ----------- | ------ | ---- |
| `gt`          | Game time | `Timedelta`  | `MM:SS`
| `clock`       | Clock time    | `Timedelta`   | `MM:SS:CC`
| `s1`       | Score team 1 | `int`
| `s2`       | Score team 2 | `int`

where:

- `MM:SS:CC`, where `CC` is hundredths of a second. When a period starts, lock is "`10:00:00`" (10 min left).

### Other information on format

* `gt` and `clock_time`. We used [Timestamp](https://pandas.pydata.org/docs/reference/api/pandas.Timestamp.html), the Pandas version of Datetime.
  * One could also consider using [Timedelta](https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.to_timedelta.html).
  * `clock time` uses `MM:SS:CC` where `CC` is hundredths of seconds, which is read as microseconds. So `00:05:10` is 00:00:05.100` which is correct.
  * We can use `.dt.time` on a `datetime` to extract just the time.
  * We can eventually do  `errors=coerece` to get `NaN` on errors.
## Questions

- Where is the format documented?


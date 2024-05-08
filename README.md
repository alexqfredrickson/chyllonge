# chyllonge

A Python 3.8+ implementation of [the challonge.com API](https://api.challonge.com/v1).

## Prerequisites

`chyllonge` requires that the `CHALLONGE_KEY` and `CHALLONGE_USER` environment variables are set.

* `CHALLONGE_USER` is your `challonge.com` username.
* `CHALLONGE_KEY` is your `challonge.com` API key.  An API key can be generated [here](https://challonge.com/settings/developer).

`chyllonge` also allows a `CHALLONGE_IANA_TZ_NAME` environment variable, which accepts an 
[IANA-compliant time zone name](https://data.iana.org/time-zones/tzdb-2021a/zone1970.tab) - for 
example: `Europe/Berlin`.

## Installation

To install `chyllonge`, execute `pip install chyllonge`.

## Usage

Detailed API documentation is available at https://api.challonge.com/v1.

```python
from chyllonge.api import ChallongeAPI
from datetime import datetime, timedelta

api = ChallongeAPI()

# create a basic tournament
tournament = api.tournaments.create(name="My Chyllonge Tournament")
print(tournament["id"])

# create a tournament that starts in an hour
an_hour_from_now = (datetime.now() + timedelta(hours=1)).isoformat() + api.http.tz_utc_offset_string
tournament = api.tournaments.create(name="My Chyllonge Tournament", start_at=an_hour_from_now, check_in_duration=60)
print(tournament["id"])

# create a tournament, add Alice and Bob, process their check-ins, start the tournment, set their match underway,
# score their match (congratulations Alice!), finalize the tournament
an_hour_from_now = (datetime.now() + timedelta(hours=1)).isoformat() + api.http.tz_utc_offset_string
tournament = api.tournaments.create(name="Alice and Bob Play Bingo", start_at=an_hour_from_now, check_in_duration=60)

api.participants.add(tournament["id"], name="Alice")
api.participants.add(tournament["id"], name="Bob")

api.tournaments.process_checkins(tournament["id"])
api.tournaments.start(tournament["id"])

match = api.matches.get_all(tournament_id=tournament["id"])[0]
alice = api.participants.get_all(tournament["id"])[0]

api.matches.set_underway(tournament["id"], match["id"])
api.matches.update(tournament["id"], match["id"], match_scores_csv="3-1,2-2", match_winner_id=alice["id"])

api.tournaments.finalize(tournament["id"])

finished_tournment = api.tournaments.get(tournament["id"])
```

## History

`chyllonge` was inspired by `pychallonge` - developed by Russ Amos - which (in turn) includes `pychal`. 

See `CONTRIBUTORS.txt` for the original authors.

## Testing

To run local tests, run `python -m unittest tests/tests.py`.

Note that the unit tests will create tournaments in your account, called `chyllonge-temp`.  It will try to delete them 
afterward, but automated cleanup is not always guaranteed.

## Contributing

Please feel free to contribute, and to suggest updates to these contribution guidelines!

The current guidelines are:

* Functions should be documented in-line using `reStructuredText` format.
* Support for older Python versions should be dropped as those minor updates approach end-of-life.
* There are no plans to support XML for the time being (although this is a nice-to-have).

## Building

`chyllonge` is built using [`flit`](https://flit.pypa.io/en/stable/) and [`build`](https://build.pypa.io/en/stable/).

## Releases

New versions of `chyllonge` are released to PyPI with the help of a GitHub Action workflow, which:

1. Updates the `pyproject.toml` version
2. Creates a GitHub release
3. Invokes `build`, which publishes to PyPI

### Non-frequently Asked Questions

**Q: How do you pronounce `chyllonge`?**

**A:** Like "chill-ahnge".

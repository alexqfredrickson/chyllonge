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

```python
from chyllonge import TournamentAPI

# create a tournament
tournaments_api = TournamentAPI()

from datetime import datetime, timedelta

tournament = tournaments_api.create(
    name="chyllonge-temp",
    start_at=(datetime.now() + timedelta(hours=1)).isoformat() + "-5:00",
    check_in_duration=60
)

print(tournament["tournament"]["id"])
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

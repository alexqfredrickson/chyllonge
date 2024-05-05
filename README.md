# chyllonge

A Python 3.8+ implementation of [the challonge.com API](https://api.challonge.com/v1).

## Prerequisites

`chyllonge` requires that the `CHALLONGE_KEY` and `CHALLONGE_USER` environment variables are set.

* `CHALLONGE_USER` is your `challonge.com` username.
* `CHALLONGE_KEY` is your `challonge.com` API key.  An API key can be generated [here](https://challonge.com/settings/developer).

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

To run local tests, run `python -m unittest tests.py`.

Note that the unit tests will create tournaments in your account, called `chyllonge-temp`.  It will try to delete them 
afterward, but automated cleanup is not always guaranteed.

### Non-frequently Asked Questions

Q: _How do you pronounce `chyllonge`_?

A: Like "chill-ahnge".
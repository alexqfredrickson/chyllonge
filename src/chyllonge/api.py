import os
import ast
import json
import zoneinfo
from datetime import datetime

from typing import List

import tzlocal
import requests


class ChallongeAPIException(Exception):
    # raise ChallongeAPIException('foo bar baz buzz')
    pass


class ChallongeAPINotImplementedException(Exception):
    # raise ChallongeAPIException('foo bar baz buzz')
    pass


class ChallongeApi:

    def __init__(self):
        self.http = ChallongeApiHttpMethods()

        self.tournaments = TournamentAPI(self.http)
        self.matches = MatchAPI(self.http)
        self.participants = ParticipantAPI(self.http)
        self.attachments = AttachmentAPI(self.http)

    def get_heartbeat(self):
        """
        Invokes the most basic kind of API request.
        """

        response = requests.get(
            self.http.base_challonge_url,
            headers=self.http.user_agent_param,
            auth=self.http.basic_auth_param
        )

        if response.status_code != 200:
            raise ChallongeAPIException(f"ERROR: {', '.join([e for e in json.loads(response.text)['errors']])}")

        return response.text


class ChallongeApiHttpMethods:

    def __init__(self):
        self.user = os.environ["CHALLONGE_USER"]
        self.key = os.environ["CHALLONGE_KEY"]

        if not self.user:
            raise ChallongeAPIException(
                'ERROR: No API username was defined in the CHALLONGE_USER system environment variable.'
            )

        if not self.key:
            raise ChallongeAPIException(
                'ERROR: No API key was defined in the CHALLONGE_KEY system environment variable.'
            )

        self.basic_auth_param = (self.user, self.key)

        if "CHALLONGE_IANA_TZ_NAME" in os.environ:
            self.timezone = zoneinfo.ZoneInfo(os.environ["CHALLONGE_IANA_TZ_NAME"])
        else:
            self.timezone = tzlocal.get_localzone()

        if not self.timezone:
            raise ChallongeAPIException(
                'ERROR: The local timezone could not be ascertained. This may create issues.'
            )

        self.now = datetime.now(tz=self.timezone)
        self.tz_utc_offset = self.now.strftime('%z')
        self.tz_utc_offset_string = self.tz_utc_offset[0:-2] + ":" + self.tz_utc_offset[-2:]

        # note that the user agent string is required to get around Cloudflare issues
        self.user_agent_param = {"User-Agent": "chyllonge"}

        self.base_challonge_url = "https://api.challonge.com/v1/"

    def get(self, api_suffix='', params=None):
        response = requests.get(
            self.base_challonge_url + api_suffix,
            headers=self.user_agent_param,
            auth=self.basic_auth_param,
            params=params
        )

        if response.status_code != 200:
            raise ChallongeAPIException(f"ERROR: {', '.join([e for e in json.loads(response.text)['errors']])}")

        return json.loads(response.text)

    def post(self, api_suffix, params=None):
        response = requests.post(
            self.base_challonge_url + api_suffix,
            headers=self.user_agent_param,
            auth=self.basic_auth_param,
            data=params
        )

        if response.status_code != 200:

            if response.status_code == 401:

                errors = response.text if "HTTP Basic" in response.text else ', '.join(
                    [e for e in json.loads(response.text)['errors']]
                )

                raise ChallongeAPIException(
                    f"ERROR: Access was denied. Ensure that the local CHALLONGE_USER and CHALLONGE_KEY "
                    f"environment variables are set. See https://challonge.com/settings/developer for more information."
                    f" {errors}"
                )

            else:
                raise ChallongeAPIException(
                    f"ERROR: {self.base_challonge_url + api_suffix} | "
                    f"{ast.literal_eval(response.content.decode('utf-8'))}"
                )

        return json.loads(response.text)

    def put(self, api_suffix, params=None):
        response = requests.put(
            self.base_challonge_url + api_suffix,
            headers=self.user_agent_param,
            auth=self.basic_auth_param,
            data=params
        )

        if response.status_code != 200:
            raise ChallongeAPIException(f"ERROR: {', '.join([e for e in json.loads(response.text)['errors']])}")

        return json.loads(response.text)

    def delete(self, api_suffix, params=None):
        response = requests.delete(
            self.base_challonge_url + api_suffix,
            headers=self.user_agent_param,
            auth=self.basic_auth_param,
            params=params
        )

        if response.status_code != 200:
            raise ChallongeAPIException(f"ERROR: {', '.join([e for e in json.loads(response.text)['errors']])}")

        return json.loads(response.text)


class TournamentAPI:

    def __init__(self, http_methods):
        self.http = http_methods
        self.participant_api = ParticipantAPI(self.http)  # special case for a built-in sanity check

    def get_all(self, state: str = None, tournament_type: str = None, created_after: str = None,
                created_before: str = None, subdomain=None):
        """
        Retrieve a set of tournaments created with your account.

        :param state: all, pending, in_progress, ended
        :param tournament_type: single_elimination, double_elimination, round_robin, swiss
        :param created_after: A YYYY-MM-DD string.
        :param created_before: A YYYY-MM-DD string.
        :param subdomain: A Challonge subdomain you've published tournaments to. NOTE: Until v2 of our API, the
                    subdomain parameter is required to retrieve a list of your organization-hosted tournaments.
        """

        if subdomain:
            raise ChallongeAPINotImplementedException

        params = {
            "state": state,
            "tournament_type": tournament_type,
            "created_after": created_after,
            "created_before": created_before
        }

        response = self.http.get("tournaments.json", params=params)

        tournaments = [t["tournament"] for t in response]

        return tournaments

    def create(self, name: str = None, tournament_type: str = None, url: str = None, subdomain: str = None,
               description: str = None, open_signup: bool = None, hold_third_place_match: bool = None,
               pts_for_match_win: float = None, pts_for_match_tie: float = None,
               pts_for_game_win: float = None, pts_for_game_tie: float = None, pts_for_bye: float = None,
               swiss_rounds: int = None, ranked_by: str = None, rr_pts_for_match_win: float = None,
               rr_pts_for_match_tie: float = None, rr_pts_for_game_win: float = None,
               rr_pts_for_game_tie: float = None, accept_attachments: bool = None,
               hide_forum: bool = None, show_rounds: bool = None, private: bool = None,
               notify_users_when_matches_open: bool = None, notify_users_when_the_tournament_ends: bool = None,
               sequential_pairings: bool = None, signup_cap: int = None, start_at: str = None,
               check_in_duration: int = None, grand_finals_modifier=None, prediction_method: int = None):
        """
        Create a new tournament.

        :param name: Your event's name/title (Max: 60 characters)
        :param tournament_type: Single elimination (default), double elimination, round robin, swiss
        :param url: challonge.com/url (letters, numbers, and underscores only); when blank on create, a random URL
        will be generated for you
        :param subdomain: subdomain.challonge.com/url (Requires write access to the specified subdomain)
        :param description: Description/instructions to be displayed above the bracket
        :param open_signup: True or false. Have Challonge host a sign-up page (otherwise, you manually add all
        participants)
        :param hold_third_place_match: True or false - Single Elimination only. Include a match between semifinal
        losers? (default: false)
        :param pts_for_match_win: Decimal (to the nearest tenth) - Swiss only - default: 1.0
        :param pts_for_match_tie: Decimal (to the nearest tenth) - Swiss only - default: 0.5
        :param pts_for_game_win: Decimal (to the nearest tenth) - Swiss only - default: 0.0
        :param pts_for_game_tie: Decimal (to the nearest tenth) - Swiss only - default: 0.0
        :param pts_for_bye: Decimal (to the nearest tenth) - Swiss only - default: 1.0
        :param swiss_rounds: Integer - Swiss only - We recommend limiting the number of rounds to less than
        two-thirds the number of players. Otherwise, an impossible pairing situation can be reached and your
        tournament may end before the desired number of rounds are played.
        :param ranked_by: One of the following: 'match wins', 'game wins', 'points scored', 'points difference',
        'custom' Help
        :param rr_pts_for_match_win: Decimal (to the nearest tenth) - Round Robin "custom only" - default: 1.0
        :param rr_pts_for_match_tie: Decimal (to the nearest tenth) - Round Robin "custom" only - default: 0.5
        :param rr_pts_for_game_win: Decimal (to the nearest tenth) - Round Robin "custom" only - default: 0.0
        :param rr_pts_for_game_tie: Decimal (to the nearest tenth) - Round Robin "custom" only - default: 0.0
        :param accept_attachments: True or false - Allow match attachment uploads (default: false)
        :param hide_forum: True or false - Hide the forum tab on your Challonge page (default: false)
        :param show_rounds: True or false - Single &amp; Double Elimination only - Label each round above the
        bracket (default: false)
        :param private: True or false - Hide this tournament from the public browsable index and your profile
        (default: false)
        :param notify_users_when_matches_open: True or false - Email registered Challonge participants when matches
        open up for them (default: false)
        :param notify_users_when_the_tournament_ends: True or false - Email registered Challonge participants the
        results when this tournament ends (default: false)
        :param sequential_pairings: True or false - Instead of traditional seeding rules, make pairings by going
        straight down the list of participants. First round matches are filled in top to bottom, then qualifying
        matches (if applicable). (default: false)
        :param signup_cap: Integer - Maximum number of participants in the bracket. A waiting list (attribute on
        Participant) will capture participants once the cap is reached.
        :param start_at: Datetime - the planned or anticipated start time for the tournament (Used with
        check_in_duration to determine participant check-in window). Timezone defaults to Eastern.
        :param check_in_duration: Integer - Length of the participant check-in window in minutes.
        :param grand_finals_modifier: String - This option only affects double elimination. null/blank (default) -
        give the winners bracket finalist two chances to beat the losers bracket finalist, 'single match' -
        create only one grand finals match, 'skip' - don't create a finals match between winners and losers
        bracket finalists
        :param prediction_method: Integer - This is undocumented.
        """

        if subdomain:
            raise ChallongeAPINotImplementedException

        params = {
            "tournament[name]": name,
            "tournament[tournament_type]": tournament_type,
            "tournament[url]": url,
            "tournament[subdomain]": subdomain,
            "tournament[description]": description,
            "tournament[open_signup]": "true" if open_signup else "false",
            "tournament[hold_third_place_match]": "true" if hold_third_place_match else "false",
            "tournament[pts_for_match_win]": pts_for_match_win,
            "tournament[pts_for_match_tie]": pts_for_match_tie,
            "tournament[pts_for_game_win]": pts_for_game_win,
            "tournament[pts_for_game_tie]": pts_for_game_tie,
            "tournament[pts_for_bye]": pts_for_bye,
            "tournament[swiss_rounds]": swiss_rounds,
            "tournament[ranked_by]": ranked_by,
            "tournament[rr_pts_for_match_win]": rr_pts_for_match_win,
            "tournament[rr_pts_for_match_tie]": rr_pts_for_match_tie,
            "tournament[rr_pts_for_game_win]": rr_pts_for_game_win,
            "tournament[rr_pts_for_game_tie]": rr_pts_for_game_tie,
            "tournament[accept_attachments]": "true" if accept_attachments else "false",
            "tournament[hide_forum]": "true" if hide_forum else "false",
            "tournament[show_rounds]": "true" if show_rounds else "false",
            "tournament[private]": "true" if private else "false",
            "tournament[notify_users_when_matches_open]": "true" if notify_users_when_matches_open else "false",
            "tournament[notify_users_when_the_tournament_ends]":
                "true" if notify_users_when_the_tournament_ends else "false",
            "tournament[sequential_pairings]": "true" if sequential_pairings else "false",
            "tournament[signup_cap]": signup_cap,
            "tournament[start_at]": start_at,
            "tournament[check_in_duration]": check_in_duration,
            "tournament[grand_finals_modifier]": grand_finals_modifier,
            "tournament[prediction_method]": prediction_method,
        }

        response = self.http.post("tournaments.json", params)

        tournament = response["tournament"]

        return tournament

    def get(self, tournament_id: str, include_participants: int = None, include_matches: int = None):
        """
        Retrieve a single tournament record created with your account.

        :param tournament_id: Tournament ID (e.g. 10230) or URL (e.g. 'single_elim' for challonge.com/single_elim).
        If assigned to a subdomain, URL format must be :subdomain-:tournament_url (e.g. 'test-mytourney'
        for test.challonge.com/mytourney)
        :param include_participants: 0 or 1; includes an array of associated participant records
        :param include_matches: 0 or 1; includes an array of associated match records
        """

        if not tournament_id:
            raise ChallongeAPIException("ERROR: A tournament ID is required.")

        params = {
            "include_participants": include_participants,
            "include_matches": include_matches
        }

        response = self.http.get(f"tournaments/{tournament_id}.json", params=params)

        tournament = response["tournament"]

        return tournament

    def update(self, tournament_id: str, name: str = None, tournament_type: str = None,
               url: str = None, subdomain: str = None, description: str = None, open_signup: bool = None,
               hold_third_place_match: bool = None, pts_for_match_win: float = None,
               pts_for_match_tie: float = None, pts_for_game_win: float = None,
               pts_for_game_tie: float = None, pts_for_bye: float = None, swiss_rounds: int = None,
               ranked_by: str = None, rr_pts_for_match_win: float = None,
               rr_pts_for_match_tie: float = None, rr_pts_for_game_win: float = None,
               rr_pts_for_game_tie: float = None, accept_attachments: bool = None,
               hide_forum: bool = None, show_rounds: bool = None, private: bool = None,
               notify_users_when_matches_open: bool = None, notify_users_when_the_tournament_ends: bool = None,
               sequential_pairings: bool = None, signup_cap: int = None, start_at: str = None,
               check_in_duration: int = None, grand_finals_modifier=None, prediction_method: int = None):
        """
        Update a tournament's attributes.

        :param tournament_id: A tournament ID.
        :param name: Your event's name/title (Max: 60 characters)
        :param tournament_type: Single elimination (default), double elimination, round robin, swiss
        :param url: challonge.com/url (letters, numbers, and underscores only); when blank on create, a random URL
        will be generated for you
        :param subdomain: subdomain.challonge.com/url (Requires write access to the specified subdomain)
        :param description: Description/instructions to be displayed above the bracket
        :param open_signup: True or false. Have Challonge host a sign-up page (otherwise, you manually add all
        participants)
        :param hold_third_place_match: True or false - Single Elimination only. Include a match between semifinal
        losers? (default: false)
        :param pts_for_match_win: Decimal (to the nearest tenth) - Swiss only - default: 1.0
        :param pts_for_match_tie: Decimal (to the nearest tenth) - Swiss only - default: 0.5
        :param pts_for_game_win: Decimal (to the nearest tenth) - Swiss only - default: 0.0
        :param pts_for_game_tie: Decimal (to the nearest tenth) - Swiss only - default: 0.0
        :param pts_for_bye: Decimal (to the nearest tenth) - Swiss only - default: 1.0
        :param swiss_rounds: Integer - Swiss only - We recommend limiting the number of rounds to less than
        two-thirds the number of players. Otherwise, an impossible pairing situation can be reached and your
        tournament may end before the desired number of rounds are played.
        :param ranked_by: One of the following: 'match wins', 'game wins', 'points scored', 'points difference',
        'custom' Help
        :param rr_pts_for_match_win: Decimal (to the nearest tenth) - Round Robin "custom only" - default: 1.0
        :param rr_pts_for_match_tie: Decimal (to the nearest tenth) - Round Robin "custom" only - default: 0.5
        :param rr_pts_for_game_win: Decimal (to the nearest tenth) - Round Robin "custom" only - default: 0.0
        :param rr_pts_for_game_tie: Decimal (to the nearest tenth) - Round Robin "custom" only - default: 0.0
        :param accept_attachments: True or false - Allow match attachment uploads (default: false)
        :param hide_forum: True or false - Hide the forum tab on your Challonge page (default: false)
        :param show_rounds: True or false - Single &amp; Double Elimination only - Label each round above the
        bracket (default: false)
        :param private: True or false - Hide this tournament from the public browsable index and your profile
        (default: false)
        :param notify_users_when_matches_open: True or false - Email registered Challonge participants when matches
        open up for them (default: false)
        :param notify_users_when_the_tournament_ends: True or false - Email registered Challonge participants the
        results when this tournament ends (default: false)
        :param sequential_pairings: True or false - Instead of traditional seeding rules, make pairings by going
        straight down the list of participants. First round matches are filled in top to bottom, then qualifying
        matches (if applicable). (default: false)
        :param signup_cap: Integer - Maximum number of participants in the bracket. A waiting list (attribute on
        Participant) will capture participants once the cap is reached.
        :param start_at: Datetime - the planned or anticipated start time for the tournament (Used with
        check_in_duration to determine participant check-in window). Timezone defaults to Eastern.
        :param check_in_duration: Integer - Length of the participant check-in window in minutes.
        :param grand_finals_modifier: String - This option only affects double elimination. null/blank (default) -
        give the winners bracket finalist two chances to beat the losers bracket finalist, 'single match' -
        create only one grand finals match, 'skip' - don't create a finals match between winners and losers
        bracket finalists
        :param prediction_method: Integer - This is undocumented.
        """

        if subdomain:
            raise ChallongeAPINotImplementedException

        params = {
            "tournament[name]": name,
            "tournament[tournament_type]": tournament_type,
            "tournament[url]": url,
            "tournament[subdomain]": subdomain,
            "tournament[description]": description,
            "tournament[open_signup]": "true" if open_signup else "false",
            "tournament[hold_third_place_match]": "true" if hold_third_place_match else "false",
            "tournament[pts_for_match_win]": pts_for_match_win,
            "tournament[pts_for_match_tie]": pts_for_match_tie,
            "tournament[pts_for_game_win]": pts_for_game_win,
            "tournament[pts_for_game_tie]": pts_for_game_tie,
            "tournament[pts_for_bye]": pts_for_bye,
            "tournament[swiss_rounds]": swiss_rounds,
            "tournament[ranked_by]": ranked_by,
            "tournament[rr_pts_for_match_win]": rr_pts_for_match_win,
            "tournament[rr_pts_for_match_tie]": rr_pts_for_match_tie,
            "tournament[rr_pts_for_game_win]": rr_pts_for_game_win,
            "tournament[rr_pts_for_game_tie]": rr_pts_for_game_tie,
            "tournament[accept_attachments]": "true" if accept_attachments else "false",
            "tournament[hide_forum]": "true" if hide_forum else "false",
            "tournament[show_rounds]": "true" if show_rounds else "false",
            "tournament[private]": "true" if private else "false",
            "tournament[notify_users_when_matches_open]": "true" if notify_users_when_matches_open else "false",
            "tournament[notify_users_when_the_tournament_ends]":
                "true" if notify_users_when_the_tournament_ends else "false",
            "tournament[sequential_pairings]": "true" if sequential_pairings else "false",
            "tournament[signup_cap]": signup_cap,
            "tournament[start_at]": start_at,
            "tournament[check_in_duration]": check_in_duration,
            "tournament[grand_finals_modifier]": grand_finals_modifier,
            "tournament[prediction_method]": prediction_method,
        }

        response = self.http.put(f"tournaments/{tournament_id}.json", params=params)

        tournament = response["tournament"]

        return tournament

    def delete(self, tournament_id: str):
        """
        Deletes a tournament along with all its associated records. There is no undo, so use with care!

        :param tournament_id: A tournament ID.
        """

        response = self.http.delete(f"tournaments/{tournament_id}.json")

        tournament = response["tournament"]

        return tournament

    def process_checkins(self, tournament_id: str, include_participants: int = None,
                         include_matches: int = None):
        """
        This should be invoked after a tournament's check-in window closes before the tournament is started.

            - Marks participants who have not checked in as inactive.
            - Moves inactive participants to bottom seeds (ordered by original seed).
            - Transitions the tournament state from 'checking_in' to 'checked_in'

        NOTE: Checked in participants on the waiting list will be promoted if slots become available.

        :param tournament_id: Tournament ID (e.g. 10230) or URL (e.g. 'single_elim' for challonge.com/single_elim).
        If assigned to a subdomain, URL format must be :subdomain-:tournament_url (e.g. 'test-mytourney'
        for test.challonge.com/mytourney)
        :param include_participants: 0 or 1; includes an array of associated participant records
        :param include_matches: 0 or 1; includes an array of associated match records
        """

        params = {
            "include_participants": include_participants,
            "include_matches": include_matches
        }

        response = self.http.post(f"tournaments/{tournament_id}/process_check_ins.json", params)

        tournament = response["tournament"]

        return tournament

    def abort_checkins(self, tournament_id: str, include_participants: int = None, include_matches: int = None):
        """
        When your tournament is in a 'checking_in' or 'checked_in' state, there's no way to edit the tournament's
        start time (start_at) or check-in duration (check_in_duration). You must first abort check-in,
        then you may edit those attributes.

            - Makes all participants active and clears their checked_in_at times.
            - Transitions the tournament state from 'checking_in' or 'checked_in' to 'pending'

        :param tournament_id: Tournament ID (e.g. 10230) or URL (e.g. 'single_elim' for challonge.com/single_elim).
        If assigned to a subdomain, URL format must be :subdomain-:tournament_url (e.g. 'test-mytourney'
        for test.challonge.com/mytourney)
        :param include_participants: 0 or 1; includes an array of associated participant records
        :param include_matches: 0 or 1; includes an array of associated match records
        """

        params = {
            "include_participants": include_participants,
            "include_matches": include_matches
        }

        response = self.http.post(f"tournaments/{tournament_id}/abort_check_in.json", params)

        tournament = response["tournament"]

        return tournament

    def start(self, tournament_id: str, include_participants: int = None, include_matches: int = None):
        """
        Start a tournament, opening up first round matches for score reporting. The tournament must have at least
        2 participants.

        :param tournament_id: Tournament ID (e.g. 10230) or URL (e.g. 'single_elim' for challonge.com/single_elim).
        If assigned to a subdomain, URL format must be :subdomain-:tournament_url (e.g. 'test-mytourney'
        for test.challonge.com/mytourney)
        :param include_participants: 0 or 1; includes an array of associated participant records
        :param include_matches: 0 or 1; includes an array of associated match records
        """

        params = {
            "include_participants": include_participants,
            "include_matches": include_matches
        }

        participants = self.participant_api.get_all(tournament_id)

        if len(participants) <= 1:
            raise ChallongeAPIException("ERROR: A tournament needs at least two participants in order to start.")
        else:
            response = self.http.post(f"tournaments/{tournament_id}/start.json", params)

            tournament = response["tournament"]

            return tournament

    def finalize(self, tournament_id: str, include_participants: int = None, include_matches: int = None):
        """
        Finalize a tournament that has had all match scores submitted, rendering its results permanent.

        :param tournament_id: Tournament ID (e.g. 10230) or URL (e.g. 'single_elim' for challonge.com/single_elim).
        If assigned to a subdomain, URL format must be :subdomain-:tournament_url (e.g. 'test-mytourney'
        for test.challonge.com/mytourney)
        :param include_participants: 0 or 1; includes an array of associated participant records
        :param include_matches: 0 or 1; includes an array of associated match records
        """

        params = {
            "include_participants": include_participants,
            "include_matches": include_matches
        }

        response = self.http.post(f"tournaments/{tournament_id}/finalize.json", params)

        tournament = response["tournament"]

        return tournament

    def reset(self, tournament_id: str, include_participants: int = None, include_matches: int = None):
        """
        Reset a tournament, clearing all of its scores and attachments. You can then add/remove/edit participants
        before starting the tournament again.

        :param tournament_id: Tournament ID (e.g. 10230) or URL (e.g. 'single_elim' for challonge.com/single_elim).
        If assigned to a subdomain, URL format must be :subdomain-:tournament_url (e.g. 'test-mytourney'
        for test.challonge.com/mytourney)
        :param include_participants: 0 or 1; includes an array of associated participant records
        :param include_matches: 0 or 1; includes an array of associated match records
        """

        params = {
            "include_participants": include_participants,
            "include_matches": include_matches
        }

        response = self.http.post(f"tournaments/{tournament_id}/reset.json", params)

        tournament = response["tournament"]

        return tournament

    def open_for_predictions(self, tournament_id: str, include_participants: int = None,
                             include_matches: int = None):
        """
        Sets the state of the tournament to start accepting predictions. Your tournament's 'prediction_method'
        attribute must be set to 1 (exponential scoring) or 2 (linear scoring) to use this option. Note: Once open
        for predictions, match records will be persisted, so participant additions and removals will no longer be
        permitted.

        :param tournament_id: Tournament ID (e.g. 10230) or URL (e.g. 'single_elim' for challonge.com/single_elim).
        If assigned to a subdomain, URL format must be :subdomain-:tournament_url (e.g. 'test-mytourney'
        for test.challonge.com/mytourney)
        :param include_participants: 0 or 1; includes an array of associated participant records
        :param include_matches: 0 or 1; includes an array of associated match records
        :return:
        """

        params = {
            "include_participants": include_participants,
            "include_matches": include_matches
        }

        response = self.http.post(f"tournaments/{tournament_id}/open_for_predictions.json", params)

        tournament = response["tournament"]

        return tournament


class ParticipantAPI:

    def __init__(self, http_methods):
        self.http = http_methods

    def get_all(self, tournament_id: str):
        """
        Retrieve a tournament's participant list.
        """

        response = self.http.get(f"tournaments/{tournament_id}/participants.json")

        participants = [p["participant"] for p in response]

        return participants

    def add(self, tournament_id: str, name: str = None, challonge_username: str = None, email: str = None,
            seed: str = None, misc: str = None):
        """
        Add a participant to a tournament (up until it is started).
        """

        params = {
            "participant[name]": name,
            "participant[challonge_username]": challonge_username,
            "participant[email]": email,
            "participant[seed]": seed,
            "participant[misc]": misc,
        }

        response = self.http.post(f"tournaments/{tournament_id}/participants.json", params)

        participant = response["participant"]

        return participant

    def add_multiple(self, tournament_id: str, names: List[str] = None,
                     challonge_usernames_or_emails: List[str] = None, seeds: List[str] = None,
                     miscs: List[str] = None):
        """
        Bulk add participants to a tournament (up until it is started). If an invalid participant is detected,
        bulk participant creation will halt and any previously added participants (from this API request) will
        be rolled back.

        NOTE: Names and Challonge usernames/emails are _not_ inclusive: if you add two names and three usernames,
        you'll have five participants.
        """

        params = {
            "participants[][name]": names,
            "participants[][invite_name_or_email]": challonge_usernames_or_emails,
            "participants[][seed]": seeds,
            "participants[][misc]": miscs,
        }

        response = self.http.post(f"tournaments/{tournament_id}/participants/bulk_add.json", params)

        participants = [p["participant"] for p in response]

        return participants

    def get(self, tournament_id: str, participant_id: int = None, include_matches: bool = False):
        """
        Retrieve a single participant record for a tournament.
        """

        params = {"include_matches": include_matches}

        response = self.http.get(f"tournaments/{tournament_id}/participants/{participant_id}.json", params)

        participant = response["participant"]

        return participant

    def update(self, tournament_id: str, participant_id: str, participant_name: str = None,
               participant_challonge_username: str = None, participant_email: str = None,
               participant_seed: int = None, misc: str = None):
        """
        Update the attributes of a tournament participant.
        """

        params = {
            "participant[name]": participant_name,
            "participant[challonge_username]": participant_challonge_username,
            "participant[email]": participant_email,
            "participant[seed]": participant_seed,
            "participant[misc]": misc,
        }

        response = self.http.put(f"tournaments/{tournament_id}/participants/{participant_id}.json", params)

        participant = response["participant"]

        return participant

    def check_in(self, tournament_id: str, participant_id: str):
        """
        Checks a participant in, setting checked_in_at to the current time.
        """

        response = self.http.post(f"tournaments/{tournament_id}/participants/{participant_id}/check_in.json")

        participant = response["participant"]

        return participant

    def check_out(self, tournament_id: str, participant_id: str):
        """
        Marks a participant as having not checked in, setting checked_in_at to nil - also called 'undo_check_in'.
        """

        response = self.http.post(f"tournaments/{tournament_id}/participants/{participant_id}/undo_check_in.json")

        participant = response["participant"]

        return participant

    def remove(self, tournament_id: str, participant_id: str):
        """
        If the tournament has not started, delete a participant, automatically filling in the abandoned seed
        number. If tournament is underway, mark a participant inactive, automatically forfeiting his/her
        remaining matches.
        """

        response = self.http.delete(f"tournaments/{tournament_id}/participants/{participant_id}.json")

        participant = response["participant"]

        return participant

    def remove_all(self, tournament_id: str):
        """
        Deletes all participants in a tournament. (Only allowed if tournament hasn't started yet)
        """

        response = self.http.delete(f"tournaments/{tournament_id}/participants/clear.json")

        return response["message"]  # "Cleared all participants"

    def randomize(self, tournament_id: str):
        """
        Randomize seeds among participants. Only applicable before a tournament has started.
        """

        response = self.http.post(f"tournaments/{tournament_id}/participants/randomize.json")

        participants = [p["participant"] for p in response]

        return participants


class MatchAPI:

    def __init__(self, http_methods):
        self.http = http_methods

    def get_all(self, tournament_id: str, state: str = None, participant_id: str = None):
        """
        Retrieve a tournament's match list.
        """

        params = {"state": state, "participant_id": participant_id}
        response = self.http.get(f"tournaments/{tournament_id}/matches.json", params)

        matches = [m["match"] for m in response]

        return matches

    def get(self, tournament_id: str, match_id: str = None, include_attachments: int = 0):
        """
        Retrieve a single match record for a tournament.
        """

        params = {"include_attachments": include_attachments}
        response = self.http.get(f"tournaments/{tournament_id}/matches/{match_id}.json", params)

        match = response["match"]

        return match

    def update(self, tournament_id: str, match_id: str = None, match_scores_csv: str = None,
               match_winner_id: str = None, match_player1_votes: str = None, match_player2_votes: str = None):
        """
        Update/submit the score(s) for a match. 'If you're updating winner_id, scores_csv must also be provided. You
        may, however, update score_csv without providing winner_id for live score updates.'

        :param tournament_id: A tournament ID.
        :param match_id: A match ID.
        :param match_scores_csv: Comma separated set/game scores with player 1 score first (e.g. "1-3,3-0,3-2")
        :param match_winner_id: The participant ID of the winner or "tie" if applicable (Round Robin and Swiss).
               NOTE: If you change the outcome of a completed match, all matches in the bracket that branch
               from the updated match will be reset.
        :param match_player1_votes: Overwrites the number of votes for player 1.
        :param match_player2_votes: Overwrites the number of votes for player 2.
        """

        params = {
            "match[scores_csv]": match_scores_csv,
            "match[winner_id]": match_winner_id,
            "match[player1_votes]": match_player1_votes,
            "match[player2_votes]": match_player2_votes
        }

        response = self.http.put(f"tournaments/{tournament_id}/matches/{match_id}.json", params)

        match = response["match"]

        return match

    def reopen(self, tournament_id: str, match_id: str = None):
        """
        Reopens a match that was marked completed, automatically resetting matches that follow it.
        """

        response = self.http.post(f"tournaments/{tournament_id}/matches/{match_id}/reopen.json")

        match = response["match"]

        return match

    def set_underway(self, tournament_id: str, match_id: str = None):
        """
        Sets "underway_at" to the current time and highlights the match in the bracket
        """

        response = self.http.post(f"tournaments/{tournament_id}/matches/{match_id}/mark_as_underway.json")

        match = response["match"]

        return match

    def unset_underway(self, tournament_id: str, match_id: str = None):
        """
        Clears "underway_at" and unhighlights the match in the bracket
        """

        response = self.http.post(f"tournaments/{tournament_id}/matches/{match_id}/unmark_as_underway.json")

        match = response["match"]

        return match


class AttachmentAPI:

    def __init__(self, http_methods):
        self.http = http_methods

    def get_all(self, tournament_id: str, match_id: str = None):
        """
        Retrieve a set of attachments created for a specific match.
        """

        response = self.http.get(f"tournaments/{tournament_id}/matches/{match_id}/attachments.json")

        match_attachments = [ma["match_attachment"] for ma in response]

        return match_attachments

    def create(self, tournament_id: str, match_id: str = None, match_attachment_asset: str = None,
               match_attachment_url: str = None, match_attachment_description: str = None):
        """
        Create a new attachment for the specific match.

        :param tournament_id: A tournament ID.
        :param match_id:  A match ID.
        :param match_attachment_asset: A file upload (250KB max, no more than 4 attachments per match). If provided,
               the url parameter will be ignored.
        :param match_attachment_url: A web URL
        :param match_attachment_description: Text to describe the file or URL attachment, or this can simply be
               standalone text.
        """

        params = {
            "match_attachment[asset]": match_attachment_asset,
            "match_attachment[url]": match_attachment_url,
            "match_attachment[description]": match_attachment_description
        }

        response = self.http.post(f"tournaments/{tournament_id}/matches/{match_id}/attachments.json", params)

        match_attachment = response["match_attachment"]

        return match_attachment

    def get(self, tournament_id: str, match_id: str = None, attachment_id: str = None):
        """
        Retrieve a single match attachment record.
        """

        response = self.http.get(f"tournaments/{tournament_id}/matches/{match_id}/attachments/{attachment_id}.json")

        match_attachment = response["match_attachment"]

        return match_attachment

    def update(self, tournament_id: str, match_id: str = None, attachment_id: str = None,
               match_attachment_asset: str = None, match_attachment_url: str = None,
               match_attachment_description: str = None):
        """
        Update the attributes of a match attachment.

        :param tournament_id: A tournament ID.
        :param match_id: A match ID.
        :param match_id: A match ID.
        :param attachment_id: An attachment ID.
        :param match_attachment_asset: A file upload (250KB max, no more than 4 attachments per match). If provided,
               the url parameter will be ignored.
        :param match_attachment_url: A web URL
        :param match_attachment_description: Text to describe the file or URL attachment, or this can simply be
               standalone text.
        """

        params = {
            "match_attachment[asset]": match_attachment_asset,
            "match_attachment[url]": match_attachment_url,
            "match_attachment[description]": match_attachment_description
        }

        response = self.http.put(
            f"tournaments/{tournament_id}/matches/{match_id}/attachments/{attachment_id}.json", params
        )

        match_attachment = response["match_attachment"]

        return match_attachment

    def delete(self, tournament_id: str, match_id: str = None, attachment_id: str = None):
        """
        Delete a match attachment.
        """

        response = self.http.delete(f"tournaments/{tournament_id}/matches/{match_id}/attachments/{attachment_id}.json")

        match_attachment = response["match_attachment"]

        return match_attachment



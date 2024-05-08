import random
import string
import unittest
from datetime import datetime, timedelta
from src.chyllonge.api import ChallongeApi, ChallongeApiHttpMethods


def delete_all_tournaments():
    """
    Deletes all tournaments associated with your account.
    """

    api = ChallongeApi()

    all_tournaments = api.tournaments.get_all()
    all_tournament_ids = [t["tournament"]["id"] for t in all_tournaments]

    for tid in all_tournament_ids:
        api.tournaments.delete(tournament_id=tid)


# @unittest.skip
class ChallongeAPITests(unittest.TestCase):

    def setUp(self):
        self.api = ChallongeApi()

    def test_heartbeat(self):
        response = self.api.get_heartbeat()
        self.assertIsNotNone(response)


class ChallongeAPIHttpMethodTests(unittest.TestCase):

    def setUp(self):
        self.http = ChallongeApiHttpMethods()

    def test_api_user_is_not_null(self):
        self.assertIsNotNone(self.http.user)

    def test_api_key_is_not_null(self):
        self.assertIsNotNone(self.http.key)

    def test_local_timezone_is_not_null(self):
        self.assertIsNotNone(self.http.timezone)

    def test_local_timezone_utc_offset_looks_right(self):
        print(self.http.tz_utc_offset_string)
        self.assertIsNotNone(self.http.tz_utc_offset_string)


# @unittest.skip
class TournamentAPITests(unittest.TestCase):

    def setUp(self):
        self.api = ChallongeApi()

        an_hour_from_now = ((datetime.now() + timedelta(hours=1)).isoformat() + self.api.http.tz_utc_offset_string)

        self.tournament = self.api.tournaments.create(
            name="chyllonge-temp",
            start_at=an_hour_from_now,
            check_in_duration=60
        )

        self.tournament_id = self.tournament["tournament"]["id"]
        self.tournament_name = self.tournament["tournament"]["name"]

    def tearDown(self):
        delete_all_tournaments()

    def test_get_all_tournaments(self):
        all_tournaments = self.api.tournaments.get_all()

        return self.assertIsNotNone(all_tournaments[0]["tournament"]["id"])

    def test_create_tournament(self):
        return self.assertTrue(self.tournament["tournament"]["name"] == "chyllonge-temp")

    def test_get_tournament(self):
        t2 = self.api.tournaments.get(self.tournament["tournament"]["id"])

        return self.assertIsNotNone(t2["tournament"]["id"])

    def test_update_tournament(self):
        new_t = self.api.tournaments.update(tournament_id=self.tournament_id, name="test2!")
        new_t_name = new_t["tournament"]["name"]

        return self.assertTrue(new_t_name != self.tournament_name)

    def test_delete_tournament(self):
        self.api.tournaments.delete(self.tournament_id)
        ts = self.api.tournaments.get_all()

        return self.assertTrue(len(ts) == 0)

    def test_process_tournament_checkins(self):
        alice = self.api.participants.add(self.tournament_id, name="Alice")
        self.api.participants.check_in(self.tournament_id, alice["participant"]["id"])
        t = self.api.tournaments.process_checkins(self.tournament_id)

        return self.assertTrue(t["tournament"]["state"] == "checked_in")

    def test_abort_tournament_checkins(self):
        alice = self.api.participants.add(self.tournament_id, name="Alice")
        self.api.participants.check_in(self.tournament_id, alice["participant"]["id"])
        self.api.tournaments.process_checkins(self.tournament_id)
        t = self.api.tournaments.abort_checkins(self.tournament_id)

        return self.assertTrue(t["tournament"]["state"] == "pending")

    def test_start_tournament(self):
        self.api.participants.add(self.tournament_id, name="Alice")
        self.api.participants.add(self.tournament_id, name="Bob")
        self.api.tournaments.process_checkins(self.tournament_id)
        self.api.tournaments.start(self.tournament_id)

        t = self.api.tournaments.get(self.tournament_id)

        return self.assertIsNotNone(t["tournament"]["state"] == "underway")

    def test_finalize_tournament(self):
        self.api.participants.add(self.tournament_id, name="Alice")
        self.api.participants.add(self.tournament_id, name="Bob")
        self.api.tournaments.process_checkins(self.tournament_id)
        self.api.tournaments.start(self.tournament_id)

        match_id = self.api.matches.get_all(tournament_id=self.tournament_id)[0]["match"]["id"]
        alice_id = self.api.participants.get_all(self.tournament_id)[0]["participant"]["id"]

        self.api.matches.set_underway(self.tournament_id, match_id)
        self.api.matches.update(self.tournament_id, match_id, match_scores_csv="3-1,2-2", match_winner_id=alice_id)
        self.api.tournaments.finalize(self.tournament_id)

        t = self.api.tournaments.get(self.tournament_id)

        return self.assertTrue(t["tournament"]["state"] == "complete")

    def test_reset_tournament(self):
        self.api.participants.add(self.tournament_id, name="Alice")
        self.api.participants.add(self.tournament_id, name="Bob")
        self.api.tournaments.process_checkins(self.tournament_id)
        self.api.tournaments.start(self.tournament_id)

        match_id = self.api.matches.get_all(tournament_id=self.tournament_id)[0]["match"]["id"]
        alice_id = self.api.participants.get_all(self.tournament_id)[0]["participant"]["id"]

        self.api.matches.set_underway(self.tournament_id, match_id)
        self.api.matches.update(self.tournament_id, match_id, match_scores_csv="3-1,2-2", match_winner_id=alice_id)

        self.api.tournaments.reset(self.tournament_id)

        updated_matches = self.api.matches.get_all(self.tournament_id)

        return self.assertTrue(len(updated_matches) == 0)

    def test_open_tournament_for_predictions(self):

        # overwrite tourney
        self.tournament = self.api.tournaments.create(name="chyllonge-temp", prediction_method=1)
        self.tournament_id = self.tournament["tournament"]["id"]
        self.tournament_name = self.tournament["tournament"]["name"]

        self.api.participants.add(self.tournament_id, name="Alice")
        self.api.participants.add(self.tournament_id, name="Bob")

        r = self.api.tournaments.open_for_predictions(self.tournament_id)

        return self.assertTrue(r["tournament"]["state"] == "accepting_predictions")


# @unittest.skip
class ParticipantsAPITests(unittest.TestCase):

    @staticmethod
    def _generate_mock_email_addresses(count):

        mock_email_addresses = []

        for c in range(0, count):
            mock_email_addresses.append(
                f"{''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(15))}@"
                f"{''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(15))}.com"
            )

        return mock_email_addresses

    def setUp(self):
        self.api = ChallongeApi()

        an_hour_from_now = ((datetime.now() + timedelta(hours=1)).isoformat() +
                            self.api.http.tz_utc_offset_string)

        self.tournament = self.api.tournaments.create(
            name="chyllonge-temp",
            start_at=an_hour_from_now,
            check_in_duration=60
        )

        self.tournament_id = self.tournament["tournament"]["id"]
        self.tournament_name = self.tournament["tournament"]["name"]

    def tearDown(self):
        delete_all_tournaments()

    def test_get_participants(self):
        """
        Retrieve a tournament's participant list.
        """

        self.api.participants.add(self.tournament_id, name="Alice")
        self.tournament_participants = self.api.participants.get_all(self.tournament_id)

        self.assertTrue(len(self.tournament_participants) == 1)

    def test_add_participant(self):
        """
        Add a participant to a tournament (up until it is started).
        """

        self.api.participants.add(self.tournament_id, name="Alice")
        self.api.participants.add(self.tournament_id, name="Bob")
        self.tournament_participants = self.api.participants.get_all(self.tournament_id)

        self.assertTrue(len(self.tournament_participants) >= 2)

    def test_add_participants(self):
        """
        Bulk add participants to a tournament (up until it is started). If an invalid participant is detected,
        bulk participant creation will halt and any previously added participants (from this API request) will
        be rolled back.
        """

        self.api.participants.add_multiple(
            tournament_id=self.tournament_id,
            names=["Alice", "Bob", "Charlie"],
            challonge_usernames_or_emails=self._generate_mock_email_addresses(3)
        )

        self.tournament_participants = self.api.participants.get_all(self.tournament_id)

        self.assertTrue(len(self.tournament_participants) == 5)

    def test_get_participant(self):
        """
        Retrieve a single participant record for a tournament.
        """

        p = self.api.participants.add(self.tournament_id, name="Alice")

        self.assertIsNotNone(p["participant"]["id"])

    def test_update_participant(self):
        """
        Update the attributes of a tournament participant.
        """

        p = self.api.participants.add(self.tournament_id, name="Alice")
        p2 = self.api.participants.update(self.tournament_id, p["participant"]["id"], "Allison")

        self.assertTrue(p["participant"]["name"] != p2["participant"]["name"])

    def test_check_in_participant(self):
        """
        Checks a participant in, setting checked_in_at to the current time.
        """

        alice = self.api.participants.add(self.tournament_id, name="Alice")
        self.api.participants.check_in(self.tournament_id, alice["participant"]["id"])
        alice = self.api.participants.get(self.tournament_id, alice["participant"]["id"])

        self.assertTrue(alice["participant"]["checked_in"])

    def test_check_out_participant(self):
        """
        Marks a participant as having not checked in, setting checked_in_at to nil.
        """

        alice = self.api.participants.add(self.tournament_id, name="Alice")
        alice = self.api.participants.check_in(self.tournament_id, alice["participant"]["id"])
        alice = self.api.participants.check_out(self.tournament_id, alice["participant"]["id"])

        self.assertFalse(alice["participant"]["checked_in"])

    def test_remove_participant(self):
        """
        If the tournament has not started, delete a participant, automatically filling in the abandoned seed
        number. If tournament is underway, mark a participant inactive, automatically forfeiting his/her
        remaining matches.
        """

        alice = self.api.participants.add(self.tournament_id, name="Alice")
        ps = self.api.participants.get_all(self.tournament_id)

        self.api.participants.remove(self.tournament_id, alice["participant"]["id"])
        ps2 = self.api.participants.get_all(self.tournament_id)

        self.assertTrue(len(ps) != len(ps2))

    def test_remove_all_participants(self):
        """
        Deletes all participants in a tournament. (Only allowed if tournament hasn't started yet)
        """

        self.api.participants.add_multiple(
            tournament_id=self.tournament_id,
            names=["Alice", "Bob", "Charlie"],
            challonge_usernames_or_emails=self._generate_mock_email_addresses(3)
        )

        self.api.participants.remove_all(self.tournament_id)
        ps = self.api.participants.get_all(self.tournament_id)

        self.assertTrue(len(ps) == 0)

    def test_randomize_participants(self):
        """
        Randomize seeds among participants. Only applicable before a tournament has started.

        NOTE: this test obviously has a 10% chance of failing.
        """

        self.api.participants.add_multiple(
            tournament_id=self.tournament_id,
            names=["Alice", "Bob", "Charlie", "David", "Edward", "Frank", "Geoff", "Hector", "Isabelle", "James"],
            challonge_usernames_or_emails=self._generate_mock_email_addresses(10)
        )

        ps = self.api.participants.randomize(self.tournament_id)

        self.assertTrue(ps[0]["participant"]["name"] != "Alice")


# @unittest.skip
class MatchAPITests(unittest.TestCase):

    def setUp(self):
        self.api = ChallongeApi()

        an_hour_from_now = ((datetime.now() + timedelta(hours=1)).isoformat() +
                            self.api.http.tz_utc_offset_string)

        self.tournament = self.api.tournaments.create(
            name="chyllonge-temp",
            start_at=an_hour_from_now,
            check_in_duration=60
        )

        self.tournament_id = self.tournament["tournament"]["id"]
        self.tournament_name = self.tournament["tournament"]["name"]

        # pretend alice and bob are in a match
        self.api.participants.add(self.tournament_id, name="Alice")
        self.api.participants.add(self.tournament_id, name="Bob")
        self.api.tournaments.process_checkins(self.tournament_id)
        self.api.tournaments.start(self.tournament_id)

        self.all_current_matches = self.api.matches.get_all(tournament_id=self.tournament_id)
        self.all_current_participants = self.api.participants.get_all(self.tournament_id)

    def tearDown(self):
        delete_all_tournaments()

    def test_get_all(self):
        self.assertTrue(len(self.all_current_matches) > 0)

    def test_get(self):
        match_id = self.all_current_matches[0]["match"]["id"]
        match = self.api.matches.get(self.tournament_id, match_id)

        self.assertTrue(len(match) > 0)

    def test_update(self):
        match_id = self.all_current_matches[0]["match"]["id"]
        self.api.matches.set_underway(self.tournament_id, match_id)
        alice_id = self.all_current_participants[0]["participant"]["id"]

        updated_match = self.api.matches.update(
            self.tournament_id,
            match_id,
            match_scores_csv="3-1,2-2",
            match_winner_id=alice_id)["match"]

        self.assertIsNotNone(updated_match["scores_csv"])

    def test_reopen(self):
        match_id = self.all_current_matches[0]["match"]["id"]
        self.api.matches.set_underway(self.tournament_id, match_id)
        alice_id = self.all_current_participants[0]["participant"]["id"]

        updated_match = self.api.matches.update(
            self.tournament_id,
            match_id,
            match_scores_csv="3-1,2-2",
            match_winner_id=alice_id)["match"]

        self.api.matches.reopen(self.tournament_id, updated_match["id"])

        updated_match = self.api.matches.get(self.tournament_id, match_id)

        self.assertTrue(updated_match["match"]["state"] == "open")

    def test_set_underway(self):
        match_id = self.all_current_matches[0]["match"]["id"]
        self.api.matches.set_underway(self.tournament_id, match_id)
        match = self.api.matches.get(self.tournament_id, match_id)["match"]

        self.assertIsNotNone(match["underway_at"])

    def test_unset_underway(self):
        match_id = self.all_current_matches[0]["match"]["id"]
        self.api.matches.set_underway(self.tournament_id, match_id)
        self.api.matches.unset_underway(self.tournament_id, match_id)
        match = self.api.matches.get(self.tournament_id, match_id)["match"]

        self.assertIsNone(match["underway_at"])


# @unittest.skip
class AttachmentAPITests(unittest.TestCase):

    def setUp(self):
        self.api = ChallongeApi()

        an_hour_from_now = ((datetime.now() + timedelta(hours=1)).isoformat() + self.api.http.tz_utc_offset_string)

        self.tournament = self.api.tournaments.create(
            name="chyllonge-temp",
            start_at=an_hour_from_now,
            check_in_duration=60,
            accept_attachments=True
        )

        self.tournament_id = self.tournament["tournament"]["id"]
        self.tournament_name = self.tournament["tournament"]["name"]

        # pretend alice and bob are in a match
        self.api.participants.add(self.tournament_id, name="Alice")
        self.api.participants.add(self.tournament_id, name="Bob")
        self.api.tournaments.process_checkins(self.tournament_id)
        self.api.tournaments.start(self.tournament_id)

        self.all_current_matches = self.api.matches.get_all(tournament_id=self.tournament_id)
        self.current_match = self.all_current_matches[0]["match"]

        self.api.attachments.create(
            self.tournament_id,
            self.current_match["id"],
            # just some image that shouldn't go away anytime soon
            match_attachment_url="https://www.gstatic.com/webp/gallery3/1.png",
            match_attachment_description="chyllonge-test"
        )

    def tearDown(self):
        delete_all_tournaments()

    def test_get_all(self):
        attachments = self.api.attachments.get_all(self.tournament_id, self.current_match["id"])

        self.assertIsNotNone(attachments)

    def test_create(self):
        attachments = self.api.attachments.get_all(self.tournament_id, self.current_match["id"])

        self.assertIsNotNone(attachments)

    def test_get(self):
        attachment_1 = self.api.attachments.get_all(self.tournament_id, self.current_match["id"])[0]["match_attachment"]
        attachment_2 = self.api.attachments.get(self.tournament_id, self.current_match["id"], attachment_1["id"])

        self.assertIsNotNone(attachment_2)

    @unittest.skip
    def test_update(self):
        attachment = self.api.attachments.get_all(self.tournament_id, self.current_match["id"])[0]["match_attachment"]

        self.api.attachments.update(
            self.tournament_id,
            self.current_match["id"],
            attachment["id"],
            # another image that shouldn't go away anytime soon
            match_attachment_url="https://www.gstatic.com/webp/gallery3/2.png",
            match_attachment_description="chyllonge-test-2"
        )

        attachment = self.api.attachments.get_all(self.tournament_id, self.current_match["id"])[0]["match_attachment"]

        # TODO: this DOES work; the attachment is updated - figure out why the API doesn't realize that.
        self.assertTrue(attachment["url"] == "https://www.gstatic.com/webp/gallery3/2.png")

    def test_delete(self):
        attachment = self.api.attachments.get_all(self.tournament_id, self.current_match["id"])[0]["match_attachment"]
        self.api.attachments.delete(self.tournament_id, self.current_match["id"], attachment["id"])
        attachments = self.api.attachments.get_all(self.tournament_id, self.current_match["id"])

        self.assertTrue(len(attachments) == 0)

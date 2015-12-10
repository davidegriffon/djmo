import sys
import os
from django.test import TestCase
from .models import SoccerTeam, SoccerPlayer
from django.conf import settings
# add dynamically djmo to PYTHONPATH
djmo_root = settings.BASE_DIR[:settings.BASE_DIR.rfind("{}djmo".format(os.sep))]
sys.path.insert(0, djmo_root)
from djmo import observe_models


class BaseTestCase(TestCase):

    def setUp(self):
        teams = [
            ('Dream Team', 58000, ['Mario Rossi', 'Mario Verdi', 'Mario Gialli']),
            ('Empty Team', 7500, []),  # no players
        ]
        for name, supporters, players in teams:
            soccer_team = SoccerTeam.objects.create(name=name, number_of_supporters=supporters)
            for player in players:
                first_name, last_name = tuple(player.split())
                SoccerPlayer.objects.create(team=soccer_team, first_name=first_name, last_name=last_name)
        self.dream_team = SoccerTeam.objects.all()[0]
        self.empty_team = SoccerTeam.objects.all()[1]

    def perform_some_actions(self):
        # players creations
        p1 = SoccerPlayer.objects.create(team=self.dream_team, first_name='a', last_name='b')
        p2 = SoccerPlayer.objects.create(team=self.dream_team, first_name='c', last_name='d')
        p3 = SoccerPlayer.objects.create(team=self.dream_team, first_name='e', last_name='f')
        # team creation
        new_team = SoccerTeam.objects.create(name='other team', number_of_supporters=400)
        # team deletion
        self.empty_team.delete()
        # soccer updates
        p1.first_name = 'Mario'
        p1.save()
        p2.team = new_team
        p2.save()
        # deletion not affect `number_of_objects_created`
        p3.delete()


class ObserverTestCase(BaseTestCase):
    """tests for class Observer"""

    @observe_models(SoccerPlayer)
    def test_crud_actions_should_be_traced(self):
        # print(self._testMethodName, "test_crud_actions_should_be_traced -->", id(self.observers[SoccerPlayer]), threading.current_thread())
        self.perform_some_actions()
        self.assertEqual(3, self.observers[SoccerPlayer].number_of_objects_created)
        self.assertEqual(2, self.observers[SoccerPlayer].number_of_objects_updated)
        self.assertEqual(1, self.observers[SoccerPlayer].number_of_objects_deleted)
        self.assertFalse(self.observers[SoccerPlayer].nothing_has_changed)

    @observe_models(SoccerPlayer)
    def test_reset_method(self):
        # print(self._testMethodName, "test_crud_actions_should_be_traced -->", id(self.observers[SoccerPlayer]), threading.current_thread())
        self.perform_some_actions()
        self.observers[SoccerPlayer].reset()
        self.assertEqual(0, self.observers[SoccerPlayer].number_of_objects_created)
        self.assertEqual(0, self.observers[SoccerPlayer].number_of_objects_updated)
        self.assertEqual(0, self.observers[SoccerPlayer].number_of_objects_deleted)

    @observe_models(SoccerPlayer)
    def test_property_observer(self):
        # print(self._testMethodName, "test_property_observer -->", id(self.observers[SoccerPlayer]), threading.current_thread())
        self.perform_some_actions()
        self.assertEqual(self.observers[SoccerPlayer], self.observer)
        self.assertEqual(self.observers[SoccerPlayer], self.soccerplayer_observer)

    @observe_models(SoccerPlayer, SoccerTeam)
    def test_multiple_observers(self):
        # print(self._testMethodName, "test_multiple_observers -->", id(self.observers[SoccerPlayer]), threading.current_thread())
        self.perform_some_actions()
        # asserts on player obserever
        self.assertEqual(3, self.observers[SoccerPlayer].number_of_objects_created)
        self.assertEqual(2, self.observers[SoccerPlayer].number_of_objects_updated)
        self.assertEqual(1, self.observers[SoccerPlayer].number_of_objects_deleted)
        # asserts on team obserever
        self.assertEqual(1, self.observers[SoccerTeam].number_of_objects_created)
        self.assertEqual(0, self.observers[SoccerTeam].number_of_objects_updated)
        self.assertEqual(1, self.observers[SoccerTeam].number_of_objects_deleted)

    @observe_models(SoccerPlayer, SoccerTeam)
    def test_cascade_deletion(self):
        # print(self._testMethodName, "test_cascade_deletion -->", id(self.observers[SoccerPlayer]), threading.current_thread())
        self.dream_team.delete()
        self.assertEqual(3, self.observers[SoccerPlayer].number_of_objects_deleted)
        self.assertEqual(1, self.observers[SoccerTeam].number_of_objects_deleted)

    @observe_models(SoccerPlayer)
    def test_observer_properties(self):
        # print(self._testMethodName, "test_object_method -->", id(self.observers[SoccerPlayer]), threading.current_thread())
        # only created
        mario_neri = SoccerPlayer.objects.create(team=self.dream_team, first_name='Mario', last_name='Neri')

        # created and updated
        mario_bianchi = SoccerPlayer.objects.create(team=self.dream_team, first_name='Mariooo', last_name='Bianchi')
        mario_bianchi.first_name = 'Mario'
        mario_bianchi.save()

        # updated and then deleted
        mario_rossi = SoccerPlayer.objects.get(first_name='Mario', last_name='Rossi')
        mario_rossi.team = self.empty_team
        mario_rossi.save()
        mario_rossi.delete()

        # untouched
        mario_verdi = SoccerPlayer.objects.get(first_name='Mario', last_name='Verdi')

        # never saved
        mario_rosa = SoccerPlayer(first_name='Mario', last_name='Rosa')

        self.assertTrue(self.observers[SoccerPlayer].instance(mario_neri).is_created)
        self.assertFalse(self.observers[SoccerPlayer].instance(mario_neri).is_updated)
        self.assertFalse(self.observers[SoccerPlayer].instance(mario_neri).is_deleted)

        self.assertTrue(self.observers[SoccerPlayer].instance(mario_bianchi).is_created)
        self.assertTrue(self.observers[SoccerPlayer].instance(mario_bianchi).is_updated)
        self.assertFalse(self.observers[SoccerPlayer].instance(mario_bianchi).is_deleted)

        self.assertFalse(self.observers[SoccerPlayer].instance(mario_rossi).is_created)
        self.assertTrue(self.observers[SoccerPlayer].instance(mario_rossi).is_updated)
        self.assertTrue(self.observers[SoccerPlayer].instance(mario_rossi).is_deleted)

        self.assertFalse(self.observers[SoccerPlayer].instance(mario_verdi).is_created)
        self.assertFalse(self.observers[SoccerPlayer].instance(mario_verdi).is_updated)
        self.assertFalse(self.observers[SoccerPlayer].instance(mario_verdi).is_deleted)

        self.assertFalse(self.observers[SoccerPlayer].instance(mario_rosa).is_created)
        self.assertFalse(self.observers[SoccerPlayer].instance(mario_rosa).is_updated)
        self.assertFalse(self.observers[SoccerPlayer].instance(mario_rosa).is_deleted)

    @observe_models(SoccerPlayer)
    def test_assertDelta_method(self):
        mario_rossi = SoccerPlayer.objects.get(last_name='Rossi')
        mario_verdi = SoccerPlayer.objects.get(last_name='Verdi')
        self.observers[SoccerPlayer].observe_instances(mario_rossi, mario_verdi)

        # some operation on Mario Rossi
        mario_rossi.last_name = "Arancioni"
        mario_rossi.save()
        self.assertDictEqual({'last_name': 'Arancioni'}, self.observers[SoccerPlayer].instance(mario_rossi).delta)
        mario_rossi.first_name = "Giulio"
        mario_rossi.save()
        self.assertDictEqual({'last_name': 'Arancioni', 'first_name': 'Giulio'}, self.observers[SoccerPlayer].instance(mario_rossi).delta)
        self.assertTrue(self.observers[SoccerPlayer].instance(mario_rossi).is_updated)
        self.assertFalse(self.observers[SoccerPlayer].instance(mario_rossi).is_deleted)

        # check assertRaises method
        self.observers[SoccerPlayer].assertDelta(mario_rossi, {'last_name': 'Arancioni', 'first_name': 'Giulio'})
        self.assertRaises(AssertionError, self.observers[SoccerPlayer].assertDelta, mario_rossi, {'foo': 'bar'})

        # some operation on Mario Verdi
        self.assertDictEqual({}, self.observers[SoccerPlayer].instance(mario_verdi).delta)
        self.assertFalse(self.observers[SoccerPlayer].instance(mario_verdi).is_updated)
        self.assertFalse(self.observers[SoccerPlayer].instance(mario_verdi).is_deleted)
        mario_verdi.delete()
        self.assertTrue(self.observers[SoccerPlayer].instance(mario_verdi).is_deleted)

    @observe_models(SoccerPlayer)
    def test_assertModelIsUntouched_method(self):
        self.observers[SoccerPlayer].assertModelIsUntouched()  # check that this method does not raise an error
        self.perform_some_actions()
        self.assertRaises(Exception, self.observers[SoccerPlayer].assertModelIsUntouched)


class ObserversListTestCase(BaseTestCase):
    """tests for class ObserversList"""

    @observe_models(SoccerPlayer, SoccerTeam)
    def test_reset_and_nothing_has_changed_method(self):
        self.perform_some_actions()
        self.assertFalse(self.observers.nothing_has_changed)
        self.observers.reset()
        self.assertTrue(self.observers.nothing_has_changed)

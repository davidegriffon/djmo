"""
Only for test purpose
"""
from django.db import models


class SoccerTeam(models.Model):
    name = models.CharField(max_length=50)
    number_of_supporters = models.IntegerField()

    @property
    def all_players(self):
        return SoccerPlayer.objects.filter(team=self)


class SoccerPlayer(models.Model):
    team = models.ForeignKey(SoccerTeam)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)

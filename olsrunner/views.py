from django.shortcuts import render
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.http import HttpResponseServerError
from cassiopeia import riotapi, baseriotapi
from cassiopeia.type.core.common import LoadPolicy
from cassiopeia.type.dto.tournament import TournamentCodeParameters
from olsrunner.models import Player, Game, Team, Stats, Week, TourneyCode, PlayoffGames
from django.template import loader, Context
from django.contrib.auth.decorators import permission_required
from django.core import serializers
from django.db.models import Max, Q
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from datetime import date, time, timedelta, datetime
from django.db import connection
import pickle
import json
from django.views.decorators.csrf import csrf_exempt
import django_tables2 as tables
from django_tables2   import RequestConfig
from cassiopeia.type.api.exception import APIError
import re
import itertools
import random

def index(request):
	return HttpResponse(render(request, 'index.html',))
# Create your views here.

class Match:
	pass


#          ADMIN VIEWS

@permission_required('ols.olsadmin')
def addPlayers(request):
	#for row in Player.objects.all():
	#	if Player.objects.filter(SummonerNumber=row.SummonerNumber).count() > 1:
	#		row.delete()
	return HttpResponse(render(request, 'addplayers.html', ))

@permission_required('ols.olsadmin')
def addplayerlist(request):
	if not request.user.is_authenticated():
		return HttpResponseRedirect('/ols/login')
	else:
		posted = request.POST
		#playerlist = posted.split(','')
		playerlist = posted.get('players').split(',')
		print(playerlist)
		riotapi.set_region("NA")
		riotapi.set_api_key("APIKEY")
		for player in playerlist:
			player = player.split(':')
			play = Player()
			play.PlayerName = player[0]
			play.PlayerIGN = player[1]
			play.SummonerNumber = riotapi.get_summoner_by_name(player[1]).id
			play.save()
		return HttpResponse("Added players")

@permission_required('ols.olsadmin')
def AddTeam(request):
	if request.POST:
		newteam = Team()
		posted = request.POST
		#print(posted.get('teamname'))
		newteam.teamName = posted.get('teamname')
		newteam.Captain = posted.get('cap')
		newteam.Player1 = posted.get('P1')
		newteam.Player2 = posted.get('P2')
		newteam.Player3 = posted.get('P3')
		newteam.Player4 = posted.get('P4')
		riotapi.set_region("NA")
		riotapi.set_api_key("APIKEY")
		summtoadd = riotapi.get_summoner_by_name(newteam.Captain)
		print(summtoadd)
		newteam.CaptainID = summtoadd.id
		summtoadd = riotapi.get_summoner_by_name(newteam.Player1)
		print(summtoadd)
		newteam.Player1ID = summtoadd.id
		summtoadd = riotapi.get_summoner_by_name(newteam.Player2)
		print(summtoadd)
		newteam.Player2ID = summtoadd.id
		summtoadd = riotapi.get_summoner_by_name(newteam.Player3)
		print(summtoadd)
		newteam.Player3ID = summtoadd.id
		summtoadd = riotapi.get_summoner_by_name(newteam.Player4)
		print(summtoadd)
		newteam.Player4ID = summtoadd.id
		#print(Team.objects.all().aggregate(Max('teamID')))
		try:
			if Team.objects.all().aggregate(Max('teamID'))['teamID_max'] is not None:
				newteam.teamID = Team.objects.all().aggregate(Max('teamID'))['teamID__max'] + 1
			else:
				raise KeyError("no teams yet")
		except KeyError:
			newteam.teamID = 0
		newteam.save()
		return HttpResponse(render(request, 'addedteam.html'))
	else:
		return HttpResponse(render(request, 'addteam.html'))


def addPoints(winner, loser, winnerpos):
	winner.points = winner.points + 1
	if winnerpos == 1:
		gm = Game.objects.filter(team1__iexact= loser.teamID)
		try:
			gm = gm.get(winner= winner.teamID)
		except ObjectDoesNotExist:
			winner.save()
			return
	else:
		gm = Game.objects.filter(team2__iexact=loser.teamID)
		try:
			gm = gm.get(winner=winner.teamID)
		except ObjectDoesNotExist:
			winner.save()
			return
	winner.points = winner.points + 1
	winner.save()
	return

@permission_required('ols.olsadmin')
def addMatch(request):
	if request.POST:
		newgame = Game()
		posted = request.POST
		print(posted.get('team1name'))
		newgame.team1 = Team.objects.get(teamName__iexact=posted.get('team1name')).teamID
		newgame.team2 = Team.objects.get(teamName__iexact=posted.get('team2name')).teamID
		newgame.winner = Team.objects.get(teamName__iexact=posted.get('winner')).teamID
		print (Game.objects.all().aggregate(Max('Number')))
		try:
			newgame.Number = Game.objects.all().aggregate(Max('Number'))['Number__max'] + 1
		except TypeError:
			newgame.Number = 0
		riotapi.set_region("NA")
		riotapi.set_api_key("APIKEY")
		m = riotapi.get_match(posted.get('match'))
		if newgame.team2 == newgame.winner:
			loser = Team.objects.get(teamName__iexact=posted.get('team1name'))
			position = 2
		else:
			loser = Team.objects.get(teamName__iexact=posted.get('team2name'))
			position = 1

		#Adding games doesn't give points now
		#addPoints(Team.objects.get(teamName__iexact=posted.get('winner')), loser, position)
		print(posted.get('P2'))
		namelist= []
		namelist.append(posted.get('P1'))
		namelist.append(posted.get('P2'))
		namelist.append(posted.get('P3'))
		namelist.append(posted.get('P4'))
		namelist.append(posted.get('P5'))
		namelist.append(posted.get('2P1'))
		namelist.append(posted.get('2P2'))
		namelist.append(posted.get('2P3'))
		namelist.append(posted.get('2P4'))
		namelist.append(posted.get('2P5'))
		summoners = riotapi.get_summoners_by_name(namelist)
		print(dir(summoners[0]))
		print(summoners[0].id)
		newgame.team1Player1 = summoners[0].id
		newgame.team1Player2 = summoners[1].id
		newgame.team1Player3 = summoners[2].id
		newgame.team1Player4 = summoners[3].id
		newgame.team1Player5 = summoners[4].id
		newgame.team2Player1 = summoners[5].id
		newgame.team2Player2 = summoners[6].id
		newgame.team2Player3 = summoners[7].id
		newgame.team2Player4 = summoners[8].id
		newgame.team2Player5 = summoners[9].id
		newgame.matchID = posted.get('match')
		i = 0
		'''for player in m.participants:
			try:
				st = Stats.objects.get(PlayerID=summoners[i].id)
			except:
				st = Stats()
				st.PlayerID = summoners[i].id
			i= i+ 1
			st.Kills = st.Kills + player.stats.kills
			st.Deaths = st.Deaths + player.stats.deaths
			st.Assists = st.Assists + player.stats.assists
			st.GoldTotal = st.GoldTotal + player.stats.gold_earned
			st.GamesPlayed = st.GamesPlayed + 1
			if player.stats.largest_critical_strike > st.LargestCrit:
				st.LargestCrit = player.stats.largest_critical_strike
			st.Creeps = st.Creeps + player.stats.minion_kills + player.stats.monster_kills
			st.SecondsPlayed = st.SecondsPlayed + m.duration.total_seconds()
			st.DamageDealt = st.DamageDealt + player.stats.damage_dealt_to_champions
			st.DamageReceived = st.DamageReceived + player.stats.damage_taken
			if i <= 5:
				st.TeamKillTotal =  st.TeamKillTotal + m.participants[0].stats.kills  + m.participants[1].stats.kills  + m.participants[2].stats.kills  + m.participants[3].stats.kills  + m.participants[4].stats.kills
			else:
				st.TeamKillTotal =  st.TeamKillTotal + m.participants[5].stats.kills  + m.participants[6].stats.kills  + m.participants[7].stats.kills  + m.participants[8].stats.kills  + m.participants[9].stats.kills
			st.DoubleKills =  st.DoubleKills + player.stats.double_kills
			st.TripleKills = st.TripleKills + player.stats.triple_kills
			st.QuadraKills = st.QuadraKills + player.stats.quadra_kills
			st.PentaKills = st.PentaKills + player.stats.penta_kills
			st.save()'''
		with open('olsrunner/matches/' + str(newgame.Number) + '.pk', 'wb') as outfile:
			pickle.dump( m , outfile)
		newgame.filename = 'olsrunner/matches/' + str(newgame.Number) + '.pk'
		newgame.save()
		return HttpResponse("match added")
	else:
		teamNames = []
		teams = Team.objects.all().values('teamName')
		for t in teams:
			teamNames.append(t['teamName'])

		return HttpResponse(render(request, 'addMatch.html', {'teams' :teamNames}))

@permission_required('ols.olsadmin')
def updateIDs(request):
	NoIDs = Player.objects.filter(SummonerNumber=0)
	riotapi.set_region("NA")
	riotapi.set_api_key("APIKEY")
	for play in NoIDs:
		summtoadd = riotapi.get_summoner_by_name(play.PlayerIGN)
		play.SummonerNumber = summtoadd.id
		play.save()
		print(summtoadd.id)
	return HttpResponse("All unset IDs have been updated")

@permission_required('ols.olsadmin')
def updateTeamIDs(request):
	teams = Team.objects.all()
	riotapi.set_region("NA")
	riotapi.set_api_key("APIKEY")
	for t in teams:
		if t.CaptainID == 0:
			summtoadd = riotapi.get_summoner_by_name(t.Captain)
			t.CaptainID = summtoadd.id
		if t.Player1ID == 0:
			summtoadd = riotapi.get_summoner_by_name(t.Player1)
			t.Player1ID = summtoadd.id
		if t.Player2ID == 0:
			summtoadd = riotapi.get_summoner_by_name(t.Player2)
			t.Player2ID = summtoadd.id
		if t.Player3ID == 0:
			summtoadd = riotapi.get_summoner_by_name(t.Player3)
			t.Player3ID = summtoadd.id
		if t.Player4ID == 0:
			summtoadd = riotapi.get_summoner_by_name(t.Player4)
			t.Player4ID = summtoadd.id
		t.save()

	return HttpResponse("All unset IDs have been updated")

@permission_required('ols.olsadmin')
def generateplayoffs(request):
	baseriotapi.set_region("NA")
	baseriotapi.set_api_key("APIKEY")
	baseriotapi.set_tournament_api_key("APIKEY")
	t1 = 1
	t2 = 12
	t3 = 20
	t4 = 0
	t5 = 6
	t6 = 11
	t7 = 17
	t8 = 9
	t9 = 23
	t10 = 3
	t11 = 19
	t12 = 15
	t13 = 13
	t14 = 21
	t15 = 22
	t16 = 18
	series = []
	codecount = 8*3 + 4*3+2*3+5
	params = TournamentCodeParameters(5, "ALL", "TOURNAMENT_DRAFT", "SUMMONERS_RIFT")
	codes = baseriotapi.create_tournament_codes(6365, params,  count=codecount)
	codeiter = 0
	seriesiter = 0
	#round of 16
	series = PlayoffGames()
	series.roundof= 16
	series.identifier = seriesiter
	series.team1 = t1
	series.team2 = t2
	series.code1 = codes[codeiter]
	codeiter = codeiter + 1
	series.code2 = codes[codeiter]
	codeiter = codeiter + 1
	series.code3 = codes[codeiter]
	codeiter = codeiter + 1
	seriesiter = seriesiter + 1
	series.save()

	series = PlayoffGames()
	series.roundof= 16
	series.identifier = seriesiter
	series.team1 = t3
	series.team2 = t4
	series.code1 = codes[codeiter]
	codeiter = codeiter + 1
	series.code2 = codes[codeiter]
	codeiter = codeiter + 1
	series.code3 = codes[codeiter]
	codeiter = codeiter + 1
	seriesiter = seriesiter + 1
	series.save()

	series = PlayoffGames()
	series.roundof= 16
	series.identifier = seriesiter
	series.team1 = t5
	series.team2 = t6
	series.code1 = codes[codeiter]
	codeiter = codeiter + 1
	series.code2 = codes[codeiter]
	codeiter = codeiter + 1
	series.code3 = codes[codeiter]
	codeiter = codeiter + 1
	seriesiter = seriesiter + 1
	series.save()

	series = PlayoffGames()
	series.roundof= 16
	series.identifier = seriesiter
	series.team1 = t7
	series.team2 = t8
	series.code1 = codes[codeiter]
	codeiter = codeiter + 1
	series.code2 = codes[codeiter]
	codeiter = codeiter + 1
	series.code3 = codes[codeiter]
	codeiter = codeiter + 1
	seriesiter = seriesiter + 1
	series.save()

	series = PlayoffGames()
	series.roundof= 16
	series.identifier = seriesiter
	series.team1 = t9
	series.team2 = t10
	series.code1 = codes[codeiter]
	codeiter = codeiter + 1
	series.code2 = codes[codeiter]
	codeiter = codeiter + 1
	series.code3 = codes[codeiter]
	codeiter = codeiter + 1
	seriesiter = seriesiter + 1
	series.save()

	series = PlayoffGames()
	series.roundof= 16
	series.identifier = seriesiter
	series.team1 = t11
	series.team2 = t12
	series.code1 = codes[codeiter]
	codeiter = codeiter + 1
	series.code2 = codes[codeiter]
	codeiter = codeiter + 1
	series.code3 = codes[codeiter]
	codeiter = codeiter + 1
	seriesiter = seriesiter + 1
	series.save()

	series = PlayoffGames()
	series.roundof= 16
	series.identifier = seriesiter
	series.team1 = t13
	series.team2 = t14
	series.code1 = codes[codeiter]
	codeiter = codeiter + 1
	series.code2 = codes[codeiter]
	codeiter = codeiter + 1
	series.code3 = codes[codeiter]
	codeiter = codeiter + 1
	seriesiter = seriesiter + 1
	series.save()

	series = PlayoffGames()
	series.roundof= 16
	series.identifier = seriesiter
	series.team1 = t15
	series.team2 = t16
	series.code1 = codes[codeiter]
	codeiter = codeiter + 1
	series.code2 = codes[codeiter]
	codeiter = codeiter + 1
	series.code3 = codes[codeiter]
	codeiter = codeiter + 1
	seriesiter = seriesiter + 1
	series.save()

	#round of 8
	series = PlayoffGames()
	series.roundof= 8
	series.identifier = seriesiter
	series.code1 = codes[codeiter]
	codeiter = codeiter + 1
	series.code2 = codes[codeiter]
	codeiter = codeiter + 1
	series.code3 = codes[codeiter]
	codeiter = codeiter + 1
	seriesiter = seriesiter + 1
	series.save()

	series = PlayoffGames()
	series.roundof= 8
	series.identifier = seriesiter
	series.code1 = codes[codeiter]
	codeiter = codeiter + 1
	series.code2 = codes[codeiter]
	codeiter = codeiter + 1
	series.code3 = codes[codeiter]
	codeiter = codeiter + 1
	seriesiter = seriesiter + 1
	series.save()

	series = PlayoffGames()
	series.roundof= 8
	series.identifier = seriesiter
	series.code1 = codes[codeiter]
	codeiter = codeiter + 1
	series.code2 = codes[codeiter]
	codeiter = codeiter + 1
	series.code3 = codes[codeiter]
	codeiter = codeiter + 1
	seriesiter = seriesiter + 1
	series.save()

	series = PlayoffGames()
	series.roundof= 8
	series.identifier = seriesiter
	series.code1 = codes[codeiter]
	codeiter = codeiter + 1
	series.code2 = codes[codeiter]
	codeiter = codeiter + 1
	series.code3 = codes[codeiter]
	codeiter = codeiter + 1
	seriesiter = seriesiter + 1
	series.save()
	#round of 4
	series = PlayoffGames()
	series.roundof= 4
	series.identifier = seriesiter
	series.code1 = codes[codeiter]
	codeiter = codeiter + 1
	series.code2 = codes[codeiter]
	codeiter = codeiter + 1
	series.code3 = codes[codeiter]
	codeiter = codeiter + 1
	seriesiter = seriesiter + 1
	series.save()

	series = PlayoffGames()
	series.roundof= 4
	series.identifier = seriesiter
	series.code1 = codes[codeiter]
	codeiter = codeiter + 1
	series.code2 = codes[codeiter]
	codeiter = codeiter + 1
	series.code3 = codes[codeiter]
	codeiter = codeiter + 1
	seriesiter = seriesiter + 1
	series.save()
	#finals
	series = PlayoffGames()
	series.roundof= 2
	series.identifier = seriesiter
	series.code1 = codes[codeiter]
	codeiter = codeiter + 1
	series.code2 = codes[codeiter]
	codeiter = codeiter + 1
	series.code3 = codes[codeiter]
	codeiter = codeiter + 1
	series.code4 = codes[codeiter]
	codeiter = codeiter + 1
	series.code5 = codes[codeiter]
	codeiter = codeiter + 1
	seriesiter = seriesiter + 1
	series.save()

@permission_required('ols.olsadmin')
def generatecodes(request):
	#6365 is spring tournament ID
	baseriotapi.set_region("NA")
	baseriotapi.set_api_key("APIKEY")
	baseriotapi.set_tournament_api_key("APIKEY")
	weeks = 5
	gamesperweek = 12
	codecount = weeks * gamesperweek * 2
	codes = baseriotapi.create_tournament_codes(6365, count=codecount)
	i = 0
	weekcount = 0
	for week in Week.objects.all():
		savecode = TourneyCode()
		savecode.team1 =  week.L0game1t1
		savecode.team2 =  week.L0game1t2
		savecode.code = codes[i]
		savecode.week = weekcount
		savecode.league = 0
		savecode.game = 1
		savecode.rift = 0
		savecode.save()
		i = i + 1
		savecode = TourneyCode()
		savecode.team1 =  week.L0game1t1
		savecode.team2 =  week.L0game1t2
		savecode.code = codes[i]
		savecode.week = weekcount
		savecode.league = 0
		savecode.game = 1
		savecode.rift = 1
		savecode.save()
		i = i + 1
		savecode = TourneyCode()

		savecode.team1 =  week.L0game2t1
		savecode.team2 =  week.L0game2t2
		savecode.code = codes[i]
		savecode.week = weekcount
		savecode.league = 0
		savecode.game = 2
		savecode.rift = 0
		savecode.save()
		i = i + 1
		savecode = TourneyCode()

		savecode.team1 =  week.L0game2t1
		savecode.team2 =  week.L0game2t2
		savecode.code = codes[i]
		savecode.week = weekcount
		savecode.league = 0
		savecode.game = 2
		savecode.rift = 1
		savecode.save()
		i = i + 1
		savecode = TourneyCode()

		savecode.team1 =  week.L0game3t1
		savecode.team2 =  week.L0game3t2
		savecode.code = codes[i]
		savecode.week = weekcount
		savecode.league = 0
		savecode.game = 3
		savecode.rift = 0
		savecode.save()
		i = i + 1
		savecode = TourneyCode()

		savecode.team1 =  week.L0game3t1
		savecode.team2 =  week.L0game3t2
		savecode.code = codes[i]
		savecode.week = weekcount
		savecode.league = 0
		savecode.game = 3
		savecode.rift = 1
		savecode.save()
		i = i + 1
		savecode = TourneyCode()

		savecode.team1 =  week.L1game1t1
		savecode.team2 =  week.L1game1t2
		savecode.code = codes[i]
		savecode.week = weekcount
		savecode.league = 1
		savecode.game = 1
		savecode.rift = 0
		savecode.save()
		i = i + 1
		savecode = TourneyCode()

		savecode.team1 =  week.L1game1t1
		savecode.team2 =  week.L1game1t2
		savecode.code = codes[i]
		savecode.week = weekcount
		savecode.league = 1
		savecode.game = 1
		savecode.rift = 1
		savecode.save()
		i = i + 1
		savecode = TourneyCode()

		savecode.team1 =  week.L1game2t1
		savecode.team2 =  week.L1game2t2
		savecode.code = codes[i]
		savecode.week = weekcount
		savecode.league = 1
		savecode.game = 2
		savecode.rift = 0
		savecode.save()
		i = i + 1
		savecode = TourneyCode()

		savecode.team1 =  week.L1game2t1
		savecode.team2 =  week.L1game2t2
		savecode.code = codes[i]
		savecode.week = weekcount
		savecode.league = 1
		savecode.game = 2
		savecode.rift = 1
		savecode.save()
		i = i + 1
		savecode = TourneyCode()

		savecode.team1 =  week.L1game3t1
		savecode.team2 =  week.L1game3t2
		savecode.code = codes[i]
		savecode.week = weekcount
		savecode.league = 1
		savecode.game = 3
		savecode.rift = 0
		savecode.save()
		i = i + 1
		savecode = TourneyCode()

		savecode.team1 =  week.L1game3t1
		savecode.team2 =  week.L1game3t2
		savecode.code = codes[i]
		savecode.week = weekcount
		savecode.league = 1
		savecode.game = 3
		savecode.rift = 1
		savecode.save()
		i = i + 1
		savecode = TourneyCode()

		savecode.team1 =  week.L2game1t1
		savecode.team2 =  week.L2game1t2
		savecode.code = codes[i]
		savecode.week = weekcount
		savecode.league = 2
		savecode.game = 1
		savecode.rift = 0
		savecode.save()
		i = i + 1
		savecode = TourneyCode()

		savecode.team1 =  week.L2game1t1
		savecode.team2 =  week.L2game1t2
		savecode.code = codes[i]
		savecode.week = weekcount
		savecode.league = 2
		savecode.game = 1
		savecode.rift = 1
		savecode.save()
		i = i + 1
		savecode = TourneyCode()

		savecode.team1 =  week.L2game2t1
		savecode.team2 =  week.L2game2t2
		savecode.code = codes[i]
		savecode.week = weekcount
		savecode.league = 2
		savecode.game = 2
		savecode.rift = 0
		savecode.save()
		i = i + 1
		savecode = TourneyCode()

		savecode.team1 =  week.L2game2t1
		savecode.team2 =  week.L2game2t2
		savecode.code = codes[i]
		savecode.week = weekcount
		savecode.league = 2
		savecode.game = 2
		savecode.rift = 1
		savecode.save()
		i = i + 1
		savecode = TourneyCode()

		savecode.team1 =  week.L2game3t1
		savecode.team2 =  week.L2game3t2
		savecode.code = codes[i]
		savecode.week = weekcount
		savecode.league = 2
		savecode.game = 3
		savecode.rift = 0
		savecode.save()
		i = i + 1
		savecode = TourneyCode()

		savecode.team1 =  week.L2game3t1
		savecode.team2 =  week.L2game3t2
		savecode.code = codes[i]
		savecode.week = weekcount
		savecode.league = 2
		savecode.game = 3
		savecode.rift = 1
		savecode.save()
		i = i + 1
		savecode = TourneyCode()

		savecode.team1 =  week.L3game1t1
		savecode.team2 =  week.L3game1t2
		savecode.code = codes[i]
		savecode.week = weekcount
		savecode.league = 3
		savecode.game = 1
		savecode.rift = 0
		savecode.save()
		i = i + 1
		savecode = TourneyCode()

		savecode.team1 =  week.L3game1t1
		savecode.team2 =  week.L3game1t2
		savecode.code = codes[i]
		savecode.week = weekcount
		savecode.league = 3
		savecode.game = 1
		savecode.rift = 1
		savecode.save()
		i = i + 1
		savecode = TourneyCode()

		savecode.team1 =  week.L3game2t1
		savecode.team2 =  week.L3game2t2
		savecode.code = codes[i]
		savecode.week = weekcount
		savecode.league = 3
		savecode.game = 2
		savecode.rift = 0
		savecode.save()
		i = i + 1
		savecode = TourneyCode()

		savecode.team1 =  week.L3game2t1
		savecode.team2 =  week.L3game2t2
		savecode.code = codes[i]
		savecode.week = weekcount
		savecode.league = 3
		savecode.game = 2
		savecode.rift = 1
		savecode.save()
		i = i + 1
		savecode = TourneyCode()

		savecode.team1 =  week.L3game3t1
		savecode.team2 =  week.L3game3t2
		savecode.code = codes[i]
		savecode.week = weekcount
		savecode.league = 3
		savecode.game = 3
		savecode.rift = 0
		savecode.save()
		i = i + 1
		savecode = TourneyCode()

		savecode.team1 =  week.L3game3t1
		savecode.team2 =  week.L3game3t2
		savecode.code = codes[i]
		savecode.week = weekcount
		savecode.league = 3
		savecode.game = 3
		savecode.rift = 1
		savecode.save()
		i = i + 1
		savecode = TourneyCode()
		weekcount = weekcount + 1
'''
def swaprift1s(request):
	rift1s = TourneyCode.objects.filter(rift= 1)
	for code in rift1s:
		print(code)
		t1temp = code.team1
		print(t1temp)
		code.team1 = code.team2
		code.team2 = t1temp
		code.save()
	return HttpResponse("games swipped")
'''
  #                                                       CAPTAIN VIEWS


@csrf_exempt
def callback(request):
	print("received request")
	posted = request.body.decode('utf-8')
	#print(dir(posted))
	print(posted)
	#with open('olsrunner/tests/gabetest.pk', 'wb') as outfile:
	#	pickle.dump( posted , outfile)
	gameparse = json.loads(posted)
	riotapi.set_region("NA")
	riotapi.set_api_key("APIKEY")
	riotapi.set_tournament_api_key("APIKEY")
	#print(gameparse['shortCode'])
	try:
		m = riotapi.get_match(gameparse['gameId'], tournament_code=gameparse['shortCode'])
	except APIError:
		return HttpResponseServerError("match was not yet published")
	#print(gameparse)
	newgame = Game()
	try:
		code = TourneyCode.objects.get(code = gameparse['shortCode'])
	except ObjectDoesNotExist:  # If this is playoff game
		playoff = PlayoffGames.objects.get(Q(code1 = gameparse['shortCode']) | Q(code2 = gameparse['shortCode']) | Q(code3 = gameparse['shortCode']) | Q(code4 = gameparse['shortCode']) | Q(code5 = gameparse['shortCode']))
		if (playoff.code1 == gameparse['shortCode'] or playoff.code3 == gameparse['shortCode']) or playoff.code5 == gameparse['shortCode']:
			newgame.team1 = playoff.team1
			team1obj = Team.objects.get(teamID = newgame.team1)
			newgame.team2 = playoff.team2
			team2obj = Team.objects.get(teamID = newgame.team2)
		elif playoff.code2 == gameparse['shortCode'] or playoff.code4 == gameparse['shortCode']:
			newgame.team1 = playoff.team2
			team1obj = Team.objects.get(teamID = newgame.team1)
			newgame.team2 = playoff.team1
			team2obj = Team.objects.get(teamID = newgame.team2)

		for p in gameparse['winningTeam']:
			print(p)
			if (p['summonerId']  == team1obj.CaptainID or p['summonerId']  == team1obj.Player1ID) or ((p['summonerId']  == team1obj.Player2ID or p['summonerId']  == team1obj.Player3ID) or p['summonerId']  == team1obj.Player4ID):
				newgame.winner = newgame.team1
				break
			if (p['summonerId']  == team2obj.CaptainID or (p['summonerId']  == team2obj.Player1ID or p['summonerId']  == team2obj.Player2ID)) or (p['summonerId']  == team2obj.Player3ID or p['summonerId']  == team2obj.Player4ID):
				newgame.winner = newgame.team2
				break
		newgame.Number = Game.objects.all().aggregate(Max('Number'))['Number__max'] + 1
		if newgame.team2 == newgame.winner:
			loser = team1obj
			winner = team2obj
			position = 2
		else:
			winner = team1obj
			loser = team2obj
			position = 1
		if playoff.team1 == newgame.winner:
			playoff.team1wins = playoff.team1wins + 1
		if playoff.team2 == newgame.winner:
			playoff.team2wins = playoff.team2wins + 1
		newgame.team1Player1 = riotapi.get_summoner_by_name(m.participants[0].summoner_name).id
		newgame.team1Player2 = riotapi.get_summoner_by_name(m.participants[1].summoner_name).id
		newgame.team1Player3 = riotapi.get_summoner_by_name(m.participants[2].summoner_name).id
		newgame.team1Player4 = riotapi.get_summoner_by_name(m.participants[3].summoner_name).id
		newgame.team1Player5 = riotapi.get_summoner_by_name(m.participants[4].summoner_name).id
		newgame.team2Player1 = riotapi.get_summoner_by_name(m.participants[5].summoner_name).id
		newgame.team2Player2 = riotapi.get_summoner_by_name(m.participants[6].summoner_name).id
		newgame.team2Player3 = riotapi.get_summoner_by_name(m.participants[7].summoner_name).id
		newgame.team2Player4 = riotapi.get_summoner_by_name(m.participants[8].summoner_name).id
		newgame.team2Player5 = riotapi.get_summoner_by_name(m.participants[9].summoner_name).id

		newgame.matchID = gameparse['gameId']
		with open('olsrunner/matches/' + str(newgame.Number) + '.pk', 'wb') as outfile:
			pickle.dump( m , outfile)
		newgame.filename = 'olsrunner/matches/' + str(newgame.Number) + '.pk'
		newgame.save()
		if playoff.code1 == gameparse['shortCode']:
			playoff.match1 = newgame.Number
		if playoff.code2 == gameparse['shortCode']:
			playoff.match2 = newgame.Number
		if playoff.code3 == gameparse['shortCode']:
			playoff.match3 = newgame.Number
		if playoff.code4 == gameparse['shortCode']:
			playoff.match4 = newgame.Number
		if playoff.code5 == gameparse['shortCode']:
			playoff.match5 = newgame.Number

		playoff.save()
		if playoff.code4 == None and (playoff.team1wins >= 2 or playoff.team2wins >= 2): #This is a 3 game series that was won
			if playoff.identifier < 8:
				playoffadvance = PlayoffGames.objects.get(identifier = (playoff.identifier //2) +8)
			elif playoff.identifier < 12:
				playoffadvance = PlayoffGames.objects.get(identifier = ((playoff.identifier-8)//2)+12 )
			else:
				playoffadvance = PlayoffGames.objects.get(identifier = 14)
			if playoffadvance.team1:
				advanced = Team.objects.get(teamID= playoffadvance.team1)
				advancedpoints = advanced.points
				if playoff.team1wins >= 2:
					if Team.objects.get(teamID = playoff.team1).points > advancedpoints:
						playoffadvance.team2 = advanced.teamID
						playoffadvance.team1 = playoff.team1
					elif Team.objects.get(teamID = playoff.team1).points < advancedpoints:
						playoffadvance.team1 = advanced.teamID
						playoffadvance.team2 = playoff.team1
					else:
						if random.randint(1,2) == 1:
							playoffadvance.team2 = advanced.teamID
							playoffadvance.team1 = playoff.team1
						else:
							playoffadvance.team1 = advanced.teamID
							playoffadvance.team2 = playoff.team1
				else:
					if Team.objects.get(teamID = playoff.team2).points > advancedpoints:
						playoffadvance.team2 = advanced.teamID
						playoffadvance.team1 = playoff.team2
					elif Team.objects.get(teamID = playoff.team2).points < advancedpoints:
						playoffadvance.team1 = advanced.teamID
						playoffadvance.team2 = playoff.team2
					else:
						if random.randint(1,2) == 1:
							playoffadvance.team2 = advanced.teamID
							playoffadvance.team1 = playoff.team2
						else:
							playoffadvance.team1 = advanced.teamID
							playoffadvance.team2 = playoff.team2
			else:
				if playoff.team1wins >= 2:
					playoffadvance.team1 = playoff.team1
				else:
					playoffadvance.team1 = playoff.team2
			playoffadvance.save()
		return HttpResponse("match added")

	newgame.team1 = code.team1 #WCC
	team1obj = Team.objects.get(teamID = newgame.team1)
	newgame.team2 = code.team2  #CAH
	team2obj = Team.objects.get(teamID = newgame.team2)
	j = 0
	for p in gameparse['winningTeam']:
		print(p)
		if p['summonerId']  == team1obj.CaptainID:
			newgame.winner = newgame.team1
			break
		if p['summonerId']  == team1obj.Player1ID:
			newgame.winner = newgame.team1
			break
		if p['summonerId']  == team1obj.Player2ID:
			newgame.winner = newgame.team1
			break
		if p['summonerId']  == team1obj.Player3ID:
			newgame.winner = newgame.team1
			break
		if p['summonerId']  == team1obj.Player4ID:
			newgame.winner = newgame.team1
			break
		if p['summonerId']  == team2obj.CaptainID:
			newgame.winner = newgame.team2
			break
		if p['summonerId']  == team2obj.Player1ID:
			newgame.winner = newgame.team2
			break
		if p['summonerId']  == team2obj.Player2ID:
			newgame.winner = newgame.team2
			break
		if p['summonerId']  == team2obj.Player3ID:
			newgame.winner = newgame.team2
			break
		if p['summonerId']  == team2obj.Player4ID:
			newgame.winner = newgame.team2
			break
		j = j+1

	try:
		newgame.Number = Game.objects.all().aggregate(Max('Number'))['Number__max'] + 1
	except KeyError:
		newgame.Number = 0
	if newgame.team2 == newgame.winner:
		loser = team1obj
		winner = team2obj
		position = 2
	else:
		winner = team1obj
		loser = team2obj
		position = 1
	addPoints(winner, loser, position)
	'''if position == 1:
		newgame.team1Player1 = gameparse['winningTeam'][0]['summonerId']
		newgame.team1Player2 = gameparse['winningTeam'][1]['summonerId']
		newgame.team1Player3 = gameparse['winningTeam'][2]['summonerId']
		newgame.team1Player4 = gameparse['winningTeam'][3]['summonerId']
		newgame.team1Player5 = gameparse['winningTeam'][4]['summonerId']
		newgame.team2Player1 = gameparse['losingTeam'][0]['summonerId']
		newgame.team2Player2 = gameparse['losingTeam'][1]['summonerId']
		newgame.team2Player3 = gameparse['losingTeam'][2]['summonerId']
		newgame.team2Player4 = gameparse['losingTeam'][3]['summonerId']
		newgame.team2Player5 = gameparse['losingTeam'][4]['summonerId']
	else:
		newgame.team1Player1 = gameparse['losingTeam'][0]['summonerId']
		newgame.team1Player2 = gameparse['losingTeam'][1]['summonerId']
		newgame.team1Player3 = gameparse['losingTeam'][2]['summonerId']
		newgame.team1Player4 = gameparse['losingTeam'][3]['summonerId']
		newgame.team1Player5 = gameparse['losingTeam'][4]['summonerId']
		newgame.team2Player1 = gameparse['winningTeam'][0]['summonerId']
		newgame.team2Player2 = gameparse['winningTeam'][1]['summonerId']
		newgame.team2Player3 = gameparse['winningTeam'][2]['summonerId']
		newgame.team2Player4 = gameparse['winningTeam'][3]['summonerId']
		newgame.team2Player5 = gameparse['winningTeam'][4]['summonerId']'''
	newgame.team1Player1 = riotapi.get_summoner_by_name(m.participants[0].summoner_name).id
	newgame.team1Player2 = riotapi.get_summoner_by_name(m.participants[1].summoner_name).id
	newgame.team1Player3 = riotapi.get_summoner_by_name(m.participants[2].summoner_name).id
	newgame.team1Player4 = riotapi.get_summoner_by_name(m.participants[3].summoner_name).id
	newgame.team1Player5 = riotapi.get_summoner_by_name(m.participants[4].summoner_name).id
	newgame.team2Player1 = riotapi.get_summoner_by_name(m.participants[5].summoner_name).id
	newgame.team2Player2 = riotapi.get_summoner_by_name(m.participants[6].summoner_name).id
	newgame.team2Player3 = riotapi.get_summoner_by_name(m.participants[7].summoner_name).id
	newgame.team2Player4 = riotapi.get_summoner_by_name(m.participants[8].summoner_name).id
	newgame.team2Player5 = riotapi.get_summoner_by_name(m.participants[9].summoner_name).id

	newgame.matchID = gameparse['gameId']
	i = 0
	for player in m.participants:
		try:
			if i==0:
				st = Stats.objects.get(PlayerID=newgame.team1Player1)
			if i==1:
				st = Stats.objects.get(PlayerID=newgame.team1Player2)
			if i==2:
				st = Stats.objects.get(PlayerID=newgame.team1Player3)
			if i==3:
				st = Stats.objects.get(PlayerID=newgame.team1Player4)
			if i==4:
				st = Stats.objects.get(PlayerID=newgame.team1Player5)
			if i==5:
				st = Stats.objects.get(PlayerID=newgame.team2Player1)
			if i==6:
				st = Stats.objects.get(PlayerID=newgame.team2Player2)
			if i==7:
				st = Stats.objects.get(PlayerID=newgame.team2Player3)
			if i==8:
				st = Stats.objects.get(PlayerID=newgame.team2Player4)
			if i==9:
				st = Stats.objects.get(PlayerID=newgame.team2Player5)
		except:
			st = Stats()
			st.PlayerID = riotapi.get_summoner_by_name(player.summoner_name).id
		i= i+ 1
		st.Kills = st.Kills + player.stats.kills
		st.Deaths = st.Deaths + player.stats.deaths
		st.Assists = st.Assists + player.stats.assists
		st.GoldTotal = st.GoldTotal + player.stats.gold_earned
		st.GamesPlayed = st.GamesPlayed + 1
		if player.stats.largest_critical_strike > st.LargestCrit:
			st.LargestCrit = player.stats.largest_critical_strike
		st.Creeps = st.Creeps + player.stats.minion_kills + player.stats.monster_kills
		st.SecondsPlayed = st.SecondsPlayed + m.duration.total_seconds()
		st.DamageDealt = st.DamageDealt + player.stats.damage_dealt_to_champions
		st.DamageReceived = st.DamageReceived + player.stats.damage_taken
		if i <= 5:
			st.TeamKillTotal =  st.TeamKillTotal + m.participants[0].stats.kills  + m.participants[1].stats.kills  + m.participants[2].stats.kills  + m.participants[3].stats.kills  + m.participants[4].stats.kills
		else:
			st.TeamKillTotal =  st.TeamKillTotal + m.participants[5].stats.kills  + m.participants[6].stats.kills  + m.participants[7].stats.kills  + m.participants[8].stats.kills  + m.participants[9].stats.kills
		st.DoubleKills =  st.DoubleKills + player.stats.double_kills
		st.TripleKills = st.TripleKills + player.stats.triple_kills
		st.QuadraKills = st.QuadraKills + player.stats.quadra_kills
		st.PentaKills = st.PentaKills + player.stats.penta_kills
		st.save()
	with open('olsrunner/matches/' + str(newgame.Number) + '.pk', 'wb') as outfile:
		pickle.dump( m , outfile)
	newgame.filename = 'olsrunner/matches/' + str(newgame.Number) + '.pk'
	newgame.save()
	return HttpResponse("match added")


def reschedule(request):
	posted = request.POST
	print(posted)
	match = posted['match']
	matchs = match.split('|')
	weeks = Week.objects.all().order_by('startdate')
	timeof= None
	print(weeks)
	#print(matchs[0])
	#print(matchs[1])
	try:
		dateof = datetime.strptime(posted['date'], '%m/%d/%Y')
	except ValueError:
		dateof = datetime.strptime(posted['date'], '%b. %d, %Y')
	am = re.compile('[0-9]{1,2}:[0-9]{2} a.m.')
	if am.match(posted['time']) is not None:
		timeof = datetime.strptime(posted['time'], '%I:%M a.m.')
	pm = re.compile('[0-9]{1,2}:[0-9]{2} p.m.')
	if pm.match(posted['time']) is not None:
		timeof = datetime.strptime(posted['time'], '%I:%M p.m.')
		timeof = timeof +timedelta(hours=12)
	am = re.compile('[0-9]{1,2}:[0-9]{2} am')
	if am.match(posted['time']) is not None:
		timeof = datetime.strptime(posted['time'], '%I:%M am')
	pm = re.compile('[0-9]{1,2}:[0-9]{2} pm')
	if pm.match(posted['time']) is not None:
		timeof = datetime.strptime(posted['time'], '%I:%M pm')
		timeof = timeof +timedelta(hours=12)
	am = re.compile('[0-9]{1,2}:[0-9]{2} AM')
	if am.match(posted['time']) is not None:
		timeof = datetime.strptime(posted['time'], '%I:%M AM')
	pm = re.compile('[0-9]{1,2}:[0-9]{2} PM')
	if pm.match(posted['time']) is not None:
		timeof = datetime.strptime(posted['time'], '%I:%M PM')
		timeof = timeof +timedelta(hours=12)
	am = re.compile('[0-9]{1,2} a.m.')
	if am.match(posted['time']) is not None:
		timeof = datetime.strptime(posted['time'], '%I a.m.')
	pm = re.compile('[0-9]{1,2} p.m.')
	if pm.match(posted['time']) is not None:
		timeof = datetime.strptime(posted['time'], '%I p.m.')
		timeof = timeof +timedelta(hours=12)
	am = re.compile('[0-9]{1,2} am')
	if am.match(posted['time']) is not None:
		timeof = datetime.strptime(posted['time'], '%I am')
	pm = re.compile('[0-9]{1,2} pm')
	if pm.match(posted['time']) is not None:
		timeof = datetime.strptime(posted['time'], '%I pm')
		timeof = timeof +timedelta(hours=12)
	am = re.compile('[0-9]{1,2} AM')
	if am.match(posted['time']) is not None:
		timeof = datetime.strptime(posted['time'], '%I AM')
	pm = re.compile('[0-9]{1,2} PM')
	if pm.match(posted['time']) is not None:
		timeof = datetime.strptime(posted['time'], '%I PM')
		timeof = timeof +timedelta(hours=12)
	#nospaces
	am = re.compile('[0-9]{1,2}:[0-9]{2}a.m.')
	if am.match(posted['time']) is not None:
		timeof = datetime.strptime(posted['time'], '%I:%Ma.m.')
	pm = re.compile('[0-9]{1,2}:[0-9]{2}p.m.')
	if pm.match(posted['time']) is not None:
		timeof = datetime.strptime(posted['time'], '%I:%Mp.m.')
		timeof = timeof +timedelta(hours=12)
	am = re.compile('[0-9]{1,2}:[0-9]{2}am')
	if am.match(posted['time']) is not None:
		timeof = datetime.strptime(posted['time'], '%I:%Mam')
	pm = re.compile('[0-9]{1,2}:[0-9]{2}pm')
	if pm.match(posted['time']) is not None:
		timeof = datetime.strptime(posted['time'], '%I:%Mpm')
		timeof = timeof +timedelta(hours=12)
	am = re.compile('[0-9]{1,2}:[0-9]{2}AM')
	if am.match(posted['time']) is not None:
		timeof = datetime.strptime(posted['time'], '%I:%MAM')
	pm = re.compile('[0-9]{1,2}:[0-9]{2}PM')
	if pm.match(posted['time']) is not None:
		timeof = datetime.strptime(posted['time'], '%I:%MPM')
		timeof = timeof +timedelta(hours=12)
	am = re.compile('[0-9]{1,2}a.m.')
	if am.match(posted['time']) is not None:
		timeof = datetime.strptime(posted['time'], '%Ia.m.')
	pm = re.compile('[0-9]{1,2}p.m.')
	if pm.match(posted['time']) is not None:
		timeof = datetime.strptime(posted['time'], '%Ip.m.')
		timeof = timeof +timedelta(hours=12)
	am = re.compile('[0-9]{1,2}am')
	if am.match(posted['time']) is not None:
		timeof = datetime.strptime(posted['time'], '%Iam')
	pm = re.compile('[0-9]{1,2}pm')
	if pm.match(posted['time']) is not None:
		timeof = datetime.strptime(posted['time'], '%Ipm')
		timeof = timeof +timedelta(hours=12)
	am = re.compile('[0-9]{1,2}AM')
	if am.match(posted['time']) is not None:
		timeof = datetime.strptime(posted['time'], '%IAM')
	pm = re.compile('[0-9]{1,2}PM')
	if pm.match(posted['time']) is not None:
		timeof = datetime.strptime(posted['time'], '%IPM')
		timeof = timeof +timedelta(hours=12)
	if timeof is None:
		return HttpResponse("time entry was not formatted properly, please use: 10:00 p.m. as an example ")
	#timeof = timeof.strftime('%H:%M:%S')
	#timeof = timeof.time
	#dateof = dateof.strftime('%Y-%m-%d')
	#dateof = dateof.date
	week = weeks[int(matchs[0])-1] #this gets the week list
	if week.L0game1t1==int(matchs[1]): #if team1 matches
		week.L0game1Time = timeof
		week.L0game1date = dateof
	if week.L0game2t1==int(matchs[1]):
		week.L0game2Time = timeof
		week.L0game2date = dateof
	if week.L0game3t1==int(matchs[1]):
		week.L0game3Time = timeof
		week.L0game3date = dateof
	if week.L1game1t1==int(matchs[1]):
		week.L1game1Time = timeof
		week.L1game1date = dateof
	if week.L1game2t1==int(matchs[1]):
		week.L1game2Time = timeof
		week.L1game2date = dateof
	if week.L1game3t1==int(matchs[1]):
		week.L1game3Time = timeof
		week.L1game3date = dateof
	if week.L2game1t1==int(matchs[1]):
		week.L2game1Time = timeof
		week.L2game1date = dateof
	if week.L2game2t1==int(matchs[1]):
		week.L2game2Time = timeof
		week.L2game2date = dateof
	if week.L2game3t1==int(matchs[1]):
		week.L2game3Time = timeof
		week.L2game3date = dateof
	if week.L3game1t1==int(matchs[1]):
		week.L3game1Time = timeof
		week.L3game1date = dateof
	if week.L3game2t1==int(matchs[1]):
		week.L3game2Time = timeof
		week.L3game2date = dateof
	if week.L3game3t1==int(matchs[1]):
		week.L3game3Time = timeof
		week.L3game3date = dateof
	print("final check")
	#import pdb; pdb.set_trace()
	week.save()
	#print(connection.queries)
	return HttpResponseRedirect('/ols/schedule/')



def rescheduleplayoffs(request):
	posted = request.POST
	match = posted['match']
	timeof= None
	#print(matchs[0])
	#print(matchs[1])
	try:
		dateof = datetime.strptime(posted['date'], '%m/%d/%Y')
	except ValueError:
		dateof = datetime.strptime(posted['date'], '%b. %d, %Y')
	am = re.compile('[0-9]{1,2}:[0-9]{2} a.m.')
	if am.match(posted['time']) is not None:
		timeof = datetime.strptime(posted['time'], '%I:%M a.m.')
	pm = re.compile('[0-9]{1,2}:[0-9]{2} p.m.')
	if pm.match(posted['time']) is not None:
		timeof = datetime.strptime(posted['time'], '%I:%M p.m.')
		timeof = timeof +timedelta(hours=12)
	am = re.compile('[0-9]{1,2}:[0-9]{2} am')
	if am.match(posted['time']) is not None:
		timeof = datetime.strptime(posted['time'], '%I:%M am')
	pm = re.compile('[0-9]{1,2}:[0-9]{2} pm')
	if pm.match(posted['time']) is not None:
		timeof = datetime.strptime(posted['time'], '%I:%M pm')
		timeof = timeof +timedelta(hours=12)
	am = re.compile('[0-9]{1,2}:[0-9]{2} AM')
	if am.match(posted['time']) is not None:
		timeof = datetime.strptime(posted['time'], '%I:%M AM')
	pm = re.compile('[0-9]{1,2}:[0-9]{2} PM')
	if pm.match(posted['time']) is not None:
		timeof = datetime.strptime(posted['time'], '%I:%M PM')
		timeof = timeof +timedelta(hours=12)
	am = re.compile('[0-9]{1,2} a.m.')
	if am.match(posted['time']) is not None:
		timeof = datetime.strptime(posted['time'], '%I a.m.')
	pm = re.compile('[0-9]{1,2} p.m.')
	if pm.match(posted['time']) is not None:
		timeof = datetime.strptime(posted['time'], '%I p.m.')
		timeof = timeof +timedelta(hours=12)
	am = re.compile('[0-9]{1,2} am')
	if am.match(posted['time']) is not None:
		timeof = datetime.strptime(posted['time'], '%I am')
	pm = re.compile('[0-9]{1,2} pm')
	if pm.match(posted['time']) is not None:
		timeof = datetime.strptime(posted['time'], '%I pm')
		timeof = timeof +timedelta(hours=12)
	am = re.compile('[0-9]{1,2} AM')
	if am.match(posted['time']) is not None:
		timeof = datetime.strptime(posted['time'], '%I AM')
	pm = re.compile('[0-9]{1,2} PM')
	if pm.match(posted['time']) is not None:
		timeof = datetime.strptime(posted['time'], '%I PM')
		timeof = timeof +timedelta(hours=12)
	#nospaces
	am = re.compile('[0-9]{1,2}:[0-9]{2}a.m.')
	if am.match(posted['time']) is not None:
		timeof = datetime.strptime(posted['time'], '%I:%Ma.m.')
	pm = re.compile('[0-9]{1,2}:[0-9]{2}p.m.')
	if pm.match(posted['time']) is not None:
		timeof = datetime.strptime(posted['time'], '%I:%Mp.m.')
		timeof = timeof +timedelta(hours=12)
	am = re.compile('[0-9]{1,2}:[0-9]{2}am')
	if am.match(posted['time']) is not None:
		timeof = datetime.strptime(posted['time'], '%I:%Mam')
	pm = re.compile('[0-9]{1,2}:[0-9]{2}pm')
	if pm.match(posted['time']) is not None:
		timeof = datetime.strptime(posted['time'], '%I:%Mpm')
		timeof = timeof +timedelta(hours=12)
	am = re.compile('[0-9]{1,2}:[0-9]{2}AM')
	if am.match(posted['time']) is not None:
		timeof = datetime.strptime(posted['time'], '%I:%MAM')
	pm = re.compile('[0-9]{1,2}:[0-9]{2}PM')
	if pm.match(posted['time']) is not None:
		timeof = datetime.strptime(posted['time'], '%I:%MPM')
		timeof = timeof +timedelta(hours=12)
	am = re.compile('[0-9]{1,2}a.m.')
	if am.match(posted['time']) is not None:
		timeof = datetime.strptime(posted['time'], '%Ia.m.')
	pm = re.compile('[0-9]{1,2}p.m.')
	if pm.match(posted['time']) is not None:
		timeof = datetime.strptime(posted['time'], '%Ip.m.')
		timeof = timeof +timedelta(hours=12)
	am = re.compile('[0-9]{1,2}am')
	if am.match(posted['time']) is not None:
		timeof = datetime.strptime(posted['time'], '%Iam')
	pm = re.compile('[0-9]{1,2}pm')
	if pm.match(posted['time']) is not None:
		timeof = datetime.strptime(posted['time'], '%Ipm')
		timeof = timeof +timedelta(hours=12)
	am = re.compile('[0-9]{1,2}AM')
	if am.match(posted['time']) is not None:
		timeof = datetime.strptime(posted['time'], '%IAM')
	pm = re.compile('[0-9]{1,2}PM')
	if pm.match(posted['time']) is not None:
		timeof = datetime.strptime(posted['time'], '%IPM')
		timeof = timeof +timedelta(hours=12)
	if timeof is None:
		return HttpResponse("time entry was not formatted properly, please use: 10:00 p.m. as an example ")
	#timeof = timeof.strftime('%H:%M:%S')
	#timeof = timeof.time
	#dateof = dateof.strftime('%Y-%m-%d')
	#dateof = dateof.date
	series = PlayoffGames.objects.get(identifier=match)
	series.date = dateof
	series.time = timeof
	#import pdb; pdb.set_trace()
	series.save()
	#print(connection.queries)
	return HttpResponseRedirect('/ols/playoffs/')

		#                                                     GENERAL VIEWS

class StatsTable(tables.Table):
	row_number = tables.Column(empty_values=(), verbose_name='Row')
	team = tables.Column(accessor='team', verbose_name='Team',attrs={"th": {"id": "Team"}} )
	name = tables.Column(accessor='Name', verbose_name='IGN', order_by='name_lower',attrs={"th": {"id": "name"}})
	kills = tables.Column(accessor='Kills', verbose_name='K', order_by='-Kills',attrs={"th": {"id": "kills"}})
	death = tables.Column(accessor='Deaths', verbose_name='D',attrs={"th": {"id": "death"}})
	assists = tables.Column(accessor='Assists',verbose_name='A', order_by='-Assists',attrs={"th": {"id": "assists"}})
	kda = tables.Column(accessor='KDA', verbose_name='KDA ratio', order_by='-KDA',attrs={"th": {"id": "kda"}})
	partic = tables.Column(accessor='participation', verbose_name='Kill Participation', order_by='-participation',attrs={"th": {"id": "kpart"}})
	gold = tables.Column(accessor='Gold per minute', verbose_name='GPM', order_by='-Gold per minute',attrs={"th": {"id": "gold"}})
	games = tables.Column(accessor='Games Played', verbose_name='Games Played', order_by='-Games Played',attrs={"th": {"id": "gametotal"}})
	creeps = tables.Column(accessor='Creeps per minute', verbose_name='CS per minute', order_by='-Creeps per minute',attrs={"th": {"id": "creeps"}})
	multis = tables.Column(accessor='multis', verbose_name='T/Q/P', order_by=('-p', '-q', '-t'),attrs={"th": {"id": "multikills"}})
	crit = tables.Column(accessor='Largest Critical Strike', verbose_name='Largest Critical', order_by='-Largest Critical Strike',attrs={"th": {"id": "bigcrit"}})
	fantasy = tables.Column(accessor='fantasy', verbose_name='Fantasy', order_by='-fantasy',attrs={"th": {"id": "fantasypoints"}})

	def __init__(self, *args, **kwargs):
		super(StatsTable, self).__init__(*args, **kwargs)
		self.counter = itertools.count()
		next(self.counter)
	def render_row_number(self):
		return '%d' % next(self.counter)

def overallstats(request):
	players = Player.objects.all()
	finalstats = []
	for p in players:
		ptemp = {}
		for t in Team.objects.all():
			if t.CaptainID == p.SummonerNumber:
				ptemp['team']= t.teamName
				break
			if t.Player1ID == p.SummonerNumber:
				ptemp['team']= t.teamName
				break
			if t.Player2ID == p.SummonerNumber:
				ptemp['team']= t.teamName
				break
			if t.Player3ID == p.SummonerNumber:
				ptemp['team']= t.teamName
				break
			if t.Player4ID == p.SummonerNumber:
				ptemp['team']= t.teamName
				break
		ptemp['Name'] =  p.PlayerIGN
		ptemp['name_lower'] = p.PlayerIGN.lower()
		try:
			s = Stats.objects.get(PlayerID= p.SummonerNumber)
			ptemp['Kills'] = round(s.Kills/ s.GamesPlayed, 2)
			ptemp['Deaths'] = round(s.Deaths /s.GamesPlayed, 2)
			ptemp['Assists'] = round(s.Assists / s.GamesPlayed, 2)
			ptemp['Gold per minute'] = round((s.GoldTotal * 60)/s.SecondsPlayed,2)
			ptemp['Games Played'] = s.GamesPlayed
			ptemp['Largest Critical Strike'] = s.LargestCrit
			ptemp['Creeps per minute'] = round((s.Creeps * 60)/s.SecondsPlayed, 2)
			ptemp['participation'] = str(round((s.Kills + s.Assists)/s.TeamKillTotal * 100, 1)) + "%"
			ptemp['t'] = s.TripleKills
			ptemp['q'] = s.QuadraKills
			ptemp['p'] = s.PentaKills
			ptemp['fantasy'] = round((s.Kills * 2) + (s.Deaths * -0.5) + (s.Assists * 1.5) + (s.Creeps * .01) + (s.TripleKills * 2) + (s.QuadraKills * 5) + (s.PentaKills * 10), 2)
			ptemp['multis'] = str(s.TripleKills) + "/" + str(s.QuadraKills) + "/" + str(s.PentaKills)
			try:
				ptemp['KDA'] = round((s.Kills + s.Assists)/s.Deaths, 2)
			except ZeroDivisionError:
				ptemp['KDA'] = 420
		except:
			'''ptemp['Kills'] = 0
			ptemp['Deaths'] = 0
			ptemp['Assists'] = 0
			ptemp['Gold per minute'] = 0
			ptemp['Games Played'] = 0
			ptemp['Largest Critical Strike'] = 0
			ptemp['Creeps per minute'] = 0
			ptemp['KDA'] = 0
			ptemp['participatio']
			'''
		finalstats.append(ptemp)
	statst = StatsTable(finalstats, order_by="team")
	RequestConfig(request, paginate=False).configure(statst)
	return render(request, "overallstats.html", {"stats": statst})


def player_stats(request, player):
	print(player)
	shit = False
	try:
		play = Player.objects.get(SummonerNumber=player)
	except ValueError:
		print('player link with IGN')
		shit = True
	if shit:
		try:
			play = Player.objects.get(PlayerIGN__icontains=player)
		except ObjectDoesNotExist:
			try:
				play = Player.objects.get(PlayerName__icontains=player)
			except ObjectDoesNotExist:
					return HttpResponse("Player not found")
		except MultipleObjectsReturned:
			try:
				play = Player.objects.get(PlayerName__icontains=player)
			except ObjectDoesNotExist:
				return HttpResponse("Your search was too general, multiple players found")
			except MultipleObjectsReturned:
				return HttpResponse("Your search was too general, multiple players found")

	try:
		s = Stats.objects.get(PlayerID=play.SummonerNumber)
	except KeyError:
		return HttpResponse("No stats for this player yet")
	except ObjectDoesNotExist:
		return HttpResponse("No stats for this player yet")

	query = Q(team1Player1= play.SummonerNumber) | Q(team1Player2= play.SummonerNumber) | Q(team1Player3= play.SummonerNumber) | Q(team1Player4= play.SummonerNumber) | Q(team1Player5= play.SummonerNumber) | Q(team2Player1= play.SummonerNumber) | Q(team2Player2= play.SummonerNumber) | Q(team2Player3= play.SummonerNumber) |Q(team2Player4= play.SummonerNumber) | Q(team2Player5= play.SummonerNumber)
	g = Game.objects.filter(query)
	gm = []
	for game in g:
		if game.team1Player1 ==play.SummonerNumber:
			i = 0
		if game.team1Player2 ==play.SummonerNumber:
			i =1
		if game.team1Player3 ==play.SummonerNumber:
			i=2
		if game.team1Player4 ==play.SummonerNumber:
			i=3
		if game.team1Player5 ==play.SummonerNumber:
			i=4
		if game.team2Player1 ==play.SummonerNumber:
			i=5
		if game.team2Player2 ==play.SummonerNumber:
			i=6
		if game.team2Player3 ==play.SummonerNumber:
			i=7
		if game.team2Player4 ==play.SummonerNumber:
			i=8
		if game.team2Player5 ==play.SummonerNumber:
			i=9
		with open(str(game.filename), 'rb') as infile:
			gamefile = pickle.load(infile)
		gm.append({'game': game, 'player':gamefile.participants[i], 'name':str(game)})

	tquery = Q(CaptainID=play.SummonerNumber) | Q(Player1ID=play.SummonerNumber) |  Q(Player2ID=play.SummonerNumber) |  Q(Player3ID=play.SummonerNumber) |  Q(Player4ID=play.SummonerNumber)
	t = Team.objects.get(tquery)
	advancedstats = {}
	try:
		advancedstats['KDA'] = (s.Kills + s.Assists) / s.Deaths
	except:
		advancedstats['KDA'] = 420
	advancedstats['Csmin'] = (s.Creeps* 60) / s.SecondsPlayed
	advancedstats['GPM'] = (s.GoldTotal* 60) / s.SecondsPlayed

	return HttpResponse(render(request, 'playerStats.html', {'player' :play, 'stats': s, 'team': t, 'games': gm, 'astats':advancedstats} ))


def team_stats(request, team):
	t = Team.objects.get(teamID=team)
	blank = Stats()
	players = []
	stats = []
	p1 = Player.objects.get(SummonerNumber=t.CaptainID)
	try:
		print(p1)
		p1s = Stats.objects.get(PlayerID=p1.SummonerNumber)
		print(p1)
	except KeyError:
		p1s = blank
	except ObjectDoesNotExist:
		p1s = blank
	players.append(p1)

	stats.append(p1s)
	print(players)
	p2 = Player.objects.get(SummonerNumber=t.Player1ID)
	print(p2)
	try:
		p2s = Stats.objects.get(PlayerID=p2.SummonerNumber)
	except KeyError:
		p2s = blank
	except ObjectDoesNotExist:
		p2s = blank
	players.append(p2)
	print(players)
	stats.append(p2s)
	p3 = Player.objects.get(SummonerNumber=t.Player2ID)
	try:
		p3s = Stats.objects.get(PlayerID=p3.SummonerNumber)
	except KeyError:
		p3s = blank
	except ObjectDoesNotExist:
		p3s = blank
	players.append(p3)
	print(players)
	stats.append(p3s)
	p4 = Player.objects.get(SummonerNumber=t.Player3ID)
	try:
		p4s = Stats.objects.get(PlayerID=p4.SummonerNumber)
	except KeyError:
		p4s = blank
	except ObjectDoesNotExist:
		p4s = blank
	players.append(p4)
	print(players)
	stats.append(p4s)
	p5 = Player.objects.get(SummonerNumber=t.Player4ID)
	try:
		p5s = Stats.objects.get(PlayerID=p1.SummonerNumber)
	except KeyError:
		p5s = blank
	except ObjectDoesNotExist:
		p5s = blank
	players.append(p5)
	stats.append(p5s)
	print(players)
	teamavgs = {}
	games = Game.objects.filter(Q(team1=t.teamID) | Q(team2 = t.teamID)).order_by('-Number')
	print("riot api starts here")
	gameslist= []
	riotapi.set_region("NA")
	riotapi.set_api_key("APIKEY")
	riotapi.set_load_policy(LoadPolicy.lazy)
	for g in games:
		team1 = Team.objects.get(teamID= g.team1)
		team2 = Team.objects.get(teamID= g.team2)
		if g.winner == t.teamID:
			win = "Won"
		else:
			win = "Lost"
		with open(str(g.filename), 'rb') as infile:
			game = pickle.load(infile)
		print("lag start")
		if g.team1 == t.teamID:
			try:
				b1 = "http://ddragon.leagueoflegends.com/cdn/6.2.1/img/champion/" + game.red_team.bans[0].champion.image.link
			except IndexError:
				b1 = "/static/img/Gabe.png"
			try:
				b2 = "http://ddragon.leagueoflegends.com/cdn/6.2.1/img/champion/" + game.red_team.bans[1].champion.image.link
			except IndexError:
				b2 = "/static/img/Gabe.png"
			try:
				b3 = "http://ddragon.leagueoflegends.com/cdn/6.2.1/img/champion/" + game.red_team.bans[2].champion.image.link
			except IndexError:
				b3 = "/static/img/Gabe.png"

			p1 = "http://ddragon.leagueoflegends.com/cdn/6.2.1/img/champion/" + game.blue_team.participants[0].champion.image.link
			p2 = "http://ddragon.leagueoflegends.com/cdn/6.2.1/img/champion/" + game.blue_team.participants[1].champion.image.link
			p3 = "http://ddragon.leagueoflegends.com/cdn/6.2.1/img/champion/" + game.blue_team.participants[2].champion.image.link
			p4 = "http://ddragon.leagueoflegends.com/cdn/6.2.1/img/champion/" + game.blue_team.participants[3].champion.image.link
			p5 = "http://ddragon.leagueoflegends.com/cdn/6.2.1/img/champion/" + game.blue_team.participants[4].champion.image.link
		else:
			try:
				b1 = "http://ddragon.leagueoflegends.com/cdn/6.2.1/img/champion/" + game.blue_team.bans[0].champion.image.link
			except IndexError:
				b1 = "/static/img/Gabe.png"
			try:
				b2 = "http://ddragon.leagueoflegends.com/cdn/6.2.1/img/champion/" + game.blue_team.bans[1].champion.image.link
			except IndexError:
				b2 = "/static/img/Gabe.png"
			try:
				b3 = "http://ddragon.leagueoflegends.com/cdn/6.2.1/img/champion/" + game.blue_team.bans[2].champion.image.link
			except IndexError:
				b3 = "/static/img/Gabe.png"
			p1 = "http://ddragon.leagueoflegends.com/cdn/6.2.1/img/champion/" + game.red_team.participants[0].champion.image.link
			p2 = "http://ddragon.leagueoflegends.com/cdn/6.2.1/img/champion/" + game.red_team.participants[1].champion.image.link
			p3 = "http://ddragon.leagueoflegends.com/cdn/6.2.1/img/champion/" + game.red_team.participants[2].champion.image.link
			p4 = "http://ddragon.leagueoflegends.com/cdn/6.2.1/img/champion/" + game.red_team.participants[3].champion.image.link
			p5 = "http://ddragon.leagueoflegends.com/cdn/6.2.1/img/champion/" + game.red_team.participants[4].champion.image.link
		print("lag end")
		teaminfo ={"t1": team1, "t2":team2, "won": win, "game": g, "ban1" : b1, "ban2": b2, "ban3": b3, "player1": p1, "player2": p2, "player3": p3, "player4": p4, "player5": p5, "gameobj": game }
		#print(teaminfo)

		gameslist.append(teaminfo)
	print(t.teamName)
	return HttpResponse(render(request, 'teamStats.html', {'p' :players, 's': stats, 't': t, 'gs': gameslist} ))


def match(request, match_num):
	try:
		m = Game.objects.get(Number=match_num)
		print(m.filename)
	except ObjectDoesNotExist:
		return HttpResponse("There is no match with this ID")
	with open(str(m.filename), 'rb') as infile:
		game = pickle.load(infile)

	game_players = []
	order = [11 for i in range(10)]
	duo = 3

	for i in range(len(game.participants)):

		if i == 5:
			duo = 3

		player = game.participants[i]
		role = player.timeline.role.name
		lane = player.timeline.data.lane.lower()
		index = 0

		if role == 'none': #JUNGLER {1,6}
			index = 1

		if role == 'solo':
			if lane == 'top': #TOP {0,5}
				index = 0
			elif lane == 'middle': #MIDDLE{2,7}
				index = 2
				print(player)
			else:
				index = 0

		if role == 'carry':
			index = 3

		if role == 'support':
			index = 4

		if role == 'duo':
			index = duo
			duo = duo + 1

		if player.side.name == 'red':
			index = index + 5
		#this is in case of duplicates or strange exceptions
		for indices in order:
			if indices == index:
				if index < 5:
					indexlist = []
					for indicesj in order:
						if indicesj < 5:
							indexlist.append(indicesj)
					fullteam = [0,1,2,3,4]
					openspots = list(set(fullteam)-set(indexlist))
					index=openspots[-1]
				else:
					indexlist = []
					for indicesj in order:
						if indicesj >= 5:
							indexlist.append(indicesj)
					fullteam = [5,6,7,8,9]
					openspots = list(set(fullteam)-set(indexlist))
					index=openspots[-1]

		order[i] = index

	#name = str(m)
	riotapi.set_region("NA")
	riotapi.set_api_key("APIKEY")

	class MatchPlayer:

		def __init__(self, player, data, champ):
			self.player = player
			self.data = data
			self.champ = champ

	players = []

	try:
		temp_Player = Player.objects.get(SummonerNumber=m.team1Player1)
	except ObjectDoesNotExist:
		temp_Player = Player()
		temp_Player.PlayerIGN = riotapi.get_summoner_by_id(m.team1Player1)
	temp_Participant = game.participants[0]
	temp_Champ =  "http://ddragon.leagueoflegends.com/cdn/6.2.1/img/champion/" + game.participants[0].champion.image.link
	temp_MatchPlayer = MatchPlayer(temp_Player, temp_Participant, temp_Champ)
	players.append(temp_MatchPlayer)

	try:
		temp_Player = Player.objects.get(SummonerNumber=m.team1Player2)
	except ObjectDoesNotExist:
		temp_Player = Player()
		temp_Player.PlayerIGN = riotapi.get_summoner_by_id(m.team1Player2)
	temp_Participant = game.participants[1]
	temp_Champ =  "http://ddragon.leagueoflegends.com/cdn/6.2.1/img/champion/" + game.participants[1].champion.image.link
	temp_MatchPlayer = MatchPlayer(temp_Player, temp_Participant, temp_Champ)
	players.append(temp_MatchPlayer)

	try:
		temp_Player = Player.objects.get(SummonerNumber=m.team1Player3)
	except ObjectDoesNotExist:
		temp_Player = Player()
		temp_Player.PlayerIGN = riotapi.get_summoner_by_id(m.team1Player3)
	temp_Participant = game.participants[2]
	temp_Champ =  "http://ddragon.leagueoflegends.com/cdn/6.2.1/img/champion/" + game.participants[2].champion.image.link
	temp_MatchPlayer = MatchPlayer(temp_Player, temp_Participant, temp_Champ)
	players.append(temp_MatchPlayer)

	try:
		temp_Player = Player.objects.get(SummonerNumber=m.team1Player4)
	except ObjectDoesNotExist:
		temp_Player = Player()
		temp_Player.PlayerIGN = riotapi.get_summoner_by_id(m.team1Player4)
	temp_Participant = game.participants[3]
	temp_Champ =  "http://ddragon.leagueoflegends.com/cdn/6.2.1/img/champion/" + game.participants[3].champion.image.link
	temp_MatchPlayer = MatchPlayer(temp_Player, temp_Participant, temp_Champ)
	players.append(temp_MatchPlayer)

	try:
		temp_Player = Player.objects.get(SummonerNumber=m.team1Player5)
	except ObjectDoesNotExist:
		temp_Player = Player()
		temp_Player.PlayerIGN = riotapi.get_summoner_by_id(m.team1Player5)
	temp_Participant = game.participants[4]
	temp_Champ =  "http://ddragon.leagueoflegends.com/cdn/6.2.1/img/champion/" + game.participants[4].champion.image.link
	temp_MatchPlayer = MatchPlayer(temp_Player, temp_Participant, temp_Champ)
	players.append(temp_MatchPlayer)

	try:
		temp_Player = Player.objects.get(SummonerNumber=m.team2Player1)
	except ObjectDoesNotExist:
		temp_Player = Player()
		temp_Player.PlayerIGN = riotapi.get_summoner_by_id(m.team2Player1)
	temp_Participant = game.participants[5]
	temp_Champ =  "http://ddragon.leagueoflegends.com/cdn/6.2.1/img/champion/" + game.participants[5].champion.image.link
	temp_MatchPlayer = MatchPlayer(temp_Player, temp_Participant, temp_Champ)
	players.append(temp_MatchPlayer)

	try:
		temp_Player = Player.objects.get(SummonerNumber=m.team2Player2)
	except ObjectDoesNotExist:
		temp_Player = Player()
		temp_Player.PlayerIGN = riotapi.get_summoner_by_id(m.team2Player2)
	temp_Participant = game.participants[6]
	temp_Champ =  "http://ddragon.leagueoflegends.com/cdn/6.2.1/img/champion/" + game.participants[6].champion.image.link
	temp_MatchPlayer = MatchPlayer(temp_Player, temp_Participant, temp_Champ)
	players.append(temp_MatchPlayer)

	try:
		temp_Player = Player.objects.get(SummonerNumber=m.team2Player3)
	except ObjectDoesNotExist:
		temp_Player = Player()
		temp_Player.PlayerIGN = riotapi.get_summoner_by_id(m.team2Player3)
	temp_Participant = game.participants[7]
	temp_Champ =  "http://ddragon.leagueoflegends.com/cdn/6.2.1/img/champion/" + game.participants[7].champion.image.link
	temp_MatchPlayer = MatchPlayer(temp_Player, temp_Participant, temp_Champ)
	players.append(temp_MatchPlayer)

	try:
		temp_Player = Player.objects.get(SummonerNumber=m.team2Player4)
	except ObjectDoesNotExist:
		temp_Player = Player()
		temp_Player.PlayerIGN = riotapi.get_summoner_by_id(m.team2Player4)
	temp_Participant = game.participants[8]
	temp_Champ =  "http://ddragon.leagueoflegends.com/cdn/6.2.1/img/champion/" + game.participants[8].champion.image.link
	temp_MatchPlayer = MatchPlayer(temp_Player, temp_Participant, temp_Champ)
	players.append(temp_MatchPlayer)

	try:
		temp_Player = Player.objects.get(SummonerNumber=m.team2Player5)
	except ObjectDoesNotExist:
		temp_Player = Player()
		temp_Player.PlayerIGN = riotapi.get_summoner_by_id(m.team2Player5)
	temp_Participant = game.participants[9]
	temp_Champ =  "http://ddragon.leagueoflegends.com/cdn/6.2.1/img/champion/" + game.participants[9].champion.image.link
	temp_MatchPlayer = MatchPlayer(temp_Player, temp_Participant, temp_Champ)
	players.append(temp_MatchPlayer)

	ordered_players = [0 for i in range(10)]

	for num in range(len(players)):
		ordered_players[order[num]] = players[num]

	return HttpResponse(render(request, 'Match.html', {'matchinfo' :m, 'game' : game, 'players': ordered_players}))



def standings(request):
	teamsbyleague= {}
	teamsbyleague['Demacia'] = Team.objects.filter(league=0).order_by('-points')
	teamsbyleague['Noxus'] = Team.objects.filter(league=1).order_by('-points')
	teamsbyleague['Piltover'] = Team.objects.filter(league=2).order_by('-points')
	teamsbyleague['Ionia'] = Team.objects.filter(league=3).order_by('-points')
	return HttpResponse(render(request, 'standings.html', {'leagues': teamsbyleague} ))

def schedule(request):
	#return HttpResponse("Tournament code testing right now")
	schedule = []
	weeks = []
	weeks = Week.objects.all().order_by('startdate')
	i = 0
	for w in weeks:
		wk = {}
		wkl0= []
		wkl0.append({'team1': Team.objects.get(teamID=w.L0game1t1), 'team2': Team.objects.get(teamID=w.L0game1t2), 'time' : w.L0game1Time, 'canedit' : False, 'date' :w.L0game1date, 'game1code':  TourneyCode.objects.filter(week=i).filter(league=0).filter(game=1).get(rift=0)  , 'game2code': TourneyCode.objects.filter(week=i).filter(league=0).filter(game=1).get(rift=1)})
		wkl0.append({'team1': Team.objects.get(teamID=w.L0game2t1), 'team2': Team.objects.get(teamID=w.L0game2t2), 'time' : w.L0game2Time, 'canedit' : False, 'date' :w.L0game2date, 'game1code':  TourneyCode.objects.filter(week=i).filter(league=0).filter(game=2).get(rift=0)  , 'game2code': TourneyCode.objects.filter(week=i).filter(league=0).filter(game=2).get(rift=1)})
		wkl0.append({'team1': Team.objects.get(teamID=w.L0game3t1), 'team2': Team.objects.get(teamID=w.L0game3t2), 'time' : w.L0game3Time, 'canedit' : False, 'date' :w.L0game3date, 'game1code':  TourneyCode.objects.filter(week=i).filter(league=0).filter(game=3).get(rift=0)  , 'game2code': TourneyCode.objects.filter(week=i).filter(league=0).filter(game=3).get(rift=1)})
		wk['Demacia'] = wkl0
		wkl1= []
		wkl1.append({'team1': Team.objects.get(teamID=w.L1game1t1), 'team2': Team.objects.get(teamID=w.L1game1t2), 'time' : w.L1game1Time, 'canedit' : False, 'date' :w.L1game1date, 'game1code':  TourneyCode.objects.filter(week=i).filter(league=1).filter(game=1).get(rift=0)  , 'game2code': TourneyCode.objects.filter(week=i).filter(league=1).filter(game=1).get(rift=1)})
		wkl1.append({'team1': Team.objects.get(teamID=w.L1game2t1), 'team2': Team.objects.get(teamID=w.L1game2t2), 'time' : w.L1game2Time, 'canedit' : False, 'date' :w.L1game2date, 'game1code':  TourneyCode.objects.filter(week=i).filter(league=1).filter(game=2).get(rift=0)  , 'game2code': TourneyCode.objects.filter(week=i).filter(league=1).filter(game=2).get(rift=1)})
		wkl1.append({'team1': Team.objects.get(teamID=w.L1game3t1), 'team2': Team.objects.get(teamID=w.L1game3t2), 'time' : w.L1game3Time, 'canedit' : False, 'date' :w.L1game3date, 'game1code':  TourneyCode.objects.filter(week=i).filter(league=1).filter(game=3).get(rift=0)  , 'game2code': TourneyCode.objects.filter(week=i).filter(league=1).filter(game=3).get(rift=1)})
		wk['Noxus'] = wkl1
		wkl2= []
		wkl2.append({'team1': Team.objects.get(teamID=w.L2game1t1), 'team2': Team.objects.get(teamID=w.L2game1t2), 'time' : w.L2game1Time, 'canedit' : False, 'date' :w.L2game1date, 'game1code':  TourneyCode.objects.filter(week=i).filter(league=2).filter(game=1).get(rift=0)  , 'game2code': TourneyCode.objects.filter(week=i).filter(league=2).filter(game=1).get(rift=1)})
		wkl2.append({'team1': Team.objects.get(teamID=w.L2game2t1), 'team2': Team.objects.get(teamID=w.L2game2t2), 'time' : w.L2game2Time, 'canedit' : False, 'date' :w.L2game2date, 'game1code':  TourneyCode.objects.filter(week=i).filter(league=2).filter(game=2).get(rift=0)  , 'game2code': TourneyCode.objects.filter(week=i).filter(league=2).filter(game=2).get(rift=1)})
		wkl2.append({'team1': Team.objects.get(teamID=w.L2game3t1), 'team2': Team.objects.get(teamID=w.L2game3t2), 'time' : w.L2game3Time, 'canedit' : False, 'date' :w.L2game3date, 'game1code':  TourneyCode.objects.filter(week=i).filter(league=2).filter(game=3).get(rift=0)  , 'game2code': TourneyCode.objects.filter(week=i).filter(league=2).filter(game=3).get(rift=1)})
		wk['Piltover'] =wkl2
		wkl3= []
		wkl3.append({'team1': Team.objects.get(teamID=w.L3game1t1), 'team2': Team.objects.get(teamID=w.L3game1t2), 'time' : w.L3game1Time, 'canedit' : False, 'date' :w.L3game1date, 'game1code':  TourneyCode.objects.filter(week=i).filter(league=3).filter(game=1).get(rift=0)  , 'game2code': TourneyCode.objects.filter(week=i).filter(league=3).filter(game=1).get(rift=1)})
		wkl3.append({'team1': Team.objects.get(teamID=w.L3game2t1), 'team2': Team.objects.get(teamID=w.L3game2t2), 'time' : w.L3game2Time, 'canedit' : False, 'date' :w.L3game2date, 'game1code':  TourneyCode.objects.filter(week=i).filter(league=3).filter(game=2).get(rift=0)  , 'game2code': TourneyCode.objects.filter(week=i).filter(league=3).filter(game=2).get(rift=1)})
		wkl3.append({'team1': Team.objects.get(teamID=w.L3game3t1), 'team2': Team.objects.get(teamID=w.L3game3t2), 'time' : w.L3game3Time, 'canedit' : False, 'date' :w.L3game3date, 'game1code':  TourneyCode.objects.filter(week=i).filter(league=3).filter(game=3).get(rift=0)  , 'game2code': TourneyCode.objects.filter(week=i).filter(league=3).filter(game=3).get(rift=1)})
		wk['Ionia'] = wkl3

		#Captain namechanges will not work correctly currently
		try:
			if request.user.is_authenticated():
				cap = Player.objects.get(username = request.user.username)
				team2edit = Team.objects.get(CaptainID = cap.SummonerNumber)
				if team2edit.league == 0:
					l = 'Demacia'
				if team2edit.league == 1:
					l = 'Noxus'
				if team2edit.league == 2:
					l = 'Piltover'
				if team2edit.league == 3:
					l = 'Ionia'
				for game in wk[l]:
					#print(game)
					if game['team1'] == team2edit:
						game['canedit'] = True
					if game['team2'] == team2edit:
						game['canedit'] = True
		except ObjectDoesNotExist:
			print("not a captain")
		schedule.append({'startdate': w.startdate, 'week': wk})
		#print(wk['Demacia'][0])
		#print(schedule)
		#print(schedule[0])
		#print(schedule[0][w.startdate]['Demacia'])
		#print(str(w.L0game2date.ctime()))
		i = i+1
	games = Game.objects.all()
	for g in games:
		for week in schedule:
			l = Team.objects.get(teamID=g.team1).league
			if l == 0:
				w = 'Demacia'
			if l == 1:
				w = 'Noxus'
			if l == 2:
				w = 'Piltover'
			if l == 3:
				w = 'Ionia'
			for gm in week['week'][w]:
				if gm['team1'].teamID == g.team1:
					if gm['team2'].teamID == g.team2:
						gm['game1'] = g
						gm['game1w'] = Team.objects.get(teamID=g.winner).teamName
				if gm['team2'].teamID == g.team1:
					if gm['team1'].teamID == g.team2:
						gm['game2'] = g
						gm['game2w'] = Team.objects.get(teamID=g.winner).teamName

	return HttpResponse(render(request, 'schedule.html', {'schedule': schedule} ))

def rules(request):
	return HttpResponse(render(request, 'rules.html'))
def riot(request):
	return HttpResponse('55702c23-9561-43b3-9d46-ef37b1f2c9fc')

#def streamsetup(request):


def playoffs(request):
	class Series ():

		def __init__(self, series, teamcap):
			try:
				self.team1 = Team.objects.get(teamID=series.team1).teamName
				self.t1id = Team.objects.get(teamID=series.team1).teamID
			except ObjectDoesNotExist:
				self.team1 = None
			try:
				self.team2 = Team.objects.get(teamID=series.team2).teamName
				self.t2id = Team.objects.get(teamID=series.team2).teamID
			except ObjectDoesNotExist:
				self.team2 = None
			self.id = series.identifier
			self.record = str(series.team1wins) + " - " + str(series.team2wins)
			self.match1 = series.match1
			self.match2 = series.match2
			self.match3 = series.match3
			self.match4 = series.match4
			self.match5 = series.match5
			self.code1 = series.code1
			self.code2 = series.code2
			self.code3 = series.code3
			self.code4 = series.code4
			self.code5 = series.code5
			self.canedit = False
			self.roundof = series.roundof
			if self.team1 == teamcap.teamName :
				self.canedit = True
			if self.team2 == teamcap.teamName :
				self.canedit = True
			self.time = series.time
			self.date = series.date



	series = []
	seriestemp = PlayoffGames.objects.all()
	for s in seriestemp:
		if request.user.is_authenticated():
			cap = Player.objects.get(username = request.user.username)
			team2edit = Team.objects.get(CaptainID = cap.SummonerNumber)
			seriesobj = Series(s, team2edit)
			print (team2edit)
		else:
			seriesobj = Series(s,  Team())
		print(seriesobj.date.ctime())
		series.append(seriesobj)
	return HttpResponse(render(request, 'playoffs.html', {'playoffseries': series} ))

'''def denullplayoffs(request):
	games = PlayoffGames.objects.all()
	for g in games:
		if g.team1 == 0:
			g.team1 = 25
		if g.team2 == 0:
			g.team2 = 25
		g.save()'''

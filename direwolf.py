import sys; sys.path.insert(0, '../clean/src/fireplace')
from hearthstone.enums import CardClass, CardType
import numpy as np
import fireplace.cards
import fireplace
import time
import random
import sys
import os

dire_wolf_alpha_id = 'EX1_162'
penguin_id = 'ICC_023'
river_croc_id = 'CS2_120'
magma_id = 'CS2_118'
yeti_id = 'CS2_182'
frostbolt_id='CS2_024'

cards = [penguin_id, river_croc_id, magma_id, yeti_id, frostbolt_id]
cards = [penguin_id for _ in range(3)]
og_deck = [penguin_id, river_croc_id, magma_id, yeti_id]

def setup_game():
	from fireplace.game import Game
	from fireplace.player import Player
	fireplace.cards.filter(name="Garrosh")

	deck = og_deck

	player1 = Player("Player1", deck, CardClass.WARRIOR.default_hero)
	player2 = Player("Player2", deck, CardClass.WARRIOR.default_hero)

	game = Game(players=(player1,player2))
	game.start()

	for player in game.players:
		mull_count = 0
		cards_to_mulligan = []
		player.choice.choose(*cards_to_mulligan)

	return game

def getPlayerRow(player):
	health = player.characters[0].health
	mana = player.mana
	turnTracker = player.current_player
	maxMana = player.max_mana
	handTracker = [card for card in og_deck]
	deckTracker = [card for card in og_deck]

	minions = []

	for character in player.characters[1:]:
		minions += [character.atk, character.health, int(character.can_attack())]
	for _ in range(7 - (len(player.characters)-1)):
		minions += [0,0,0]
	
	for card in og_deck:
		handTracker[handTracker.index(card)] = int( card in [i.id for i in player.hand] )
		deckTracker[deckTracker.index(card)] = int( card in [i.id for i in player.deck] )
	
	return [minions, health, mana, int(turnTracker), maxMana, handTracker, deckTracker]

if __name__ == '__main__':
	from fireplace.player import Player
	from fireplace.game import Game
	import copy 
	game = setup_game()
	gc = copy.deepcopy(game)
	player = game.players[0]
	
	for card in player.hand:
		if card.is_playable():
			card.play()
			break
		

	print("\n\n\n")
	print(getPlayerRow(player))
	print(getPlayerRow(gc.players[0]))
	#print(getPlayerRow(player))
	#print(game.entities)


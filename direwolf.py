import sys; sys.path.insert(0, './fireplace')
from hearthstone.enums import CardClass, CardType
from fireplace.card import Card
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
og_deck_names = ["snowflipper penguin", "river crocolisk", "magma rager", "chillwind yeti"]

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
	
	game.end_turn()
	game.end_turn()
		
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
	
	return minions + [health, mana, int(turnTracker), maxMana] + handTracker + deckTracker

	
def injectBoard(board):
	game = setup_game()
	
	for idx in [0,1]:		
		player = game.players[idx]
		row = board[idx]
		
		mis = [i for i in range(28)]
		hi = 29
		mi = 30
		tti = 31
		mma = 32
		hti = [i for i in range(32, 36, 1)]
		dti = [i for i in range(36, 40, 1)]
		
		if tti == 1: 
			game.current_player = player
		
		player.hand = []
		player.deck = []
		player.health = row[hi]
		player.max_mana = int(row[mma])
		player.used_mana = int(row[mma] - row[mi])
		
		for i in range(0,len(hti),3):
			if mis[i] > 0:
				card = player.card(og_deck[0])
				player.field.append(card)
				player.hand.append(card)
				
		for i in range(0,len(dti),3):
			if mis[i] > 0:
				card = player.card(og_deck[0])
				player.field.append(card)
				player.hand.append(card)
				
	return game
	
	
	
	

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
			
	row = getPlayerRow(player)
	
	board = np.zeros((2,len(row)))
	board[0] = row
	board[1] = row
	board[0][30] = 3
	board[0][32] = 5


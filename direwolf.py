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
	
		game.begin_turn(player)
		player.fatigue_counter = 0
		
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


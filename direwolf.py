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

og_deck = [penguin_id, river_croc_id, magma_id, yeti_id, dire_wolf_alpha_id, 'EX1_015']
og_deck_names = ["Snowflipper Penguin", "River Crocolisk", "Magma Rager", "Chillwind Yeti", "Dire Wolf Alpha", 'Novice Engineer']

og_deck += ['EX1_085', 'CS2_122', 'CS2_222','EX1_593','CS2_119','GVG_044','DS1_055','CS2_200','CS2_124']
og_deck_names += ['Mind Control Tech', "Raid Leader", "Stormwind Champion", "Nightblade", "Oasis Snapjaw", "Spider Tank", "Darkscale Healer", "Boulderfist Ogre", "Wolfrider"]

og_deck +=['CS2_032','CS2_024','CS2_092', 'CS2_108']
og_deck_names += ["Flamestrike", "Frostbolt", "Blessing of Kings", "Execute"]


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
		
	return game
	

if __name__ == '__main__':
	from fireplace.player import Player
	from fireplace.game import Game
	
	for c in og_deck_names:
		print(c, fireplace.cards.filter(name=c))

	print("\n\n")
	
	for c in og_deck_names:
		print('1 x {}'.format(c))

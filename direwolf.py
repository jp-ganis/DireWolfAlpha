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
og_deck = [penguin_id, river_croc_id, magma_id, yeti_id, dire_wolf_alpha_id, 'EX1_015','CS2_122','EX1_162','EX1_085','CS2_122','CS2_222','CS2_124','EX1_593','CS2_119','GVG_044','DS1_055','CS2_200']
og_deck_names = ["snowflipper penguin", "dire wolf alpha", "river crocolisk", "magma rager", "chillwind yeti"]

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
	
	print(fireplace.cards.filter(name="Novice Engineer"))
	print(fireplace.cards.filter(name="Raid Leader"))
	print(fireplace.cards.filter(name="Dire Wolf Alpha"))
	print(fireplace.cards.filter(name="Mind Control Tech"))

	print(fireplace.cards.filter(name="Raid Leader"))
	print(fireplace.cards.filter(name="Stormwind Champion"))
	print(fireplace.cards.filter(name="Wolfrider"))
	print(fireplace.cards.filter(name="Nightblade"))

	print(fireplace.cards.filter(name="Oasis Snapjaw"))
	print(fireplace.cards.filter(name="Spider Tank"))
	print(fireplace.cards.filter(name="Darkscale Healer"))
	print(fireplace.cards.filter(name="Boulderfist Ogre"))

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
import copy
import logging; logging.getLogger("fireplace").setLevel(logging.WARNING)

dire_wolf_alpha_id = 'EX1_162'
penguin_id = 'ICC_023'
river_croc_id = 'CS2_120'
magma_id = 'CS2_118'
yeti_id = 'CS2_182'
frostbolt_id='CS2_024'

og_deck = [penguin_id, river_croc_id, magma_id, yeti_id, dire_wolf_alpha_id, 'EX1_015']
og_deck_names = ["Snowflipper Penguin", "River Crocolisk", "Magma Rager", "Chillwind Yeti", "Dire Wolf Alpha", 'Novice Engineer']

og_deck += ['EX1_085', 'CS2_122', 'CS2_222','EX1_593','CS2_119','GVG_044','DS1_055','CS2_200']#,'CS2_124']
og_deck_names += ['Mind Control Tech', "Raid Leader", "Stormwind Champion", "Nightblade", "Oasis Snapjaw", "Spider Tank", "Darkscale Healer", "Boulderfist Ogre"]#, "Wolfrider"]

og_deck +=['CS2_032','CS2_024','CS2_092', 'CS2_108', 'UNG_087']
og_deck_names += ["Flamestrike", "Frostbolt", "Blessing of Kings", "Execute", "Bittertide Hydra"]

og_deck +=['NEW1_020', 'OG_314', 'NEW1_036', 'EX1_400']
og_deck_names += ["Wild Pyromancer", "Blood To Ichor", "Commanding Shout", "Whirlwind"]


def setup_game():
	from fireplace.game import Game
	from fireplace.player import Player
	fireplace.cards.filter(name="Garrosh")

	player1 = Player("Player1", og_deck, CardClass.HUNTER.default_hero)
	player2 = Player("Player2", og_deck, CardClass.MAGE.default_hero)
	
	game = Game(players=(player1,player2))
	game.start()

	for player in game.players:
		mull_count = 0
		cards_to_mulligan = []
		player.choice.choose(*cards_to_mulligan)
	
		game.begin_turn(player)
		
	return game
	

def enumerate_actions(game):
	actions = set() ## set of (function, arg) tuples
	player = game.current_player
	
	heropower = player.hero.power
	if heropower.is_usable():
		if heropower.requires_target():
			for t in heropower.targets:
				actions.add((heropower.use, t))
		else:
			actions.add((heropower.use, None))

	for card in player.hand:
		if card.is_playable():
			if card.requires_target():
				for t in card.targets:
					actions.add((card.play, t))
			else:
				actions.add((card.play, None))

	for character in player.characters:
		if character.can_attack():
			for t in character.targets:
				actions.add((character.attack, t))
				
	return actions

if __name__ == '__main__':
	from fireplace.player import Player
	from fireplace.game import Game
	
	for c in og_deck_names:
		print(c, fireplace.cards.filter(name=c))

	print("\n\n")
	
	for c in og_deck_names:
		print('1 x {}'.format(c))
		
	print("\n\n")	

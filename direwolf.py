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

og_deck = []
og_deck_names =[]

og_deck_names += ["Spider Tank"]
og_deck_names += ["Magma Rager"]
og_deck_names += ["Chillwind Yeti"]
og_deck_names += ["Oasis Snapjaw"]
og_deck_names += ["Wild Pyromancer"]
og_deck_names += ["Frostbolt"]
og_deck_names += ["Flamestrike"]
# og_deck_names += ["Brawl"] ## rng effect!
og_deck_names += ["Nightblade"]
og_deck_names += ["Boulderfist Ogre"]
og_deck_names += ["Fireball"]
og_deck_names += ["Bittertide Hydra"]
og_deck_names += ["Doomsayer"]
og_deck_names += ["Execute"]
og_deck_names += ["Darkscale Healer"]
og_deck_names += ["Whirlwind"]
og_deck_names += ["Mind Control Tech"]
og_deck_names += ["Defile"]
og_deck_names += ["Blessing of Kings"]
og_deck_names += ["River Crocolisk"]
og_deck_names += ["Snowflipper Penguin"]

# random.shuffle(og_deck_names)

og_deck = [fireplace.cards.filter(name=n)[0] for n in og_deck_names]

def setup_game():
	from fireplace.game import Game
	from fireplace.player import Player
	fireplace.cards.filter(name="Garrosh")

	player1 = Player("Player1", og_deck, CardClass.MAGE.default_hero)
	player2 = Player("Player2", og_deck, CardClass.WARLOCK.default_hero)
	
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

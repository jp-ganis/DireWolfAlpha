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

	
def get_odd_warrior_deck():
	n = []
	n += 2*["Shield Slam"]
	n += 2*["Town Crier"]
	n += 2*["Whirlwind"]
	n += 1*["Gluttonous Ooze"]
	n += 2*["Ironbeak Owl"]
	n += 2*["Rabid Worgen"]
	n += 2*["Reckless Flurry"]
	n += 2*["Shield Block"]
	n += 1*["Fiery War Axe"] ## replace this
	n += 1*["Big Game Hunter"]
	n += 2*["Brawl"]
	n += 1*["Darius Crowley"]
	n += 2*["Direhorn Hatchling"]
	n += 1*["Faceless Manipulator"]
	n += 1*["Harrison Jones"]
	n += 1*["Baron Geddon"]
	n += 1*["Gorehowl"]
	n += 1*["Baku the Mooneater"]
	n += 1*["King Mosh"]
	
	return list(set([(c, fireplace.cards.filter(name=c)[0]) for c in n if len(fireplace.cards.filter(name=c)) > 0]))

og_deck = []
og_deck_names =[]

og_deck_names += ["Brawl"] ## rng effect!
og_deck_names += ["Spider Tank"]
og_deck_names += ["Magma Rager"]
og_deck_names += ["Chillwind Yeti"]
og_deck_names += ["Oasis Snapjaw"]
og_deck_names += ["Wild Pyromancer"]
og_deck_names += ["Frostbolt"]
og_deck_names += ["Flamestrike"]
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
# og_deck = [c[1] for c in get_odd_warrior_deck()]
# og_deck_names = [c[0] for c in get_odd_warrior_deck()]

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

def setup_game():
	from fireplace.game import Game
	from fireplace.player import Player
	fireplace.cards.filter(name="Garrosh")

	player1 = Player("Player1", og_deck, CardClass.WARRIOR.default_hero)
	player2 = Player("Player2", og_deck, CardClass.WARLOCK.default_hero)
	
	game = Game(players=(player1,player2))
	game.start()

	for player in game.players:
		mull_count = 0
		cards_to_mulligan = []
		player.choice.choose(*cards_to_mulligan)
	
		game.begin_turn(player)
		
	return game
	
def get_murloc_paladin_deck():
	pass

if __name__ == '__main__':
	from fireplace.player import Player
	from fireplace.game import Game
	from fireplace.card import Card
	
	print("\n\n")
	
	for c in sorted(get_odd_warrior_deck()):
		print('1 x {}'.format(c))
		card = Card(c[1])
		
	print("\n\n")	

	

	game = setup_game()
	for i in range(7):
		game.end_turn()
	
	game.player1.give('GIL_547').play()
	game.end_turn()
	
	for card in game.player2.hand:
		if card.is_playable() and not card.requires_target():
			card.play()
	
	game.end_turn()
	
	print(game.board)
	game.player1.field[0].attack(game.player2.field[0])
	
	print(game.board[0], game.board[0].atk, game.board[0].health)
	
	print(game.board)
	

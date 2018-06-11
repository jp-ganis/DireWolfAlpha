from ..utils import *

class GIL_580:
	"""Town Crier"""
	play = Find(FRIENDLY_DECK + RUSH) & ForceDraw(RANDOM(FRIENDLY_DECK + RUSH))
	
class GIL_547:
	"""Darius Crowley"""
	events = Attack(SELF, MINION + MORTALLY_WOUNDED).after(Buff(SELF, "GIL_547e"))
	
GIL_547e = buff(+2, +2)

class UNG_957:
	"""Direhorn Hatchling"""
	deathrattle = Shuffle(CONTROLLER, "UNG_957t1")
	
class LOOT_364:
	"""Reckless Flurry"""
	play = Hit(ALL_MINIONS, ARMOR(FRIENDLY_HERO)), Hit(FRIENDLY_HERO, ARMOR(FRIENDLY_HERO))
	
class UNG_933:
	"""King Mosh"""
	play = Destroy(ALL_MINIONS + DAMAGED)
	
class UNG_946:
	"""Gluttonous Ooze"""
	play = GainArmor(FRIENDLY_HERO, ATK(ENEMY_WEAPON)), Destroy(ENEMY_WEAPON)
	

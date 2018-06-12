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
	
class UNG_073:
	"""Rockpool Hunter"""
	powered_up = Find(FRIENDLY_MINIONS + MURLOC)
	play = Buff(TARGET, "UNG_073e")
UNG_073e = buff(+1, +1)

class UNG_960:
	"""Lost in the Jungle"""
	play = Summon(CONTROLLER, "CS2_101t") * 2
	
class UNG_015:
	"""Sunkeeper Tarim"""
	play = Buff(ALL_MINIONS - SELF, "UNG_015e")

class UNG_015e:
	atk = SET(3)
	max_health = SET(3)
	
class UNG_950:
	"""Vinecleaver"""
	events = Attack(FRIENDLY_HERO).after(Summon(CONTROLLER, "CS2_101t") * 2)
	
class LOOT_167:
	"""Fungalmancer"""
	play = Buff(SELF_ADJACENT, "LOOT_167e")
LOOT_167e = buff(+2, +2)
	
class GIL_667:
	"""Rotten Applebaum"""
	deathrattle = Heal(FRIENDLY_HERO, 5)
	
class LOOT_093:
	"""Call to Arms"""
	play = Find(FRIENDLY_DECK + MINION + (COST <= 2)) & (Summon(CONTROLLER, RANDOM(FRIENDLY_DECK + MINION + (COST <= 2))) * 3)
	
import sys; sys.path.insert(0, '../fireplace'); sys.path.insert(0, './fireplace')
from fireplace.exceptions import GameOver
from hearthstone.enums import Zone
import hs.direwolf as direwolf
import fireplace.cards
import numpy as np
import pytest
import copy 
import py

import logging; logging.getLogger("fireplace").setLevel(logging.WARNING)
	
def pr(player):
	return 0 if player == 1 else 1
def test_pr():
	assert(pr(1) == 0)
	assert(pr(-1) == 1)

class HearthstoneGame():
	def __init__(self):
		self.startingHealth = 20
		self.maxMinions = 7
		self.minionSize = 4
		self.deckSize = len(direwolf.og_deck)

		self.minionSize = 4
		
		self.playerTurnTrackerIndex = -4
		self.playerHealthIndex = -3
		self.playerManaIndex = -2
		self.playerCardsInHandIndex = -1
		
		self.deckTrackerStartingIndex = -5
		self.deckTrackerIndices = [i for i in range(self.deckTrackerStartingIndex, self.deckTrackerStartingIndex-self.deckSize, -1)]
		
		self.handTrackerStartingIndex = self.deckTrackerIndices[-1] - 1
		self.handTrackerIndices = [i for i in range(self.handTrackerStartingIndex, self.handTrackerStartingIndex-self.deckSize, -1)]
		
		self.playerMaxManaIndex = self.handTrackerIndices[-1] - 1

		self.playerSize = sum([1 for _ in [self.playerHealthIndex, self.playerManaIndex, self.playerMaxManaIndex, self.playerTurnTrackerIndex]]) + len(self.deckTrackerIndices) + len(self.handTrackerIndices)
		
		self.minionAttackIndex = 0
		self.minionHealthIndex = 1
		self.minionCanAttackIndex = 2
		self.minionIdIndex = 3
		
		self.enemyTargets = 9
		self.totalTargets = 16

		self.maxMinionTargetIndex = self.enemyTargets * self.maxMinions
		self.maxCardTargetIndex = self.maxMinionTargetIndex + 10 * self.totalTargets
		
		self.passTarget = self.enemyTargets - 1
		self.faceTarget = self.passTarget - 1
		
	def getInitBoard(self):
		"""
		Returns:
			startBoard: a representation of the board (ideally this is the form
						that will be the input to your neural network)
		"""
		board = np.zeros(self.getBoardSize())

		for i in [0,1]:
				row = board[i]
				row[self.playerHealthIndex] = self.startingHealth
				row[self.playerManaIndex] = 1
				row[self.playerMaxManaIndex] = 1
				row[self.playerCardsInHandIndex] = 0
				for j in self.deckTrackerIndices: row[j] = 1
		board[0][self.playerTurnTrackerIndex] = 1

		return board

	def getBoardSize(self):
		"""
		Returns:
			(x,y): a tuple of board dimensions
		"""
		## player array size = 7 * minionSize + hp + mana + #cards_in_hand + deck_tracker
		self.boardRowSize = self.maxMinions * self.minionSize + self.playerSize
		return (2, self.boardRowSize)

	def getActionSize(self):
		## actions 0-63 are minion 1-7 attacking targets 1-9 (face is 8, pass is 9)
		## actions 64-223 are playing cards 1-10 at targets 1-16 (7 minions 1 face per player)
		## actions 224-240 are hero power targets 1-16 
		## action 240 is pass
		return 240
	
	def getMinionActionIndex(self, minionIdx, targetIdx):
		return minionIdx * self.enemyTargets + targetIdx

	def extractMinionAction(self, idx):
		base = int(idx / self.enemyTargets)
		remainder = idx % self.enemyTargets
		return base, remainder

	def getCardActionIndex(self, cardIdx, targetIdx):
		return self.maxMinionTargetIndex + cardIdx * self.totalTargets + targetIdx

	def getHeroPowerActionIndex(self, targetIdx):
		return self.maxCardTargetIndex + targetIdx

	def extractCardAction(self, idx):
		idx -= self.maxMinionTargetIndex
		base = int(idx / self.totalTargets)
		remainder = idx % self.totalTargets
		return base, remainder
	
	def getHeroPowerActionIndex(self, targetIdx):
		return self.maxCardTargetIndex + targetIdx
		
	def extractHeroPowerAction(self, idx):
		idx -= self.maxMinionTargetIndex
		idx -= self.totalTargets
		remainder = idx % self.totalTargets
		return 0, remainder
	
	def extractAction(self, action):
		if action < self.maxMinionTargetIndex:
			a,b = self.extractMinionAction(action)
			return ("attack", a, b)

		elif action < self.maxCardTargetIndex:
			a,b = self.extractCardAction(action)
			return ("card", a, b) 

		elif action < self.getActionSize() - 1:
			a,b = self.extractHeroPowerAction(action)
			return ("hero_power", a, b) 
			
		elif action == self.getActionSize() - 1:
			return ("pass", 0 , 0)
			
		return ("{} INVALID".format(action), ("ATTACK",self.extractMinionAction(action)), ("CARD",self.extractCardAction(action)))
	
	def getNextState(self, board, player, action):
		b = np.copy(board)
		idx = pr(player)
		jdx = pr(-player)
		
		if board[idx][self.playerTurnTrackerIndex] == 0:
			return (b, -player)
		
		game = self.injectBoard(b)
			
		try:			
			if action < self.maxMinionTargetIndex:
				attacker, target = self.extractMinionAction(action)
				minion = game.players[idx].field[attacker]
				
				if target == self.faceTarget:
					minion.attack(game.players[jdx].characters[0])
				elif target == self.passTarget:
					minion.num_attacks = minion.max_attacks + 1 ## exhaust minion on pass
				else:
					minion.attack(game.players[jdx].characters[target+1])

			elif action < self.maxCardTargetIndex:
				cardIdx, target = self.extractCardAction(action)
				card = game.players[idx].hand[cardIdx]

				if not card.requires_target():
					card.play()

				## 0 = own face, 1-7 = own minions
				## 8-14 = enemy minions, 15 = enemy face
				elif target == 0:
					card.play(target=game.players[idx].hero)
				elif target <= 7:
					card.play(target=game.players[idx].field[target - 1])
				elif target <= 14:
					card.play(target=game.players[jdx].field[target - 8])
				elif target == 15:
					card.play(target=game.players[jdx].hero)
					
			## hero power
			elif action < self.getActionSize() - 1:
				_, target = self.extractHeroPowerAction(action)
				if target == self.passTarget:
					game.players[idx].hero.power.use()
					
			elif action == self.getActionSize() - 1:
				game.end_turn()
		except GameOver:
			pass
			
		b = self.extractBoard(game)
		return (b, -player)

	def getValidMoves(self, board, player):
		validMoves = [0 for _ in range(self.getActionSize())]
		validMoves[-1] = 1

		if board[pr(player)][self.playerTurnTrackerIndex] == 0:
			return validMoves
		
		game = self.injectBoard(board)
		enemyPlayer = game.players[pr(-player)]
		player = game.players[pr(player)]
		
		## cards
		for i in range(len(player.hand)):
			card = player.hand[i]
			if card.is_playable(debug=True):
				if not card.requires_target():
					cIdx = self.getCardActionIndex(i, self.passTarget)
					validMoves[cIdx] = 1
				else:	
					## 0 = own face, 1-7 = own minions
					## 8-14 = enemy minions, 15 = enemy face
					for target in card.play_targets:
						tIdx = -1

						if target == player.hero:
							tIdx = 0
							
						elif target == enemyPlayer.hero:
							tIdx = 15
							
						elif target in player.field:
							tIdx = player.field.index(target) + 1
									
						elif target in enemyPlayer.field:
							tIdx = enemyPlayer.field.index(target) + 1 + 7
						
						if tIdx >= 0:
							self.getCardActionIndex(i, tIdx)
							validMoves[self.getCardActionIndex(i, tIdx)] = 1
						
		## attacks
		for i in range(len(player.characters[1:])):
			char = player.characters[1 + i]
			if char.can_attack(debug=False):
				faceIdx = self.getMinionActionIndex(i, self.faceTarget)
				passIdx = self.getMinionActionIndex(i, self.passTarget)
				validMoves[faceIdx] = 1
				validMoves[passIdx] = 1
				
				for j in range(len(enemyPlayer.characters[1:])):
					attackIdx = self.getMinionActionIndex(i, j)
					validMoves[attackIdx] = 1

		## hero power
		if player.hero.power.is_usable() and 1==2: ## NEED TO ADD HERO POWER TO OUR STATE REPRESENTATION OR THIS WILL ALWAYS BE USABLE
			if not player.hero.power.requires_target():
				validMoves[self.getHeroPowerActionIndex(self.passTarget)] = 1
			else:
				for target in player.hero.power.targets:
					tIdx = -1
					if target == player.hero:
						tIdx = 0
						
					elif target == enemyPlayer.hero:
						tIdx = 15
						
					elif target in player.field:
						tIdx = player.field.index(target) + 1
								
					elif target in enemyPlayer.field:
						tIdx = enemyPlayer.field.index(target) + 1 + 7
					
					if tIdx >= 0:
						validMoves[self.getHeroPowerActionIndex(tIdx)] = 1

		return validMoves

	def getGameEnded(self, board, player):
		idx = pr(player)
		jdx = pr(-player)
		
		if board[idx][self.playerHealthIndex] <= 0: return -1
		if board[jdx][self.playerHealthIndex] <= 0: return 1
		return 0

	def getCanonicalForm(self, board, player):
		if player == -1: 
			canonicalBoard = np.zeros(self.getBoardSize())
			canonicalBoard[0] = board[1]
			canonicalBoard[1] = board[0]
			return canonicalBoard

		return board

	def getSymmetries(self, board, pi):
		##jptodo: probs want to sort minions at some point
		return [(board, pi)]

	def stringRepresentation(self, board):
		return board.tostring()
		
	def extractRow(self, player):
		handTracker = [0 for _ in range(len(direwolf.og_deck))]
		deckTracker = [0 for _ in range(len(direwolf.og_deck))]

		minions = []

		for character in player.characters[1:]:
			minions += [character.atk, character.health, int(character.can_attack()), direwolf.og_deck.index(character.id)]
		for _ in range(self.maxMinions - (len(player.characters)-1)):
			minions += [0 for _ in range(self.minionSize)]
		
		for i in range(len(direwolf.og_deck)):
			card = direwolf.og_deck[i]
			handTracker[i] = int( card in [i.id for i in player.hand] )
			deckTracker[i] = int( card in [i.id for i in player.deck] )
		
		row = [0 for _ in range(self.getBoardSize()[1])]
		
		for i in range(self.minionSize * self.maxMinions):
			row[i] = minions[i]
			
		row[self.playerCardsInHandIndex] = len(player.hand)
		row[self.playerHealthIndex] = player.characters[0].health
		row[self.playerManaIndex] = player.mana
		row[self.playerMaxManaIndex] = player.max_mana
		row[self.playerTurnTrackerIndex] = int(player.current_player)
		
		for i in self.handTrackerIndices:
			row[i] = handTracker[self.handTrackerIndices.index(i)]
		
		for i in self.deckTrackerIndices:
			row[i] = deckTracker[self.deckTrackerIndices.index(i)]
		
		return row

	def extractBoard(self, game):
		b = np.zeros(self.getBoardSize())
		b[0] = self.extractRow(game.players[0])
		b[1] = self.extractRow(game.players[1])
		return b
	
	def syncBoard(self, board):
		return self.extractBoard(self.injectBoard(board))

	def injectBoard(self, board):
		game = direwolf.setup_game()
		
		for idx in [0,1]:		
			player = game.players[idx]
			row = board[idx]
			
			mis = [i*self.minionSize for i in range(7)]
			hi = self.playerHealthIndex
			mi = self.playerManaIndex
			tti = self.playerTurnTrackerIndex
			mma = self.playerMaxManaIndex
			hti = [i for i in self.handTrackerIndices]
			dti = [i for i in self.deckTrackerIndices]
			
			if row[tti] == 1: 
				game.current_player = player
			
			player.hand = []
			player.deck = []
			player.hero.damage = player.hero.max_health - row[hi]
			player.max_mana = int(row[mma])
			player.used_mana = int(row[mma] - row[mi])
			
			for mi in mis:
				if row[mi] > 0:
					cardIdx = int(row[mi + self.minionIdIndex])
					card = player.card(direwolf.og_deck[cardIdx])
					card.turns_in_play = 1 if row[mi + self.minionCanAttackIndex] > 0 else 0

					card.atk = row[mi + self.minionAttackIndex]
					card.damage = card.max_health - row[mi + self.minionHealthIndex]
					player.summon(card)

			for i in hti:
				if row[i] == 1:
					card = player.card(direwolf.og_deck[self.handTrackerIndices.index(i)])
					card.zone = Zone.HAND
			
			for i in dti:
				if row[i] == 1:
					card = player.card(direwolf.og_deck[self.deckTrackerIndices.index(i)])
					card.zone = Zone.DECK
					
		return game

		
def listValidMoves(board, player):
	h = HearthstoneGame()
	
	try:
		v = h.getValidMoves(board, player)
	except GameOver:
		return []
	
	l = [i for i in range(len(v)) if v[i] == 1]
	return l
		
def display(board):
	h = HearthstoneGame()
	
	print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
	print(' '.join(["[{}:{} {} ({})]".format(h.extractAction(l)[0], h.extractAction(l)[1], h.extractAction(l)[2], l) for l in listValidMoves(board, 1)]))
	print()
	
	j = 0
	print(int(board[j][h.playerHealthIndex]), int(board[j][h.playerManaIndex]), [direwolf.og_deck_names[h.handTrackerIndices.index(i)] for i in h.handTrackerIndices if board[j][i] == 1], "*" if board[j][h.playerTurnTrackerIndex] == 1 else "")
	print(["{}/{}{}".format(int(board[j][i]),int(board[j][i+1]), "⁷" if board[j][i+2]==0 else "") for i in range(0, 28, 4) if board[j][i]>0])
	
	print()
	
	j = 1
	print(["{}/{}{}".format(int(board[j][i]),int(board[j][i+1]), "⁷" if board[j][i+2]==0 else "") for i in range(0, 28, 4) if board[j][i]>0])
	print(int(board[j][h.playerHealthIndex]), int(board[j][h.playerManaIndex]), [direwolf.og_deck_names[h.handTrackerIndices.index(i)] for i in h.handTrackerIndices if board[j][i] == 1], "*" if board[j][h.playerTurnTrackerIndex] == 1 else "")
	
	print()
	print(' '.join(["[{}:{} {} ({})]".format(h.extractAction(l)[0], h.extractAction(l)[1], h.extractAction(l)[2], l) for l in listValidMoves(board, -1)]))
	
	print("\n")
	

def dfs(graph, start, end):
    """
    Compute dfs for a graph
    :param graph: The given graph
    :param start: Node to start bfs
    :param end: Goal-node
    """
    frontier = [start, ]
    explored = []

    while True:
        if len(frontier) == 0:
            raise Exception("No way Exception")
        current_node = frontier.pop()
        explored.append(current_node)

        # Check if node is goal-node
        if current_node == end:
            return

        # expanding nodes
        for node in reversed(graph[current_node]):
            if node not in explored:
                frontier.append(node)
				
def dfs_lethal_solver(board):
	h = HearthstoneGame()
	frontier = [board, ]
	explored = []
	parents = {}
	goal_node = None
	
	while True:
		if len(frontier) == 0:
			return []
		current_node = frontier.pop()
		explored.append(str(current_node))

		# Check if node is goal-node
		if current_node[1][h.playerHealthIndex] <= 0:
			goal_node = current_node
			break

		# get nodes we're connected to
		connected_nodes = []
		validMoves = h.getValidMoves(current_node, 1)[:-1]
		validMoves = [i for i in range(len(validMoves)) if validMoves[i] == 1]
		
		for v in validMoves:
			new_node = h.getNextState(current_node, 1, v)[0]
			parents[str(new_node)] = (current_node, v)
			connected_nodes.append(new_node)
		
		# expanding nodes
		for node in connected_nodes:
			if str(node) not in explored:
				frontier.append(node)
				
	path = []
	print(goal_node)
	c_node = (goal_node, None)
	
	while str(c_node[0]) != str(board):
		c_node = parents[str(c_node[0])]
		path.append(c_node[1])
	
	return path[::-1]
				
	

## -- tests -- ##
h=HearthstoneGame()

def test_dfsLethalSolver_frostboltFace():
	b = h.getInitBoard()
	fsIdx = direwolf.og_deck_names.index("Frostbolt")

	b[0][h.handTrackerIndices[fsIdx]] = 1
	b[0][h.playerManaIndex] = 10
	b[1][h.playerHealthIndex] = 3
	
	lethal = dfs_lethal_solver(b)
	assert(len(lethal) > 0)
	
def test_dfsLethalSolver_frostboltAndAttack():
	b = h.getInitBoard()
	fsIdx = direwolf.og_deck_names.index("Frostbolt")

	b[0][h.handTrackerIndices[fsIdx]] = 1
	b[0][h.playerManaIndex] = 10
	b[1][h.playerHealthIndex] = 4
	
	b[0][0] = 1
	b[0][1] = 1
	b[0][2] = 1
	b[0][3] = 0
	
	b[1][0] = 1
	b[1][1] = 1
	b[1][2] = 1
	b[1][3] = 0
	
	lethal = dfs_lethal_solver(b)
	assert(len(lethal) > 0)
	
def test_getHeroPowerAction():
	idx = h.getHeroPowerActionIndex(0)
	_, ex = h.extractHeroPowerAction(idx)
	
	assert(ex == 0)
	assert(h.getHeroPowerActionIndex(h.passTarget)==231)
	
def test_frostboltingEveryone():
	b = h.getInitBoard()
	fsIdx = direwolf.og_deck_names.index("Frostbolt")

	b[0][h.handTrackerIndices[fsIdx]] = 1
	b[0][h.playerManaIndex] = 10
	
	for i in [j*h.minionSize for j in range(h.maxMinions)]:
		for k in range(h.minionSize):
			b[0][i+k] = 1
			b[1][i+k] = 1
			b[0][i+h.minionCanAttackIndex] = 0
	
	for target in range(h.totalTargets):
		cIdx = h.getCardActionIndex(0, target)
		v = h.getValidMoves(b, 1)
		assert(v[cIdx] == 1)
	
def test_extractFinalCardIndex():
	action = h.getCardActionIndex(9, 15)
	assert(h.extractAction(action) == ("card", 9, 15))
	assert(h.extractAction(167) == ("card", 6, 8))

def test_handleUntargetedSpell():
	b = h.getInitBoard()
	fsIdx = direwolf.og_deck_names.index("Flamestrike")

	b[0][h.handTrackerIndices[fsIdx]] = 1
	b[1][0] = 1
	b[1][1] = 1
	b[1][2] = 0
	b[1][3] = 0
	b[0][h.playerManaIndex] = 10

	b,p = h.getNextState(b,1,h.getCardActionIndex(0,h.passTarget))

	assert(b[1][0] == 0)
	assert(b[1][1] == 0)

def test_ogDeck_noDuplicates():
	assert(len(direwolf.og_deck) == len(list(set(direwolf.og_deck))))

def test_handleTargetedCardOnlyMinionTarget():
	b = h.getInitBoard()
	exIdx = direwolf.og_deck_names.index("Blessing of Kings")
	cwIdx = direwolf.og_deck_names.index("Chillwind Yeti")

	b[0][h.handTrackerIndices[exIdx]] = 1
	b[1][0] = 4
	b[1][1] = 5
	b[1][2] = 0
	b[1][3] = cwIdx
	b[0][h.playerManaIndex] = 10

	b,p = h.getNextState(b, 1, h.getCardActionIndex(0,8))

	assert(b[1][0] == 8)
	assert(b[1][1] == 9)

def test_handleExecute():
	b = h.getInitBoard()
	exIdx = direwolf.og_deck_names.index("Execute")
	cwIdx = direwolf.og_deck_names.index("Chillwind Yeti")

	b[0][h.handTrackerIndices[exIdx]] = 1

	b[0][0] = 1
	b[0][1] = 1
	b[0][2] = 1
	b[0][3] = 0
	b[1][0] = 4
	b[1][1] = 5
	b[1][2] = 0
	b[1][3] = cwIdx
	b[0][h.playerManaIndex] = 10
	b = h.syncBoard(b)

	b,p = h.getNextState(b, 1, h.getMinionActionIndex(0,0))

	g = h.injectBoard(b)
	display(b)

	b,p = h.getNextState(b, 1, h.getCardActionIndex(0,8))

	assert(b[1][0] == 0)
	assert(b[1][1] == 0)

def test_handleTargetedCardAnyTarget():
	b = h.getInitBoard()
	fsIdx = direwolf.og_deck_names.index("Frostbolt")

	b[0][h.handTrackerIndices[fsIdx]] = 1
	b[1][0] = 1
	b[1][1] = 1
	b[1][2] = 0
	b[1][3] = 0
	b[0][h.playerManaIndex] = 10

	b,p = h.getNextState(b, 1, h.getCardActionIndex(0,0))

	assert(b[0][0] == 0)
	assert(b[0][1] == 0)

def test_minionPassing_advancement():
	board = h.getInitBoard()
	
	board[0][h.playerMaxManaIndex] = 10
	board[0][h.handTrackerIndices[0]] = 1
	board[0][0] = 1
	board[0][1] = 1
	board[0][2] = 1
	board[0][3] = 0
	
	board,p = h.getNextState(board, 1, h.passTarget)
	v = h.getValidMoves(board, p)
	
	assert(v[h.passTarget] == 0)
	
def test_injectBoard_fatigueDeath():
	board = h.getInitBoard()
	p=1
	for i in range(100): board, p = h.getNextState(board, p, 239)

def test_getNextState_canAttackForLethal():
	board = h.getInitBoard()
	board[1][h.playerHealthIndex] = 3
	board[0][0] = 5
	board[0][1] = 1
	board[0][2] = 1
	board[0][3] = 2
	display(board)
	
	p=1
	board, p = h.getNextState(board, p, 7)

def test_getNextState_cardsPlayedThisTurn():
	board = h.getInitBoard()

	board[0][h.handTrackerIndices[0]] = 1

	game = h.injectBoard(board)
	action = h.getCardActionIndex(0, h.passTarget)
	player = 1
	nextBoard, nextPlayer = h.getNextState(board, player, action)
	
	assert(game.players[0].cards_played_this_turn == 0)

def test_injectExtractMatch():
	board = h.getInitBoard()
	game = h.injectBoard(board)
	nboard = h.extractBoard(game)
	
	for i in range(len(board[0])):
		assert(board[0][i] == nboard[0][i])
	
def test_injectBoard_allMinions():
	board = h.getInitBoard()
	
	for i in h.handTrackerIndices:
		for j in [0,1]:
			board[j][i] = 1
	
	game = h.injectBoard(board)
	
	player = game.players[0]
	jplayer = game.players[1]
	
	assert(len(player.hand) == len(direwolf.og_deck))
	assert(len(jplayer.hand) == len(direwolf.og_deck))
	
def test_injectBoard_cardsInHand_afterOneTurn():
	board = h.getInitBoard()
	game = h.injectBoard(board)
	player = game.players[0]
	jplayer = game.players[1]
	game.end_turn()
	game.end_turn()
	
	assert(len(player.hand) == 1)
	assert(len(jplayer.hand) == 1)
	
def test_injectBoard_cardsInHand_onInit():
	board = h.getInitBoard()
	game = h.injectBoard(board)
	player = game.players[0]
	
	assert(len(game.players[0].hand) == 0)

def test_initBoard_correctDeck():
	board = h.getInitBoard()
	game = h.injectBoard(board)
	player = game.players[0]
	
	assert(len(player.deck) == len(direwolf.og_deck))
	
def test_getGameEnded_player2Win():
	board = h.getInitBoard()
	board[0][h.playerHealthIndex] = 0
	
	assert(h.getGameEnded(board, 1) == -1)
	assert(h.getGameEnded(board, -1) == 1)
	
def test_getGameEnded_player1Win():
	board = h.getInitBoard()
	board[1][h.playerHealthIndex] = 0
	
	assert(h.getGameEnded(board, 1) == 1)
	assert(h.getGameEnded(board, -1) == -1)
	
def test_getNextState_endOfGame():
	board = h.getInitBoard()
	board[0][h.playerHealthIndex] = 0
	
	h.getNextState(board, 1, h.getActionSize()-1)
	
	assert(h.getGameEnded(board, 1) == -1)
		
def test_getNextState_playCard_player1():
	board = h.getInitBoard()

	board[0][h.handTrackerIndices[0]] = 1

	game = h.injectBoard(board)
	action = h.getCardActionIndex(0, h.passTarget)
	player = 1

	nextBoard, nextPlayer = h.getNextState(board, player, action)
	assert(nextPlayer == -1)
	assert(nextBoard[0][0] == 1)

def test_getNextState_blankPass_player1():
	board = h.getInitBoard()
	action = h.getActionSize() - 1
	player = 1

	nextBoard, nextPlayer = h.getNextState(board, player, action)
	assert(nextPlayer == -1)
	assert(nextBoard[0][h.playerTurnTrackerIndex] == 0)
	
def test_getNextState_blankPass_player2():
	board = h.getInitBoard()
	game = h.injectBoard(board)
	game.end_turn()
	board = h.extractBoard(game)
	action = h.getActionSize() - 1
	player = -1

	nextBoard, nextPlayer = h.getNextState(board, player, action)
	assert(nextPlayer == -player)
	assert(nextBoard[0][h.playerTurnTrackerIndex] == 1)

def test_getNextState_minionGoesFace_player2():
	board = h.getInitBoard()
	board[1][0] = 2
	board[1][1] = 3
	board[1][2] = 1
	board[1][3] = 1

	game = h.injectBoard(board)
	game.end_turn()

	board = h.extractBoard(game)
	action = h.getMinionActionIndex(0, h.faceTarget)
	player = -1

	nextBoard, nextPlayer = h.getNextState(board, player, action)
	assert(nextBoard[0][h.playerHealthIndex] == h.startingHealth - 2)

def test_getNextState_oneMinionAttacking_oneMinionDefending_player1():
	board = h.getInitBoard()
	mId = 1

	board[0][0] = 2
	board[0][1] = 3
	board[0][2] = 0
	board[0][3] = mId
	
	board[1][0] = 2
	board[1][1] = 3
	board[1][2] = 0
	board[1][3] = mId
	
	game = h.injectBoard(board)
	game.end_turn()
	game.end_turn()
	b = h.extractBoard(game)
	
	b, p = h.getNextState(b, 1, h.getMinionActionIndex(0, 0))

	assert(p == -1)
	assert(b[0][1] == 1)
	assert(b[1][1] == 1)


def test_getNextState_oneMinionAttacking_oneMinionDefending_player2():
	board = h.getInitBoard()
	mId = 1

	board[0][0] = 2
	board[0][1] = 3
	board[0][2] = 0
	board[0][3] = mId
	
	board[1][0] = 2
	board[1][1] = 3
	board[1][2] = 0
	board[1][3] = mId
	
	game = h.injectBoard(board)
	game.end_turn()
	b = h.extractBoard(game)
	
	b, p = h.getNextState(b, -1, h.getMinionActionIndex(0, 0))

	assert(p == 1)
	assert(b[0][1] == 1)
	assert(b[1][1] == 1)

def test_getValidMoves_playCard_player1():
	board = h.getInitBoard()

	board[0][h.handTrackerIndices[0]] = 1

	game = h.injectBoard(board)
	
	v = h.getValidMoves(board, 1)
	action = h.getCardActionIndex(0, h.passTarget)
	assert(v[action] == 1)
	
def test_getValidMoves_onlyPass():
	board = h.getInitBoard()
	validMoves = h.getValidMoves(board, 1)
	assert(validMoves[-1] == 1)
	
def test_getValidMoves_oneSleepingMinion():
	board = h.getInitBoard()
	mId = 1
	
	board[0][0] = 1
	board[0][1] = 0
	board[0][2] = 0
	board[0][3] = mId
	
	v = h.getValidMoves(board, 1)
	assert(v[h.getMinionActionIndex(0, 0)] == 0)
	assert(v[h.getMinionActionIndex(0, 2)] == 0)
	assert(v[h.getMinionActionIndex(0, h.faceTarget)] == 0)
	assert(v[h.getMinionActionIndex(0, h.passTarget)] == 0)
	
def test_getValidMoves_oneMinionAttacking():
	board = h.getInitBoard()
	mId = 1
	
	board[0][0] = 2
	board[0][1] = 3
	board[0][2] = 0
	board[0][3] = mId
	
	game = h.injectBoard(board)
	game.end_turn()
	game.end_turn()
	b = h.extractBoard(game)
	
	v = h.getValidMoves(b, 1)
	assert(v[h.getMinionActionIndex(0, 0)] == 0)
	assert(v[h.getMinionActionIndex(0, 2)] == 0)
	assert(v[h.getMinionActionIndex(0, h.faceTarget)] == 1)
	assert(v[h.getMinionActionIndex(0, h.passTarget)] == 1)

def test_getValidMoves_oneMinionAttacking_oneMinionDefending_player1():
	board = h.getInitBoard()
	mId = 1
	
	board[0][0] = 2
	board[0][1] = 3
	board[0][2] = 0
	board[0][3] = mId
	
	board[1][0] = 2
	board[1][1] = 3
	board[1][2] = 0
	board[1][3] = mId
	
	game = h.injectBoard(board)
	
	game.end_turn()
	game.end_turn()
	b = h.extractBoard(game)
	
	v = h.getValidMoves(b, 1)
	assert(v[h.getMinionActionIndex(0, 0)] == 1)
	assert(v[h.getMinionActionIndex(0, 2)] == 0)
	assert(v[h.getMinionActionIndex(0, h.faceTarget)] == 1)
	assert(v[h.getMinionActionIndex(0, h.passTarget)] == 1)
	
def test_getValidMoves_oneMinionAttacking_oneMinionDefending_player2():
	board = h.getInitBoard()
	mId = 1
	
	board[0][0] = 2
	board[0][1] = 3
	board[0][2] = 0
	board[0][3] = mId
	
	board[1][0] = 2
	board[1][1] = 3
	board[1][2] = 0
	board[1][3] = mId
	
	game = h.injectBoard(board)
	game.end_turn()

	b = h.extractBoard(game)
	
	v = h.getValidMoves(b, -1)
	assert(v[h.getMinionActionIndex(0, 0)] == 1)
	assert(v[h.getMinionActionIndex(0, 2)] == 0)
	assert(v[h.getMinionActionIndex(0, h.faceTarget)] == 1)
	assert(v[h.getMinionActionIndex(0, h.passTarget)] == 1)

	
def test_injectAndExtract():
	board = h.getInitBoard()
	mId = 1
	
	board[0][0] = 1
	board[0][1] = 0
	board[0][2] = 0
	board[0][3] = mId
	
	irow = board[0]
	game = h.injectBoard(board)
	prow = h.extractRow(game.players[0])
	
	assert(len(irow) == len(prow))
	assert([irow[i] == prow[i] for i in range(len(irow))])
	
def test_extractRow():
	board = h.getInitBoard()
	mId = 1
	
	board[0][0] = 2
	board[0][1] = 3
	board[0][2] = 0
	board[0][3] = mId
	
	game = h.injectBoard(board)
	
	for i in [0,1]:
		row = h.extractRow(game.players[i])
		assert(row[h.playerHealthIndex] == h.startingHealth)
		assert(row[h.playerManaIndex] == 1)
		assert(row[h.playerMaxManaIndex] == 1)
	
	row = h.extractRow(game.players[0])
	assert(row[0] == 2)
	assert(row[1] == 3)
	assert(row[2] == 0)
	assert(row[3] == mId)
	
def test_injectBoard():
	board = h.getInitBoard()
	mId = 1
	
	board[0][0] = 2
	board[0][1] = 3
	board[0][2] = 0
	board[0][3] = mId
	
	game = h.injectBoard(board)
	
	for i in [0,1]:
		player = game.players[i]
		assert(player.hero.health == h.startingHealth)
		assert(player.mana == 1)
		assert(player.max_mana == 1)
	assert(game.board[0].id == direwolf.og_deck[mId])
	assert(game.current_player == game.players[0])
	assert(len(game.board) == 1)

def test_injectBoard_handIndex():
	board = h.getInitBoard()

	board[0][h.handTrackerIndices[0]] = 1

	game = h.injectBoard(board)
	assert(game.players[0].hand[0].id == direwolf.og_deck[0])
	
def test_getBoardSize():
	assert(h.getBoardSize() == (2, h.maxMinions * h.minionSize + h.playerSize))
	
def test_getInitBoard():
	initBoard = h.getInitBoard()

	for idx in [0,1]:
		row = initBoard[idx]
		assert(row[h.playerHealthIndex] == h.startingHealth)
		assert(row[h.playerManaIndex] == 1)
		assert(row[h.playerCardsInHandIndex] == 0)

		for i in h.deckTrackerIndices:
			assert(row[i] == 1)
			
def test_getActionSize():
	assert(h.getActionSize() == 240)
	
def test_getGameEnded_draw():
	player = 1
	board = h.getInitBoard()
	assert(h.getGameEnded(board,player) == 0)
	
def test_getGameEnded():
	player = 1
	idx = pr(player)
	board = h.getInitBoard()
	board[idx][h.playerHealthIndex] = -1
	assert(h.getGameEnded(board,-player) == 1)
	assert(h.getGameEnded(board,player) == -1)
	
def test_getMinionActionIndex():
	assert(h.getMinionActionIndex(0,0) == 0)
	assert(h.getMinionActionIndex(1,0) == h.enemyTargets)
	
def test_getCardActionIndex():
	assert(h.getCardActionIndex(0,0) == h.maxMinions * h.enemyTargets)
	assert(h.getCardActionIndex(1,0) == h.maxMinions * h.enemyTargets + h.totalTargets)

def test_extractMinionAction():
	idx = h.getMinionActionIndex(3, 4)
	assert(h.extractMinionAction(idx)[0] == 3)
	assert(h.extractMinionAction(idx)[1] == 4)

def test_extractCardAction():
	idx = h.getCardActionIndex(9, 11)
	assert(h.extractCardAction(idx)[0] == 9)
	assert(h.extractCardAction(idx)[1] == 11)

def test_heroPowerTargeted():
	b = h.getInitBoard()
	g = h.injectBoard(b)
	p = g.players[0]
	heropower = p.hero.power

	b[0][h.playerManaIndex] = 10
	
	for i in [j*h.minionSize for j in range(h.maxMinions)]:
		for k in range(h.minionSize):
			b[0][i+k] = 1
			b[1][i+k] = 1
			b[0][i+h.minionCanAttackIndex] = 0
	
	v = h.getValidMoves(b, 1)
	for target in range(h.totalTargets):
		hIdx = h.getHeroPowerActionIndex(target)
		assert(v[hIdx] == 1 or not heropower.requires_target())

def test_heroPowerUntargeted():
	b = h.getInitBoard()
	g = h.injectBoard(b)
	p = g.players[0]
	heropower = p.hero.power

	b[0][h.playerManaIndex] = 10
	v = h.getValidMoves(b, 1)
	assert(v[h.getHeroPowerActionIndex(h.passTarget)] == 1 or heropower.requires_target())

def test_heroAttack():
	pass

def test_weaponSummon():
	pass

def test_handleChargeMinion():
	pass

def test_canOnlyHeroPowerOnce():
	pass
	

import sys; sys.path.insert(0, '../fireplace')
import numpy as np
import fireplace.cards
import copy 
import py
import hs.direwolf as direwolf
import logging; logging.getLogger("fireplace").setLevel(logging.WARNING)
from hearthstone.enums import Zone
import pytest
from fireplace.exceptions import GameOver
	
def pr(player):
	return 0 if player == 1 else 1
def test_pr():
	assert(pr(1) == 0)
	assert(pr(-1) == 1)

class HearthstoneGame():
	def __init__(self):
		self.startingHealth = 10
		self.maxMinions = 7
		self.minionSize = 4
		self.deckSize = 5

		self.minionSize = 4
		
		self.playerTurnTrackerIndex = -4
		self.playerHealthIndex = -3
		self.playerManaIndex = -2
		self.playerCardsInHandIndex = -1
		
		self.starterDeck = [0,1,2,3,4]
		
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
				row[self.playerHealthIndex] = 3
				row[self.playerManaIndex] = 1
				row[self.playerMaxManaIndex] = 1
				row[self.playerCardsInHandIndex] = 3
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
		return self.maxMinions * self.enemyTargets + cardIdx * self.totalTargets + targetIdx

	def extractCardAction(self, idx):
		idx -= self.maxMinions * self.enemyTargets
		base = int(idx / self.totalTargets)
		remainder = idx % self.totalTargets
		return base, remainder
	
	def getNextState(self, board, player, action):
		b = np.copy(board)

		game = self.injectBoard(b)
		idx = pr(player)
		jdx = pr(-player)

		if action <= self.maxMinions * self.enemyTargets:
			attacker, target = self.extractMinionAction(action)
			minion = game.players[idx].field[attacker]
			
			if target == self.faceTarget:
				minion.attack(game.players[jdx].characters[0])
			elif target == self.passTarget:
				pass
			else:
				minion.attack(game.players[jdx].characters[target+1])

		elif action > self.maxMinions * self.enemyTargets and action <= 10 * self.totalTargets:
			cardIdx, target = self.extractCardAction(action)

			if target == self.passTarget:
				card = game.players[idx].hand[cardIdx]
				card.is_playable(debug=True)
				card.play()

		elif action == self.getActionSize() - 1:
			try:
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
			if card.is_playable():
				cIdx = self.getCardActionIndex(i, 0)
				validMoves[cIdx] = 1
				
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
		handTracker = [card for card in direwolf.og_deck]
		deckTracker = [card for card in direwolf.og_deck]

		minions = []

		for character in player.characters[1:]:
			minions += [character.atk, character.health, int(character.can_attack()), direwolf.og_deck.index(character.id)]
		for _ in range(self.maxMinions - (len(player.characters)-1)):
			minions += [0 for _ in range(self.minionSize)]
		
		for card in direwolf.og_deck:
			handTracker[handTracker.index(card)] = int( card in [i.id for i in player.hand] )
			deckTracker[deckTracker.index(card)] = int( card in [i.id for i in player.deck] )
		
		row = [0 for _ in range(self.getBoardSize()[1])]
		
		for i in range(self.minionSize * self.maxMinions):
			row[i] = minions[i]
		
		row[self.playerCardsInHandIndex] = len(player.hand)
		row[self.playerHealthIndex] = player.characters[0].health
		row[self.playerManaIndex] = player.mana
		row[self.playerMaxManaIndex] = player.max_mana
		row[self.playerTurnTrackerIndex] = int(player.current_player)
		
		return row

	def extractBoard(self, game):
		b = np.zeros(self.getBoardSize())
		b[0] = self.extractRow(game.players[0])
		b[1] = self.extractRow(game.players[1])
		return b
	
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
					player.summon(card)

			for i in hti:
				if row[i] == 1:
					card = player.card(direwolf.og_deck[i - self.handTrackerStartingIndex])
					card.zone = Zone.HAND
					player.hand.append(card)

		return game
		

def display(board):
	pass

## -- tests -- ##
h=HearthstoneGame()

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
	
	with pytest.raises(GameOver):
		h.getNextState(board, 1, h.getActionSize()-1)
		

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
	board[1][0] = 1
	board[1][1] = 0
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

	board[0][0] = 1
	board[0][1] = 0
	board[0][2] = 0
	board[0][3] = mId
	
	board[1][0] = 1
	board[1][1] = 0
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

	board[0][0] = 1
	board[0][1] = 0
	board[0][2] = 0
	board[0][3] = mId
	
	board[1][0] = 1
	board[1][1] = 0
	board[1][2] = 0
	board[1][3] = mId
	
	game = h.injectBoard(board)
	game.end_turn()
	b = h.extractBoard(game)
	
	b, p = h.getNextState(b, -1, h.getMinionActionIndex(0, 0))

	assert(p == 1)
	assert(b[0][1] == 1)
	assert(b[1][1] == 1)

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
	
	board[0][0] = 1
	board[0][1] = 0
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
	
	board[0][0] = 1
	board[0][1] = 0
	board[0][2] = 0
	board[0][3] = mId
	
	board[1][0] = 1
	board[1][1] = 0
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
	
	board[0][0] = 1
	board[0][1] = 0
	board[0][2] = 0
	board[0][3] = mId
	
	board[1][0] = 1
	board[1][1] = 0
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
	
	board[0][0] = 1
	board[0][1] = 0
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
	
	board[0][0] = 1
	board[0][1] = 0
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
		assert(row[h.playerCardsInHandIndex] == 3)

		for i in h.deckTrackerIndices:
			assert(row[i] == 0)
			
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

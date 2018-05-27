import sys; sys.path.insert(0, '../clean/src/fireplace')
import numpy as np
import fireplace
import copy 
import py

def pr(player):
	return 0 if player == 1 else 1
def test_pr():
	assert(pr(1) == 0)
	assert(pr(-1) == 1)

class Game():
	def __init__(self):
		self.playerHealthIndex = -3
		self.playerManaIndex = -2
		self.playerCardsInHandIndex = -1
		self.starterDeck = [0,1,2,3,4]
		self.deckTrackerIndices = [i for i in range(self.playerHealthIndex-1, self.playerHealthIndex-len(self.starterDeck)-1, -1)]

		self.hpSize = 1
		self.manaSize = 1
		self.cardsInHandSize = 1

		self.minionSize = 3
		self.deckSize = 5

		self.playerSize = self.hpSize + self.manaSize + self.cardsInHandSize + self.deckSize
		self.minionSize = 4

	def getInitBoard(self):
		"""
		Returns:
			startBoard: a representation of the board (ideally this is the form
						that will be the input to your neural network)
		"""
		board = np.zeros(self.getBoardSize())

		for i in [0,1]:
				row = board[i]
				row[self.playerHealthIndex] = 30
				row[self.playerManaIndex] = 1
				row[self.playerCardsInHandIndex] = 3

		return board

	def getBoardSize(self):
		"""
		Returns:
			(x,y): a tuple of board dimensions
		"""
		## player array size = 7 * minionSize + hp + mana + #cards_in_hand + deck_tracker
		self.boardRowSize = 7 * self.minionSize + self.hpSize + self.manaSize + self.cardsInHandSize + self.deckSize
		return (2, self.boardRowSize)

	def getActionSize(self):
		## actions 0-63 are minion 1-7 attacking targets 1-9 (face is 8, pass is 9)
		## actions 64-223 are playing cards 1-10 at targets 1-16 (7 minions 1 face per player)
		## actions 224-240 are hero power targets 1-16 
		## action 240 is pass
		return 240

	def getNextState(self, board, player, action):
		"""
		Input:
			board: current board
			player: current player (1 or -1)
			action: action taken by current player

		Returns:
			nextBoard: board after applying action
			nextPlayer: player who plays in the next turn (should be -player)
		"""
		b = copy.deepcopy(board)
		return (b, -player)

	def getValidMoves(self, board, player):
		"""
		Input:
			board: current board
			player: current player

		Returns:
			validMoves: a binary vector of length self.getActionSize(), 1 for
						moves that are valid from the current board and player,
						0 for invalid moves
		"""
		validMoves = [0 for _ in range(self.getActionSize())]
		validMoves[-1] = 1
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
		#probs want to sort minions at some point
		return [(board, pi)]

	def stringRepresentation(self, board):
		"""
		Input:
			board: current board

		Returns:
			boardString: a quick conversion of board to a string format.
						 Required by MCTS for hashing.
		"""
		return board.tostring()

def display(board):
	pass

## -- tests -- ##
h=Game()
def test_getBoardSize():
	assert(h.getBoardSize() == (2, 36))

def test_getInitBoard():
	initBoard = h.getInitBoard()

	for idx in [0,1]:
		row = initBoard[idx]
		assert(row[h.playerHealthIndex] == 30)
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
from __future__ import print_function
import sys
import numpy as np

class HearthstoneGame():
	"""
	This class specifies the base Game class. To define your own game, subclass
	this class and implement the functions below. This works when the game is
	two-player, adversarial and turn-based.

	Use 1 for player1 and -1 for player2.

	See othello/OthelloGame.py for an example implementation.
	"""
	def __init__(self):
		## size per player is: minion_slot * 7 + hp:1 + mana:1 + turns_taken:1 = 21 + 1 + 1 + 1 = 24
		self.playerSize = 3
		self.minionSize = 3
		
		self.playerHealthIndex = -3
		self.playerManaIndex = -2
		self.playerTurnCountIndex = -1
		
		self.minionAttackIndex = 0
		self.minionHealthIndex = 1
		self.minionAbleIndex = 2
		
		self.sleeping = 0
		self.alreadyAttacked = 1
		self.canAttack = 2
		
		self.minionIndices = [i*self.minionSize for i in range(7)]

	def getInitBoard(self):
		b = np.zeros(self.getBoardSize())
		
		for player in [0,1]:
			b[player][self.playerHealthIndex] = 3
			b[player][self.playerManaIndex] = 1
			
		return b

	def getBoardSize(self):
		return (2, self.minionSize * 7 + self.playerSize)

	def getActionSize(self):
		## 7 minions with 9 targets each, + summon a 1/1, + summon a 2/1, + summon a 1/3, pass entirely
		return 63 + 1 + 1 + 1 + 1
		
	def getNextState(self, board, player, action):
		## action = 0-64
		## action 0 = play a 1/1
		## action 0-8 = attack with minion 0 into slots 0 (face), 1 (pass), 2-8 (enemy minion)
		## action 9-17 = attack with minion 1, etc
		b = np.copy(board)
		newPlayer = player
		
		## get board side row
		rowIndex = 0 if player == 1 else 1
		antiIndex = (rowIndex + 1) % 2
		
		row = b[rowIndex]
		anti = b[antiIndex]
		
		## update turn counter
		b[rowIndex][self.playerTurnCountIndex] += 1
		
		## pass
		if action == self.getActionSize() - 1:
			newPlayer = -player
			
		## summon a new minion
		elif action >= 63:
			row[self.playerManaIndex] -= 1
			
			if action == 63:
				for i in self.minionIndices:
					if row[i] == 0:
						row[i+self.minionAttackIndex] = 1
						row[i+self.minionHealthIndex] = 1
						row[i+self.minionAbleIndex] = self.sleeping
						break
			elif action == 64:
				for i in self.minionIndices:
					if row[i] == 0:
						row[i+self.minionAttackIndex] = 1
						row[i+self.minionHealthIndex] = 3
						row[i+self.minionAbleIndex] = self.sleeping
						break
			elif action == 65:
				for i in self.minionIndices:
					if row[i] == 0:
						row[i+self.minionAttackIndex] = 2
						row[i+self.minionHealthIndex] = 1
						row[i+self.minionAbleIndex] = self.sleeping
					break
		
		## do an attack
		else:
			myMinion = int(action / 9)
			target = action % 9
			
			myMinionIndex = myMinion * self.minionSize
			
			row[myMinionIndex + self.minionAbleIndex] = self.alreadyAttacked
			
			if target == 0:
				anti[self.playerHealthIndex] -= row[myMinionIndex + self.minionAttackIndex]
			elif target == 1:
				pass
			else:
				targetIndex = (target - 2) * self.minionSize ## -2 to account for 2 non minion targets
			
				row[myMinionIndex + self.minionHealthIndex] -= anti[targetIndex + self.minionAttackIndex]
				anti[targetIndex + self.minionHealthIndex] -= row[myMinionIndex + self.minionAttackIndex]
			
				## zero out dead minions
				if row[myMinionIndex + self.minionHealthIndex] <= 0:
					for i in range(self.minionSize):
						row[myMinionIndex + i] = 0
				if anti[targetIndex + self.minionHealthIndex] <= 0:
					for i in range(self.minionSize):
						anti[targetIndex + i] = 0
		
		## check for player swap (no moves available except pass)
		if all([i == 0 for i in self.getValidMoves(b, player)[:-1]]):
			newPlayer = -player
			
		## check if swapping players
		if newPlayer == -player:		
			## wake up sleeping minions
			for mi in self.minionIndices:
				if row[mi] > 0 and row[mi+self.minionAbleIndex] == self.sleeping:
					row[mi+self.minionAbleIndex] = self.canAttack
		
			## minions have no longer already attacked
			for mi in self.minionIndices:
				if row[mi] > 0 and row[mi+self.minionAbleIndex] == self.alreadyAttacked:
					row[mi+self.minionAbleIndex] = self.canAttack
			
			## restore mana crystals
			row[self.playerManaIndex] = 1
					
		## return
		return (b, newPlayer)

	def getValidMoves(self, board, player):
		b = np.copy(board)
		validMoves = [0 for _ in range(self.getActionSize())]
		validMoves[self.getActionSize()-1] = 1 ## can always pass
		
		## get board side row
		rowIndex = 0 if player == 1 else 1
		antiIndex = (rowIndex + 1) % 2
		
		row = b[rowIndex]
		anti = b[antiIndex]
		
		## get number of minions i have
		myMinionIndices = [i for i in self.minionIndices if row[i] > 0]
		
		## get number of minions enemy has
		enemyMinionIndices = [i for i in self.minionIndices if anti[i] > 0]
		
		## if i have less than 7 minions i can summon another one, if i had no minions before that, i'm done
		if len(myMinionIndices) < 7 and row[self.playerManaIndex] >= 1:
			validMoves[63] = 1
			validMoves[64] = 1
			validMoves[65] = 1
		elif len(myMinionIndices) < 1:
			return validMoves
			
		## each minion that doesn't have sleeping sickness can attack each enemy minion + face + pass
		for minionSlot in range(0,6):
			minionIndex = minionSlot * self.minionSize
			
			if row[minionIndex + self.minionAbleIndex] == self.canAttack:
				validMoves[minionSlot * 9] = 1		## every minion can go face
				validMoves[minionSlot * 9 + 1] = 1  ## every minion can pass
				
				for enemyMinionSlot in range(0,6):			
					enemyMinionIndex = enemyMinionSlot * self.minionSize
					
					if b[antiIndex][enemyMinionIndex] > 0:
						validMoves[minionSlot * 9 + 2 + enemyMinionSlot] = 1
						
		return validMoves
		
	def getGameEnded(self, board, player):
		b = np.copy(board)
		rowIndex = 0 if player == 1 else 1
		antiIndex = (rowIndex + 1) % 2
		
		if b[rowIndex][self.playerTurnCountIndex] > 7: return 1e-4
		if b[rowIndex][self.playerHealthIndex] <= 0: return -1
		if b[antiIndex][self.playerHealthIndex] <= 0: return 1
		return 0

	def getCanonicalForm(self, board, player):
		if player == -1:
			canonicalBoard = np.zeros(self.getBoardSize())
			canonicalBoard[0] = board[1]
			canonicalBoard[1] = board[0]
			return canonicalBoard
			
		return board
			
	def getSymmetries(self, board, pi):
		"""
		Input:
			board: current board
			pi: policy vector of size self.getActionSize()

		Returns:
			symmForms: a list of [(board,pi)] where each tuple is a symmetrical
					   form of the board and the corresponding pi vector. This
					   is used when training the neural network from examples.
		"""
		## minion position invariant "symmetries"
		l = []
		
		
		return [(np.copy(board), np.copy(pi))]

	def stringRepresentation(self, board):
		return str(board)

def display(board,valids=False):
	p1row = board[0]
	p2row = board[1]
	
	canAttackSymbols = ["⁷", "*", ""]
	
	ms = ['', '']
	
	for (r,m) in [(p1row, 0), (p2row, 1)]:
		ms[m] = ''.join(["[{}/{}]{}".format(int(r[i]), int(r[i+1]), canAttackSymbols[int(r[i+2])]) for i in range(0, len(r) - 3, 3) if r[i] > 0])
	
	boardString = "             p1:{}\n{}\n\n{}\n             p2:{}".format(int(p1row[-3]), ms[0], ms[1], int(p2row[-3]))
	
	if valids: displayValidMoves(h,b,1)
	print("-"*30)
	print(boardString)
	print("-"*30)
	if valids: displayValidMoves(h,b,-1)
	print("\n\n")
	
def displayValidMoves(game, board, player):
	v = game.getValidMoves(board, player)
	print([i for i in range(len(v)) if v[i] == 1])
		

def runTests():
	h = HearthstoneGame()
	b = h.getInitBoard()
			

if __name__ == '__main__':
	h = HearthstoneGame()
	b = h.getInitBoard()
	
	b, n = h.getNextState(b, 1, 63)
	b, n = h.getNextState(b, -1, 65)
	b, n = h.getNextState(b, 1, 66)
	b, n = h.getNextState(b, -1, 66)
	display(b, True)
	

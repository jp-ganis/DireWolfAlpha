from __future__ import print_function
import sys
import numpy as np

class HearthstoneGame():
	def __init__(self):
		## size per player is: minion_slot * 7 + hp + mana + turns_taken + turn tracker
		self.playerSize = 4
		self.minionSize = 3
		
		self.turnTrackerIndex = -4
		
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
			
		b[0][self.turnTrackerIndex] = 1
		b[1][self.turnTrackerIndex] = 1
			
		return b

	def getBoardSize(self):
		return (2, (self.minionSize * 7) + self.playerSize)

	def getActionSize(self):
		## 7 minions with 9 targets each, + summon a 1/1, + summon a 2/1, + summon a 1/3, pass entirely
		return 63 + 1 + 1 + 1 + 1
		
	def getNextState(self, board, player, action):
		## action = 0-64
		## action 0 = play a 1/1
		## action 0-8 = attack with minion 0 into slots 0 (face), 1 (pass), 2-8 (enemy minion)
		## action 9-17 = attack with minion 1, etc
		b = np.copy(board)
		
		## get board side row
		rowIndex = 0 if player == 1 else 1
		antiIndex = (rowIndex + 1) % 2
		
		row = b[rowIndex]
		anti = b[antiIndex]
		
		## pass
		if action == self.getActionSize() - 1:
			b[0][self.turnTrackerIndex] = -player
			b[1][self.turnTrackerIndex] = -player
			
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
		
		## if we're out of moves, it's the other person's turn
		if sum(self.getValidMoves(b, player)) == 1:
			b[0][self.turnTrackerIndex] = -player
			b[1][self.turnTrackerIndex] = -player
			
		
		## check if swapping players
		if b[0][self.turnTrackerIndex] == -player:	
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
			
			## update turn counter
			b[rowIndex][self.playerTurnCountIndex] += 1
					
		## return
		return (b, -player)

	def getValidMoves(self, board, player):
		b = np.copy(board)
		validMoves = [0 for _ in range(self.getActionSize())]
		validMoves[-1] = 1 ## can always pass
		
		if board[0][self.turnTrackerIndex] != player:
			return validMoves
		
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
		
		if b[rowIndex][self.playerTurnCountIndex] > 5: return 1e-4
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
	h = HearthstoneGame()
	p1row = board[0]
	p2row = board[1]
	
	
	player = board[0][h.turnTrackerIndex]
	v = h.getValidMoves(board, player)
	if sum(v) == 1:
		print("FAUXTURN")
		return
	
	canAttackSymbols = ["⁷", "*", ""]
	
	ms = ['', '']
	
	for (r,m) in [(p1row, 0), (p2row, 1)]:
		ms[m] = ''.join(["[{}/{}]{}".format(int(r[i+h.minionAttackIndex]), int(r[i+h.minionHealthIndex]), canAttackSymbols[int(r[i+h.minionAbleIndex])]) for i in range(0, len(r) - h.playerSize, h.minionSize) if r[i] > 0])
	
	boardString = "             p1:{}1qq\n{}\n\n{}\n             p2:{}2qq".format(int(p1row[h.playerHealthIndex]), ms[0], ms[1], int(p2row[h.playerHealthIndex]))
	
	boardString = boardString.replace("1qq", "ₒ" * int(p1row[h.playerManaIndex])).replace("2qq", "ₒ" * int(p2row[h.playerManaIndex]))
	
	print("-"*30)
	print(boardString)
	print("-"*30+ "[{}]".format(str(int(board[0][h.turnTrackerIndex]))))
	if valids:
		displayValidMoves(h,board,1)
		displayValidMoves(h,board,-1)
	print("\n\n")
	
def displayValidMoves(game, board, player):
	v = game.getValidMoves(board, player)
	print([i for i in range(len(v)) if v[i] == 1])
		
def displayTestMove(h, board, player, action):
	print("~~~~~~~~~~~~~~~~~~~~~~~~~PLAYER {}, ACTION {} ~~~~~~~~~~~~~~~~~~~~~~~~~".format(player,action))
	v = h.getValidMoves(board, player)
	
	if v[action] == 0:
		print("Invalid Action")
		return None, None
	
	b, n = h.getNextState(board, player, action)
	display(b, True)
	return b, n
	
		
def runTests():
	h = HearthstoneGame()
	b = h.getInitBoard()
			

if __name__ == '__main__':
	h = HearthstoneGame()
	b = h.getInitBoard()
	
	b, n = displayTestMove(h, b, 1, 65)
	b, n = displayTestMove(h, b, -1, 65)
	b, n = displayTestMove(h, b, 1, 65)
	b, n = displayTestMove(h, b, -1, 66)
	b, n = displayTestMove(h, b, 1, 0)
	b, n = displayTestMove(h, b, -1, 66)
	

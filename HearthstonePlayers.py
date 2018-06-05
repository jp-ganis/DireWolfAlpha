import numpy as np
from .HearthstoneGame import display

class PassBot():
	def __init__(self, game):
		self.game = game

	def play(self, board):
		return self.game.getActionSize() - 1

class RandBot():
	def __init__(self, game):
		self.game = game

	def play(self, board):
		a = np.random.randint(self.game.getActionSize())
		valids = self.game.getValidMoves(board, 1)
		while valids[a]!=1:
			a = np.random.randint(self.game.getActionSize())
		return a


class HumBot():
	def __init__(self, game):
		self.game = game

	def play(self, board):
		valid = self.game.getValidMoves(board, 1)
		
		if sum(valid) == 1:
			return 239
		
		valid_indices = []
		
		for i in range(len(valid)):
			if valid[i] == 1:
				valid_indices.append(i)
		
		while True:
			a = int(input(":: "))
			
			if valid[a]==1:
				break
			else:
				print('Invalid')
		return a

		
class FaceBot():
	def __init__(self, game):
		self.game = game

	def play(self, board):
		valid = self.game.getValidMoves(board, 1)
		valid_indices = [i for i in range(len(valid)) if valid[i] == 1]
		
		return valid_indices[0]
		
		
class ValueBot():
	def __init__(self, game):
		self.game = game

	def play(self, board):
		valid = self.game.getValidMoves(board, 1)
		valid[63] = 0
		valid_indices = [i for i in range(len(valid)) if valid[i] == 1]
		
		## get current my minions/enemy minions/enemy
		my_mc = sum([board[0][i*4 + 1] for i in range(7)])
		en_mc = sum([board[1][i*4 + 1] for i in range(7)])
		
		for a in valid_indices:
			nb, _ = self.game.getNextState(board, 1, a)
			
			## check if after move i have same minions, enemy has less
			new_mmc = sum([board[0][i*4 + 1] for i in range(7)])
			new_emc = sum([board[1][i*4 + 1] for i in range(7)])
			
			## if so, do that move, otherwise check for any minion actions that go face
			if new_mmc == my_mc and new_emc < en_mc:
				return a
		
		return valid_indices[0]
import numpy as np
from .HearthstoneGame import display

class PassPlayer():
	def __init__(self, game):
		self.game = game

	def play(self, board):
		return self.game.getActionSize() - 1

class RandomPlayer():
	def __init__(self, game):
		self.game = game

	def play(self, board):
		a = np.random.randint(self.game.getActionSize())
		valids = self.game.getValidMoves(board, 1)
		while valids[a]!=1:
			a = np.random.randint(self.game.getActionSize())
		return a


class HumanPlayer():
	def __init__(self, game):
		self.game = game

	def play(self, board):
		# display(board)
		valid = self.game.getValidMoves(board, 1)
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

		
class FacePlayer():
	def __init__(self, game):
		self.game = game

	def play(self, board):
		# display(board)
		valid = self.game.getValidMoves(board, 1)
		valid_indices = []
		
		if valid[63] == 1:
			return 63
		
		for i in [j*3 for j in range(7)]:
			if valid[i] == 1:
				return i
		
		return 66
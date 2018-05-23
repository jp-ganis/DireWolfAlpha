import numpy as np
from .HearthstoneGame import display

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
		
		print("Valid Moves: ", valid_indices)
		
		while True:
			a = int(input())
			
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
		
		for i in range(len(valid)):
			if valid[i] == 1:
				valid_indices.append(i)
		
		print("Face Valid Moves: ", valid_indices)
		
		while True:
			face = [i*3 for i in range(7)]
			
			for f in face:
				if valid[f]==1:
					return f
			else:
				return 65

		return 0
import numpy as np
import random
import math
from hs.HearthstoneGame import display
EPS = 1e-8

class MCTS():
	"""
	This class handles the MCTS tree.
	"""

	def __init__(self, game, args):
		self.game = game
		self.args = args
		self.Qsa = {}	   	# Q matrix
		self.Nsa = {}	   	# stores #times edge s,a was visited
		self.Ns = {}		# stores #times board s was visited
		self.Ps = {}		# stores initial policy 

		self.Es = {}		# stores game.getGameEnded ended for board s
		self.Vs = {}		# stores game.getValidMoves for board s

	def getActionProb(self, canonicalBoard, temp=1):
		"""
		This function performs numMCTSSims simulations of MCTS starting from
		canonicalBoard.

		Returns:
			probs: a policy vector where the probability of the ith action is
				   proportional to Nsa[(s,a)]**(1./temp)
		"""
		for i in range(self.args.numMCTSSims):
			self.search(canonicalBoard)

		s = self.game.stringRepresentation(canonicalBoard)

		counts = [self.Nsa[(s,a)] if (s,a) in self.Nsa else 0 for a in range(self.game.getActionSize())]

		if temp==0:
			bestA = np.argmax(counts)
			probs = [0]*len(counts)
			probs[bestA]=1
			return probs
			
		counts = [x**(1./temp) for x in counts]
		probs = [x/float(sum(counts)) for x in counts]
		return probs


	def search(self, canonicalBoard):
		"""
		This function performs one iteration of MCTS. It is recursively called
		till a leaf node is found. The action chosen at each node is one that
		has the maximum upper confidence bound as in the paper.

		Once a leaf node is found, the neural network is called to return an
		initial policy P and a value v for the state. This value is propogated
		up the search path. In case the leaf node is a terminal state, the
		outcome is propogated up the search path. The values of Ns, Nsa, Qsa are
		updated.

		NOTE: the return values are the negative of the value of the current
		state. This is done since v is in [-1,1] and if v is the value of a
		state for the current player, then its value is -v for the other player.

		Returns:
			v: the negative of the value of the current canonicalBoard
		"""
		s = self.game.stringRepresentation(canonicalBoard)

		if s not in self.Es:
			self.Es[s] = self.game.getGameEnded(canonicalBoard, 1)
		if self.Es[s]!=0:
			# terminal node
			return -self.Es[s]

		## leaf node
		if s not in self.Ps:
			## When it can no longer apply UCT to find the successor node, it expands the game tree by appending all possible states from the leaf node.
			valids = self.game.getValidMoves(canonicalBoard, 1)
			
			self.Ps[s] = np.array([random.random() for _ in range(self.game.getActionSize())])
			self.Ps[s] = self.Ps[s]*valids	  	# masking invalid moves
			sum_Ps_s = np.sum(self.Ps[s])
			self.Ps[s] /= sum_Ps_s				# renormalize
			
			self.Vs[s] = valids
			self.Ns[s] = 0

			## After Expansion, the algorithm picks a child node arbitrarily, and it simulates a randomized game from selected node until it reaches the resulting state of the game.
			## If nodes are picked randomly or semi-randomly during the play out, it is called light play out.
			## You can also opt for heavy play out by writing quality heuristics or evaluation functions.
			value = 0
			nb = np.copy(canonicalBoard)
			nnp = 1
			while self.game.getGameEnded(nb, nnp) == 0:
				nvalids = self.game.getValidMoves(nb, nnp)
				valid_indices = [i for i in range(len(nvalids)) if nvalids[i] == 1]
				nb, nnp = self.game.getNextState(nb, nnp, random.choice(valid_indices))
			return -self.game.getGameEnded(nb, nnp)

		valids = self.Vs[s]
		cur_best = -float('inf')
		best_act = -1

		## pick the action with the highest upper confidence bound
		for a in range(self.game.getActionSize()):
			if valids[a]:
				if (s,a) in self.Qsa:
					u = self.Qsa[(s,a)] + self.args.cpuct*self.Ps[s][a]*math.sqrt(self.Ns[s])/(1+self.Nsa[(s,a)])
				else:
					u = self.args.cpuct*self.Ps[s][a]*math.sqrt(self.Ns[s] + EPS)	 # Q = 0 ?

				if u > cur_best:
					cur_best = u
					best_act = a

		a = best_act
		next_s, next_player = self.game.getNextState(canonicalBoard, 1, a)
		next_s = self.game.getCanonicalForm(next_s, next_player)

		v = self.search(next_s)

		if (s,a) in self.Qsa:
			self.Qsa[(s,a)] = (self.Nsa[(s,a)]*self.Qsa[(s,a)] + v)/(self.Nsa[(s,a)]+1)
			self.Nsa[(s,a)] += 1

		else:
			self.Qsa[(s,a)] = v
			self.Nsa[(s,a)] = 1

		self.Ns[s] += 1
		return -v

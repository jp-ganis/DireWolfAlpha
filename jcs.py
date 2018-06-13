from HearthstoneGame import HearthstoneGame, tostring, dfs_lethal_solver
import direwolf as direwolf

import multiprocessing
from multiprocessing.pool import Pool

import numpy as np
from math import *
import operator
import random
import time
import sys

class HearthState:
	""" A state of the game, i.e. the game board. These are the only functions which are
		absolutely necessary to implement UCT in any 2-player complete information deterministic 
		zero-sum game, although they can be enhanced and made quicker, for example by using a 
		GetRandomMove() function to generate a random move during rollout.
		By convention the players are numbered 1 and 2.
	"""
	def __init__(self):
		self.playerJustMoved = 1 
		self.h = HearthstoneGame()
		self.board = self.h.getInitBoard()
			
	def Clone(self):
		""" Create a deep clone of this game state.
		"""
		st = HearthState()
		st.board = np.copy(self.board)
		st.playerJustMoved = self.playerJustMoved
		return st

	def DoMove(self, move):
		""" Update a state by carrying out the given move.
			Must update playerJustMoved.
		"""
		self.board, _ = self.h.getNextState(self.board, self.playerJustMoved, move)
		self.playerJustMoved = -self.playerJustMoved
		
	def GetMoves(self):
		""" Get all possible moves from this state.
		"""
		if self.board[0][self.h.playerHealthIndex] <= 0 or self.board[1][self.h.playerHealthIndex] <= 0:
			return []
		
		v = self.h.getValidMoves(self.board, self.playerJustMoved)
		v = [i for i in range(self.h.getActionSize()) if v[i] == 1]
		
		return v
		
	def GetRandomMove(self):
		v = self.GetMoves()
		return random.choice(v)
		
	def GetBestBoardControlMove(self):
		v = self.GetMoves()
		if len(v) == 1: return v[0]
		
		best_power_gap = 0
		best_move = v[0]
		
		idx = 0 if self.playerJustMoved == 1 else 1
		jdx = int(not(idx))
		
		for a in v[:-1]:
			b, _ = self.h.getNextState(self.board, self.playerJustMoved, a)
			power_gap = 0
			for i in range(self.h.minionSize * self.h.maxMinions):
				friendly_atk = b[idx][i + self.h.minionAttackIndex]
				friendly_health = b[idx][i + self.h.minionHealthIndex]
				
				enemy_atk = b[jdx][i + self.h.minionAttackIndex]
				enemy_health = b[jdx][i + self.h.minionHealthIndex]
				
				power_gap += friendly_atk + friendly_health
				power_gap -= enemy_atk + enemy_health
				
				if power_gap > best_power_gap:
					best_power_gap = power_gap
					best_move = a
					
		return best_move
				
			
	def GetBestFaceMove(self):
		v = self.GetMoves()
		
		most_damage = 0
		best_move = v[0]
		
		idx = 0 if self.playerJustMoved == 1 else 1
		jdx = int(not(idx))
		
		starting_health = self.board[jdx][self.h.playerHealthIndex]
		
		for a in v:
			b, _ = self.h.getNextState(self.board, self.playerJustMoved, a)
			damage = starting_health - b[jdx][self.h.playerHealthIndex]
			if damage > most_damage:
				most_damage = damage
				best_move = a
					
		return best_move
				
	def GetResult(self, playerjm):
		""" Get the game result from the viewpoint of playerjm. 
		"""
		idx = 0 if playerjm == -1 else 1
		return 1 if self.board[idx][self.h.playerHealthIndex] > 0 else 0
		
	def __repr__(self):
		return tostring(self.board)

class Node:
	""" A node in the game tree. Note wins is always from the viewpoint of playerJustMoved.
		Crashes if state not specified.
	"""
	def __init__(self, move = None, parent = None, state = None):
		self.move = move # the move that got us to this node - "None" for the root node
		self.parentNode = parent # "None" for the root node
		self.childNodes = []
		self.wins = 0
		self.visits = 0
		self.untriedMoves = state.GetMoves() # future child nodes
		self.playerJustMoved = state.playerJustMoved # the only part of the state that the Node needs later
		
	def UCTSelectChild(self):
		""" Use the UCB1 formula to select a child node. Often a constant UCTK is applied so we have
			lambda c: c.wins/c.visits + UCTK * sqrt(2*log(self.visits)/c.visits to vary the amount of
			exploration versus exploitation.
		"""
		s = sorted(self.childNodes, key = lambda c: c.wins/c.visits + sqrt(2*log(self.visits)/c.visits))[-1]
		return s
	
	def AddChild(self, m, s):
		""" Remove m from untriedMoves and add a new child node for this move.
			Return the added child node
		"""
		n = Node(move = m, parent = self, state = s)
		self.untriedMoves.remove(m)
		self.childNodes.append(n)
		return n
	
	def Update(self, result):
		""" Update this node - one additional visit and result additional wins. result must be from the viewpoint of playerJustmoved.
		"""
		self.visits += 1
		self.wins += result
		
	def TreeToString(self, indent):
		s = self.IndentString(indent) + str(self)
		for c in self.childNodes:
			 s += c.TreeToString(indent+1)
		return s

	def IndentString(self,indent):
		s = "\n"
		for i in range (1,indent+1):
			s += "| "
		return s

	def ChildrenToString(self):
		s = ""
		for c in self.childNodes:
			 s += str(c) + "\n"
		return s

	def __repr__(self):
		return "[M:" + str(self.move) + " W/V:" + str(self.wins) + "/" + str(self.visits) + " U:" + str(self.untriedMoves) + "]"
		
	def __add__(self, other):
		mergedNode = Node(state=HearthState())
		mergedNode.playerJustMoved = self.playerJustMoved
		
		mergedNode.wins = self.wins + other.wins
		mergedNode.visits = self.visits + other.visits
		
		for child_a in self.childNodes:
			for child_b in other.childNodes:
				if child_a.move == child_b.move:
					mergedNode.childNodes.append(child_a + child_b)
					
		return mergedNode
		
		

""" 
Conduct a UCT search for itermax iterations starting from rootstate.
Return the best move from the rootstate.
Assumes 2 alternating players (player 1 starts), with game results in the range [0.0, 1.0].
"""
def UCT(rootstate, itermax, verbose=False, parallel=False, bestNode=False, prebuiltNode=None):
	rootnode = Node(state = rootstate) if prebuiltNode is None else prebuiltNode

	for i in range(itermax):
		if verbose: print("[{}/{}]".format(i+1,itermax), end="\r")
		node = rootnode
		state = rootstate.Clone()

		# Select
		while node.untriedMoves == [] and node.childNodes != []: # node is fully expanded and non-terminal
			node = node.UCTSelectChild()
			state.DoMove(node.move)

		# Expand
		if node.untriedMoves != []: # if we can expand (i.e. state/node is non-terminal)
			m = random.choice(node.untriedMoves) 
			state.DoMove(m)
			node = node.AddChild(m,state) # add child and descend tree

		# Rollout - this can often be made orders of magnitude quicker using a state.GetRandomMove() function
		while state.GetMoves() != []:
			r = random.random()
			if r < 0.5:
				state.DoMove(state.GetRandomMove())
			elif r < 0.6:
				state.DoMove(state.GetBestFaceMove())
			else:
				state.DoMove(state.GetBestBoardControlMove())

		# Backpropagate
		while node != None: # backpropagate from the expanded node and work back to the root node
			node.Update(state.GetResult(node.playerJustMoved)) # state is terminal. Update node with result from POV of node.playerJustMoved
			node = node.parentNode
		
	# Output some information about the tree - can be omitted
	if verbose and not parallel: print(rootnode.TreeToString(0))
	elif not parallel: print(rootnode.ChildrenToString())

	if bestNode:
		return sorted(rootnode.childNodes, key = lambda c: c.visits)[-1]
	
	if parallel:
		return rootnode
	
	return sorted(rootnode.childNodes, key = lambda c: c.visits)[-1].move # return the move that was most visited
				
"""
Parallelism, Pervasive AF
"""
def mp_worker(data):
	rootstate, itermax, verbose = data
	return UCT(rootstate, itermax, verbose=verbose, parallel=True)
	
def mp_UCT(rootstate, itermax, verbose=False):
	p_c = 4
	p = multiprocessing.Pool(p_c)
	data = []
	
	for i in range(p_c):	
		rs = rootstate.Clone()
		data.append((rs, int(itermax/p_c), verbose))
		
	results = p.map(mp_worker, data)
	
	visits = {}
	
	for rootnode in results:
		for child in rootnode.childNodes:
			m = child.move
			if m in visits:
				visits[m] += child.visits
			else:
				visits[m] = child.visits
	
	s = sorted(visits.items(), key=operator.itemgetter(1))
	if (verbose): print(["{}->{}".format(a[0],a[1]) for a in s])
	p.close()
	p.join()
	return s[-1][0]
				
""" Play a sample game between two UCT players where each player gets a different number 
	of UCT iterations (= simulations = tree nodes).
"""
def UCTPlayGame(player_1, player_2, verbose=True):
	h = HearthstoneGame()
	state = HearthState()
		
	while (state.GetMoves() != []):
		real_player = 1 if state.board[0][h.playerTurnTrackerIndex] == 1 else -1
		
		if sum(h.getValidMoves(state.board, real_player)) == 1 or real_player != state.playerJustMoved:
			m = 239
			state.DoMove(m)
			
		elif real_player == 1:
			if (verbose) : print(state)
			m = player_1(state)
			if (verbose) : print("Best Move: " + str(m) + "\n")
			try:
				state.DoMove(m)
			except:
				state.DoMove(239)
		
		elif real_player == -1:
			if (verbose) : print(state)
			m = player_2(state)
			if (verbose) : print("Best Move: " + str(m) + "\n")
			try:
				state.DoMove(m)
			except:
				state.DoMove(239)
		
	return -1 if state.board[0][h.playerHealthIndex] <= 0 else 1
		

if __name__ == '__main__':
	## need to set up keeping the tree between runs
	direwolf.setup_game()
	print("\nAnd there, but for the grace of god, I go.\n")
	
	h = HearthstoneGame()
	s = HearthState()
	
	passBot = lambda b: 239
	randBot = lambda b: random.choice(b.GetMoves())
	humBot = lambda b: int(input(":: "))
	
	uct10 = lambda b: UCT(rootstate=b, itermax=10, verbose=True)
	lelBot_010 = lambda b: mp_UCT(rootstate=b, itermax=12, verbose=False)
	lelBot_100 = lambda b: mp_UCT(rootstate=b, itermax=100, verbose=False)
	lelBot_800 = lambda b: mp_UCT(rootstate=b, itermax=800, verbose=False)
	lelBot_400 = lambda b: mp_UCT(rootstate=b, itermax=400, verbose=False)
	lelBot_1600 = lambda b: mp_UCT(rootstate=b, itermax=1600, verbose=False)
	lelBot_3200 = lambda b: mp_UCT(rootstate=b, itermax=3200, verbose=False)
	t9000 = lambda b: mp_UCT(rootstate=b, itermax=9000, verbose=False)
	
	valueBot = lambda b: b.GetBestBoardControlMove()
	faceBot = lambda b: b.GetBestFaceMove()
	
	wins = {1:0, -1:0}
	matches = int(sys.argv[1]) if len(sys.argv) > 1 else 3
	
	player_1 = passBot
	player_2 = valueBot
	
	total_time = 0.0
	time_per_game = 0.0
	
	play_orders = {1: (player_1, player_2), -1: (player_2, player_1)}
	
	for m in range(matches):
		print()
		for i in play_orders.keys():
			s = time.time()
			wins[i*UCTPlayGame(play_orders[i][0], play_orders[i][1], verbose=humBot in play_orders[i])] += 1
			total_time += time.time() - s
			time_per_game = total_time / (wins[1] + wins[-1])
		
			print("[ {}:{} - {} games remaining, {} per game ]".format(wins[1], wins[-1], matches*2 - (wins[1]+wins[-1]), time.strftime('%H:%M:%S', time.gmtime(time.time() - s))))
	print()
		
		
	print("\n\n[ {}:{} ( {}% ) ]\n\n".format(wins[1], wins[-1], int((wins[1]/(wins[-1]+wins[1]))*100)))
	print()
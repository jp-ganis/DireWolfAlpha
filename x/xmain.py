from random import choice
import math
from hs.HearthstoneGame import HearthstoneGame, display

from xnode import Node
from xmcts import mcts

def iteration_budget(allowed_iterations):
	def inner_iteration_budget(iterations):
		return iterations < allowed_iterations
	return inner_iteration_budget

def timed_budget(allowed_secs):
	from time import perf_counter
	start_time = None

	def inner_timed_budget(_):
		nonlocal start_time 
		if not start_time:
			start_time = perf_counter()
		if perf_counter() - start_time > allowed_secs:
			start_time = None 
			return False
		else:
			return True
	return inner_timed_budget

def ucb_select(node):
	""" Select the best action, by taking the action that has 
		the best average reward vs the least number of explorations.
		This is based on the UCB1 mechanism for selecting the best action. """
	best_action = (None, 0)
	for action, (action_reward, visits) in node.tried_actions.items():
		ucb1 = (1/math.sqrt(2)) * math.sqrt(math.log(node.visits)/visits)+(action_reward/visits)
		if not best_action[0] or ucb1 > best_action[1]:
			best_action = (action, ucb1)
	return best_action[0]

h = HearthstoneGame()
	
def getPlayer(board):
	return 1 if board[0][h.playerTurnTrackerIndex] == 1 else -1

root = Node(None, None, h.getInitBoard())

while h.getGameEnded(root.state, getPlayer(root.state)) == 0:
	if sum(h.getValidMoves(root.state, getPlayer(root.state))) == 1: 
		a = 239
	elif getPlayer(root.state) == 1:
		display(root.state)
		a = int(input(":: "))
	else:
		display(root.state)
		a = mcts(root.state, iteration_budget(5), 50, select_action=ucb_select, verbose=False)
		print(a)
		
	print('\n\n')
	
	root = root.perform_action(a) 
	
display(root.state)
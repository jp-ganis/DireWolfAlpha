from hs.HearthstoneGame import HearthstoneGame


class Node:
	__slots__ = ['h', 'parent', 'action', 'state', 'is_goal', 'children',
				 'visits', 'utility', 'untried_actions', 'tried_actions']

	def __init__(self, parent, action, state):
		self.h = HearthstoneGame()
		self.parent = parent
		self.action = action
		self.state = state
		self.is_goal = self.h.getGameEnded(self.state, self.pr(self.state)) != 0 
		self.children = dict()
		self.visits = 0  
		self.utility = 0
		self.untried_actions = [a for a in range(self.h.getActionSize()) if self.h.getValidMoves(self.state, self.pr(self.state))[a] == 1]
		self.tried_actions = {} 
	
	def pr(self, state):
		return 1 if state[0][self.h.playerTurnTrackerIndex] else -1

	def simulate_action(self, action, most_probable=False):
		""" Execute the rollout of an action, *without* taking this action out of the list of untried actions.
		   :param action: the action to execute
		   :return: a new node obtained by applying the action in the current node """
		if action in self.children:
			child = self.children[action]
		else:
			state, _ = self.h.getNextState(self.state, self.pr(self.state), action)
			child = Node(self, action, state)
			self.children[action] = child
		return child

	def perform_action(self, action):
		""" Execute the rollout of an action, *with* taking this action out of the list of untried actions.
		   :param action: the action to execute
		   :return: a new node obtained  through action in the current node, and the reward associated with this effect
		   :raises: a ValueError if trying to perform an action that is already tried for this node """
		self.untried_actions.remove(action)
		self.tried_actions[action] = (0, 0) 
		return self.simulate_action(action)

	def rollout_actions(self, rollout_action, depth, horizon):
		""" Organise a rollout from a given node to either a goal node or a leaf node (e.g. by hitting the horizon).
		   :param rollout_action: the heuristic to select the action to use for the rollout
		   :param depth: the current depth at which the rollout is requested
		   :param horizon: the maximum depth to consider
		   :return: a new node obtained  through action in the current node, and the reward associated with this effect
		   :raises: a ValueError if trying to perform an action that is already tried for this node """
		if self.is_goal:
			return self, depth
		elif depth < horizon:
			action = rollout_action(self)
			node = self.simulate_action(action, True) 
			return node.rollout_actions(rollout_action, depth + 1, horizon)
		else:
			return self, depth

	def update(self, discounting):
		""" Traverse back up a branch to collect all rewards and to backpropagate these rewards to successor nodes.
			:param discounting: the discounting factor to use when updating ancestor nodes """
		node = self
		current_reward = 0 
		while node is not None: 
			current_reward *= discounting 
			if node.is_goal:  
				current_reward += self.h.getGameEnded(self.state, 1) 
			if not node.parent or node.action in node.parent.tried_actions:
				if node.parent: 
					utility, visits = node.parent.tried_actions[node.action] 
					node.parent.tried_actions[node.action] = (utility + current_reward, visits + 1)
				node.utility += current_reward
				node.visits += 1
			node = node.parent
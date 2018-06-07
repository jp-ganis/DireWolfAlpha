import logging as log
from random import choice, random
from collections import namedtuple
from xnode import Node

ActInfo = namedtuple('ActInfo', 'action reward visits')


def mcts(root_state, budget, horizon,
		 select_action=lambda node: choice(list(node.tried_actions.keys())),
		 expand_action=lambda node: choice(node.untried_actions),
		 rollout_action=lambda node: node.untried_actions[0],
		 select_best=lambda acts: sorted(acts, key=lambda act: act.reward/act.visits, reverse=True)[0].action,
		 *, discounting=0.9, verbose=False):
	root = Node(None, None, root_state) 
	iterations = 0 

	while budget(iterations): 
		node = root
		depth = 1 
		
		while not node.untried_actions and node.children and depth <= horizon:
			action = select_action(node)
			node = node.simulate_action(action) 
			depth += 1
	
		if node.untried_actions and depth <= horizon and not node.is_goal:
			action = expand_action(node) 
			node = node.perform_action(action)  
			depth += 1

		node, depth = node.rollout_actions(rollout_action, depth, horizon)
		node.update(discounting) 

		iterations += 1
		
	actions = [ActInfo(action, reward, visits) for
			   action, (reward, visits) in root.tried_actions.items()]

	return select_best(actions)

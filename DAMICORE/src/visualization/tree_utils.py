# src/visualization/tree_utils.py

import numpy as np
import networkx as nx

def root_tree(tree, root_node):
    """
    Roots the given tree at the specified node.
    
    Args:
        tree: A NetworkX graph representing the tree.
        root_node: The node to root the tree at.
    
    Returns:
        A new tree graph rooted at the specified node.
    """
    if root_node not in tree:
        raise ValueError("The specified root node is not in the tree.")
    
    rooted_tree = nx.DiGraph()
    rooted_tree.add_node(root_node)
    
    def add_edges(node):
        for neighbor in tree.neighbors(node):
            if neighbor not in rooted_tree:
                rooted_tree.add_node(neighbor)
                rooted_tree.add_edge(node, neighbor)
                add_edges(neighbor)
    
    add_edges(root_node)
    return rooted_tree

def modify_tree(tree, modifications):
    """
    Modifies the tree based on the provided modifications.
    
    Args:
        tree: A NetworkX graph representing the tree.
        modifications: A dictionary containing modifications to apply.
    
    Returns:
        The modified tree.
    """
    for action, params in modifications.items():
        if action == 'add_node':
            tree.add_node(params['node'])
            if 'parent' in params:
                tree.add_edge(params['parent'], params['node'])
        elif action == 'remove_node':
            tree.remove_node(params['node'])
        elif action == 'add_edge':
            tree.add_edge(params['from'], params['to'])
        elif action == 'remove_edge':
            tree.remove_edge(params['from'], params['to'])
    
    return tree

def get_tree_depth(tree, node):
    """
    Computes the depth of the tree from the specified node.
    
    Args:
        tree: A NetworkX graph representing the tree.
        node: The node to compute the depth from.
    
    Returns:
        The depth of the tree from the specified node.
    """
    if node not in tree:
        raise ValueError("The specified node is not in the tree.")
    
    return max(nx.single_source_shortest_path_length(tree, node).values())
import numpy as np
import matplotlib.pyplot as plt
from scipy.cluster.hierarchy import linkage, dendrogram

def create_consensus_tree(trees):
    """
    Create a consensus tree from a list of trees.

    Args:
        trees (list): A list of trees represented as distance matrices.

    Returns:
        consensus_tree: A consensus tree represented as a distance matrix.
    """
    # Assuming trees are represented as distance matrices
    # Here we would implement the logic to create a consensus tree
    # For simplicity, we will average the distance matrices
    avg_tree = np.mean(trees, axis=0)
    return avg_tree

def plot_consensus_tree(consensus_tree, labels):
    """
    Plot the consensus tree.

    Args:
        consensus_tree (np.ndarray): The consensus tree as a distance matrix.
        labels (list): The labels for the leaves of the tree.
    """
    linked = linkage(consensus_tree, 'single')
    plt.figure(figsize=(10, 7))
    dendrogram(linked, labels=labels, orientation='top', leaf_rotation=90)
    plt.title('Consensus Tree')
    plt.xlabel('Samples')
    plt.ylabel('Distance')
    plt.show()
import pandas as pd
import numpy as np
from typing import List
import toytree

class TreeBuilder:
    """Class for building phylogenetic trees from distance matrix"""
    
    def build_trees(self, distance_matrix: pd.DataFrame) -> List[str]:
        """
        Build Newick trees from distance matrix
        
        Args:
            distance_matrix: NCD distance matrix
            
        Returns:
            List of Newick tree strings
        """
        try:
            # Convert matrix to numpy array and ensure it's symmetric
            matrix = distance_matrix.values
            names = distance_matrix.index.tolist()
            
            # Try different toytree API versions
            try:
                # Create initial empty tree with proper Newick format
                base_tree = toytree.tree("();")
                
                # Use UPGMA to build tree from distance matrix
                tree = base_tree.from_distance_matrix(
                    dist_matrix=matrix,
                    names=names,
                    method="upgma"
                )
            except (AttributeError, TypeError) as e:
                # Alternative method if first fails
                tree = toytree.tree.from_distance_matrix(
                    dist_matrix=matrix,
                    names=names,
                    method="upgma"
                )
            
            # Ensure Newick string ends with semicolon
            newick = tree.write(format=9)
            if not newick.endswith(';'):
                newick += ';'
                
            # Return list with single tree for now
            return [newick]
            
        except Exception as e:
            raise RuntimeError(f"Failed to build UPGMA tree: {str(e)}")
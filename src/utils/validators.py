from sklearn.metrics import silhouette_score
import numpy as np

class DAMICOREValidator:
    @staticmethod
    def validate_clusters(data, clusters):
        """
        Validates cluster quality using silhouette score
        
        Returns:
            tuple: (bool, float) - validation result and score
        """
        try:
            score = float(silhouette_score(data, clusters))
            return bool(score > 0.5), score
        except Exception as e:
            raise ValueError(f"Cluster validation failed: {str(e)}")

    @staticmethod
    def validate_communities(communities, min_communities=2):
        """Validates community detection results"""
        n_communities = len(set(communities.values()))
        if n_communities < min_communities:
            raise ValueError(f"Too few communities detected: {n_communities}")
        return True, n_communities

    @staticmethod
    def validate_correlations(corr_matrix, p_values, significance=0.05):
        """Validates correlation significance"""
        significant_correlations = (p_values < significance).sum().sum()
        total_correlations = p_values.size
        ratio = significant_correlations / total_correlations
        return ratio > 0.1, ratio  # at least 10% significant correlations
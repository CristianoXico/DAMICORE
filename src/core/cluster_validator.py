from sklearn.model_selection import KFold
from sklearn.metrics import silhouette_score
import numpy as np

class ClusterValidator:
    def cross_validate_clusters(self, data, n_splits=5):
        """Validação cruzada para clustering"""
        kf = KFold(n_splits=n_splits, shuffle=True)
        scores = []
        
        for train_idx, test_idx in kf.split(data):
            # Treinar no conjunto de treino
            train_clusters = self.cluster_analysis(data[train_idx])
            
            # Predizer para conjunto de teste
            test_clusters = self.predict_clusters(data[test_idx])
            
            # Calcular score
            score = silhouette_score(data[test_idx], test_clusters)
            scores.append(score)
            
        return np.mean(scores), np.std(scores)
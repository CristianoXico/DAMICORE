from joblib import Parallel, delayed
from scipy import stats

class DAMICOREOptimizer:
    @staticmethod
    def parallel_correlation(data, n_jobs=-1):
        """Calculates correlations in parallel"""
        def _process_column(i, data):
            results = []
            for j in range(data.shape[1]):
                correlation, p_value = stats.pearsonr(data[:,i], data[:,j])
                results.append((i, j, correlation, p_value))
            return results
            
        results = Parallel(n_jobs=n_jobs)(
            delayed(_process_column)(i, data) 
            for i in range(data.shape[1])
        )
        return results
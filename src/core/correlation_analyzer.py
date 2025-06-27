import cupy as cp  # GPU acceleration
from scipy.sparse import csr_matrix

class CorrelationAnalyzer:
    def __init__(self, use_gpu=False):
        self.use_gpu = use_gpu
    
    def optimize_correlation_matrix(self, data):
        """Calcula correlações otimizadas para grandes matrizes"""
        if self.use_gpu:
            # Use GPU se disponível
            data_gpu = cp.asarray(data)
            corr_matrix = cp.corrcoef(data_gpu.T)
            return cp.asnumpy(corr_matrix)
        else:
            # Usar matriz esparsa para dados grandes
            sparse_data = csr_matrix(data)
            return self._sparse_correlation(sparse_data)
import pandas as pd
import numpy as np
from typing import Union
import zlib

class NCDCalculator:
    """Calculate Normalized Compression Distance matrix"""
    
    def calculate_matrix(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate NCD matrix from input data
        
        Args:
            data: Input DataFrame with samples to compare
            
        Returns:
            DataFrame with NCD matrix
        """
        # Convert data to string representation
        strings = data.apply(lambda x: ' '.join(x.astype(str)), axis=1)
        
        # Get number of samples
        n_samples = len(strings)
        
        # Initialize distance matrix
        distances = np.zeros((n_samples, n_samples))
        
        # Calculate NCD for each pair
        for i in range(n_samples):
            for j in range(i, n_samples):
                # Get compressed lengths
                x = strings.iloc[i]
                y = strings.iloc[j]
                
                cx = len(zlib.compress(x.encode()))
                cy = len(zlib.compress(y.encode()))
                cxy = len(zlib.compress((x + y).encode()))
                
                # Calculate NCD
                ncd = (cxy - min(cx, cy)) / max(cx, cy)
                
                # Store in matrix (symmetric)
                distances[i,j] = distances[j,i] = ncd
                
        # Create DataFrame with sample indices
        return pd.DataFrame(
            distances,
            index=data.index,
            columns=data.index
        )
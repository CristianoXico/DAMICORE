import pandas as pd
from typing import Union

class DataProcessor:
    """Class for preprocessing data before DAMICORE analysis"""
    
    def preprocess(self, data: Union[pd.DataFrame, pd.Series]) -> pd.DataFrame:
        """
        Preprocess data for DAMICORE analysis
        
        Args:
            data: Input data as DataFrame or Series
            
        Returns:
            Preprocessed DataFrame
        """
        if isinstance(data, pd.Series):
            data = data.to_frame()
            
        # Create a copy and convert all to strings first
        processed = data.astype(str).copy()
        
        # Remove missing values
        processed = processed.replace('nan', pd.NA).dropna()
        
        return processed
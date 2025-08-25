#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
DAMICORE Pareto Analysis Script

This script performs Pareto frontier analysis on a dataset with array-formatted data.
It first preprocesses the data using mode extraction before performing Pareto analysis.
"""

import os
import sys
import pandas as pd
import numpy as np
import ast
from statistics import multimode
from datetime import datetime
from collections import Counter, defaultdict
from typing import List, Dict, Tuple, Optional, Union, Any
from dataclasses import dataclass

def load_data(file_path: str) -> pd.DataFrame:
    """
    Loads a CSV file and returns a pandas DataFrame.
    
    Args:
        file_path: Path to the CSV file
        
    Returns:
        pd.DataFrame: Loaded data
    """
    try:
        df = pd.read_csv(file_path)
        print(f"Successfully loaded {len(df)} rows from {file_path}")
        return df
    except Exception as e:
        print(f"Error loading file: {e}")
        return None

def extract_value(cell):
    """
    Converts cell content to a single numeric value. Uses mode if multiple elements exist.
    
    Args:
        cell: The cell content to process (can be string, list, set, or tuple)
        
    Returns:
        A single numeric value or pd.NA if no valid value found
    """
    try:
        val = ast.literal_eval(str(cell))
    except (ValueError, SyntaxError):
        return pd.NA
        
    if isinstance(val, (set, list, tuple)):
        vals = list(val)
    else:
        vals = [val]
        
    # Remove empty strings and None values
    vals = [v for v in vals if v not in ('', None)]
    
    if not vals:
        return pd.NA
        
    # If multiple values, use the mode (most common value)
    if len(vals) > 1:
        try:
            chosen = multimode(vals)[0]
        except:
            chosen = vals[0]  # Fallback to first value if mode fails
    else:
        chosen = vals[0]
    
    # Try to convert to int or float
    try:
        return int(chosen)
    except (ValueError, TypeError):
        try:
            return float(chosen)
        except (ValueError, TypeError):
            return chosen

def is_pareto_efficient(points: np.ndarray, objectives: List[str]) -> np.ndarray:
    """
    Find the Pareto-efficient points.
    
    Args:
        points: An (n_points, n_objectives) array
        objectives: List of objectives (e.g., ['min', 'max'] for each column in points)
        
    Returns:
        A boolean mask of Pareto-efficient points
    """
    n_points = points.shape[0]
    is_efficient = np.ones(n_points, dtype=bool)
    
    for i in range(n_points):
        if is_efficient[i]:
            # Compare against all other points
            for j in range(n_points):
                if i == j:
                    continue
                    
                # Check if point j dominates point i
                dominates = True
                for k, obj in enumerate(objectives):
                    if obj == 'max':
                        if points[j, k] < points[i, k]:
                            dominates = False
                            break
                    else:  # minimization
                        if points[j, k] > points[i, k]:
                            dominates = False
                            break
                
                if dominates:
                    is_efficient[i] = False
                    break
    
    return is_efficient

def preprocess_dataframe(df):
    """
    Preprocess the dataframe by applying extract_value to all columns.
    
    Args:
        df: Input DataFrame with array-formatted data
        
    Returns:
        Processed DataFrame with extracted values
    """
    print("\nPreprocessing array-formatted data (this may take a while for large datasets)...")
    
    # Create a copy to avoid modifying the original
    processed_df = df.copy()
    
    # Apply extract_value to each cell in the dataframe
    for col in processed_df.columns:
        if processed_df[col].dtype == object:  # Only process object/string columns
            processed_df[col] = processed_df[col].apply(extract_value)
    
    # Convert columns to numeric where possible
    for col in processed_df.select_dtypes(include=['object']).columns:
        try:
            processed_df[col] = pd.to_numeric(processed_df[col], errors='ignore')
        except:
            pass
    
    return processed_df

def run_pareto_analysis(df: pd.DataFrame, output_dir: str) -> Optional[pd.DataFrame]:
    """
    Run Pareto frontier analysis on the dataset after preprocessing array-formatted data.
    
    Args:
        df: Input DataFrame with array-formatted data
        output_dir: Directory to save results
        
    Returns:
        DataFrame with Pareto-optimal points, or None if an error occurs
    """
    print("\n=== Pareto Frontier Analysis ===")
    
    try:
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Preprocess the data to extract values from arrays
        print("\nPreprocessing data (this may take a while for large datasets)...")
        processed_df = preprocess_dataframe(df)
        
        # Get list of numeric columns after preprocessing
        numeric_cols = processed_df.select_dtypes(include=[np.number]).columns.tolist()
        
        if not numeric_cols:
            print("Error: No numeric columns found after preprocessing the data.")
            return None
            
        print(f"\nFound {len(numeric_cols)} numeric columns after preprocessing:")
        for i, col in enumerate(numeric_cols, 1):
            # Show sample values for the first few columns
            sample_values = processed_df[col].dropna().head(3).tolist()
            print(f"{i}. {col} (Sample: {sample_values})")
        
        # Let user select variables for analysis
        print("\nSelect variables for Pareto analysis (comma-separated indices, e.g., 1,2,3):")
        selected = input("Variable indices: ").strip().split(',')
        
        try:
            selected_indices = [int(idx.strip()) - 1 for idx in selected if idx.strip().isdigit()]
            selected_cols = [numeric_cols[i] for i in selected_indices if i < len(numeric_cols)]
        except (ValueError, IndexError) as e:
            print(f"Error in selection: {e}")
            return None
        
        if not selected_cols:
            print("No valid variables selected. Exiting.")
            return None
        
        print(f"\nSelected variables: {', '.join(selected_cols)}")
        
        # Get optimization direction for each variable
        objectives = []
        for col in selected_cols:
            while True:
                direction = input(f"Optimize {col} (min/max): ").strip().lower()
                if direction in ['min', 'max']:
                    objectives.append(direction)
                    break
                print("Please enter 'min' or 'max'")
        
        # Prepare data for Pareto analysis
        data = processed_df[selected_cols].copy()
        
        # Remove rows with any missing values in the selected columns
        data = data.dropna()
        
        if len(data) == 0:
            print("Error: No valid data points after preprocessing and removing missing values.")
            return None
        
        # Convert all columns to numeric (in case any were missed earlier)
        for col in data.columns:
            data[col] = pd.to_numeric(data[col], errors='coerce')
        
        # Remove any rows that couldn't be converted to numeric
        data = data.dropna()
        
        if len(data) == 0:
            print("Error: No valid numeric data found in the selected columns after preprocessing.")
            return None
        
        print(f"\nAnalyzing {len(data)} data points...")
        
        # Normalize data (0-1) for fair comparison
        normalized_data = data.copy()
        for i, col in enumerate(selected_cols):
            col_data = normalized_data[col]
            min_val = col_data.min()
            max_val = col_data.max()
            
            # Handle case where all values are the same
            if max_val == min_val:
                normalized_data[col] = 0.5  # Assign middle value
            else:
                if objectives[i] == 'min':
                    normalized_data[col] = (col_data - min_val) / (max_val - min_val + 1e-10)
                else:  # max
                    normalized_data[col] = (max_val - col_data) / (max_val - min_val + 1e-10)
        
        # Debug: Show summary of selected data
        print("\n=== Data Summary ===")
        print("Selected variables and their statistics:")
        for col in selected_cols:
            print(f"\n{col} (to {objectives[selected_cols.index(col)]}imize):")
            print(data[col].describe())
            print(f"Unique values: {data[col].nunique()}")
            print(f"Missing values: {data[col].isna().sum()}")
        
        # Check for constant columns
        constant_cols = [col for col in selected_cols if data[col].nunique() <= 1]
        if constant_cols:
            print("\nWARNING: The following columns have no variation (constant values):")
            for col in constant_cols:
                print(f"- {col}: {data[col].iloc[0]}")
            print("These columns should be removed as they don't contribute to the analysis.")
        
        # Check for columns with mostly missing values
        missing_ratio = data[selected_cols].isna().mean()
        high_missing = missing_ratio[missing_ratio > 0.5]  # More than 50% missing
        if not high_missing.empty:
            print("\nWARNING: The following columns have more than 50% missing values:")
            for col, ratio in high_missing.items():
                print(f"- {col}: {ratio:.1%} missing")
        
        # Drop rows with any missing values in selected columns
        clean_data = data[selected_cols].dropna()
        if len(clean_data) < len(data):
            print(f"\nDropped {len(data) - len(clean_data)} rows with missing values.")
        
        if len(clean_data) == 0:
            print("\nERROR: No valid data points remain after removing rows with missing values.")
            return None
            
        # Convert to numpy array for efficient comparison
        data_array = clean_data.values
        
        print("\n=== Running Pareto Analysis ===")
        print(f"Analyzing {len(clean_data)} data points with {len(selected_cols)} variables...")
        
        # Identify Pareto-optimal points
        is_pareto = is_pareto_efficient(data_array, objectives)
        pareto_points = clean_data[is_pareto].copy()
        
        # Add back the original index for reference
        pareto_points = data.loc[clean_data.index[is_pareto]].copy()
        
        # Add a column indicating these are Pareto-optimal
        pareto_points['is_pareto_optimal'] = True
        
        # Debug: Print shape and columns of the data
        print("\n=== Debug Information ===")
        print(f"Shape of input data: {data.shape}")
        print(f"Shape of Pareto points: {pareto_points.shape}")
        print(f"Selected columns: {selected_cols}")
        print(f"Objectives: {objectives}")
        print(f"Number of Pareto points: {len(pareto_points)}")
        
        if len(pareto_points) == 0:
            print("\nWARNING: No Pareto-optimal points were found!")
            print("This could be due to:")
            print("1. All points being dominated by at least one other point")
            print("2. Issues with the input data (e.g., all values are the same)")
            print("3. The selected variables not having meaningful variation")
            print("\nPlease check your input data and try different variables.")
            return None
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = os.path.join(output_dir, f"pareto_results_{timestamp}.csv")
        
        try:
            # Save to CSV
            pareto_points.to_csv(output_file, index=False)
            
            # Verify the file was created and has content
            if not os.path.exists(output_file):
                print(f"\nERROR: Failed to create output file: {output_file}")
                return None
                
            file_size = os.path.getsize(output_file)
            if file_size == 0:
                print(f"\nWARNING: Output file was created but is empty: {output_file}")
                print("This suggests there might be no data to write after filtering.")
            else:
                print(f"\nPareto analysis completed. Results saved to: {output_file}")
                print(f"File size: {file_size} bytes")
                
            return pareto_points
            
        except Exception as e:
            print(f"\nERROR: Failed to save results to {output_file}")
            print(f"Error: {str(e)}")
            return None
    
    except Exception as e:
        print(f"\nError during Pareto analysis: {e}")
        import traceback
        traceback.print_exc()
        return None

def main():
    """
    Main function to run the Pareto analysis.
    """
    try:
        # Get input file path
        print("=== DAMICORE Pareto Analysis Tool ===\n")
        file_path = input("Enter the full path to the CSV file: ").strip('"')
        
        # Validate file exists
        if not os.path.isfile(file_path):
            print(f"Error: File not found: {file_path}")
            return
        
        print(f"\nLoading data from {file_path}...")
        df = load_data(file_path)
        if df is None or df.empty:
            print("Error: Failed to load data or file is empty.")
            return
        
        print(f"\nData loaded successfully with {len(df)} rows and {len(df.columns)} columns.")
        
        # Create output directory
        output_dir = os.path.join(os.path.dirname(os.path.abspath(file_path)), "pareto_results")
        os.makedirs(output_dir, exist_ok=True)
        print(f"\nResults will be saved to: {output_dir}")
        
        # Run Pareto analysis
        print("\nStarting Pareto analysis...")
        result = run_pareto_analysis(df, output_dir)
        
        if result is not None:
            print("\n=== Analysis completed successfully! ===")
        else:
            print("\n=== Analysis completed with errors. See above for details. ===")
    
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user.")
    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

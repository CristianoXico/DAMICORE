import pandas as pd
import os
import numpy as np
from pathlib import Path
from tqdm import tqdm

def create_sample(file_path: str, output_dir: str = 'data', sample_percentage: float = 0.1):
    """
    Creates a stratified sample of the data with memory optimization
    
    Args:
        file_path: Path to CSV file
        output_dir: Directory to save sample (default 'data')
        sample_percentage: Percentage of data to sample (default 10%)
    Returns:
        Path to created sample file
    """
    # Validate input file exists
    input_path = Path(file_path)
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {file_path}")

    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Define sample file path
    sample_file = output_path / "sample_dengue.csv"
    
    # Read CSV in chunks to manage memory
    chunk_size = 1000
    total_rows = sum(1 for _ in pd.read_csv(file_path, chunksize=chunk_size))
    total_rows *= chunk_size
    
    # Calculate sample size
    sample_size = int(total_rows * sample_percentage)
    print(f"Total rows: {total_rows:,}")
    print(f"Target sample size: {sample_size:,} ({sample_percentage*100}%)")
    
    # Initialize random number generator
    rng = np.random.default_rng(42)
    
    # Sample rows with probability
    print("\nProcessing chunks...")
    with open(sample_file, 'w', encoding='utf-8', newline='') as f:
        header_written = False
        rows_sampled = 0
        
        for chunk in tqdm(pd.read_csv(file_path, chunksize=chunk_size)):
            if not header_written:
                chunk.head(0).to_csv(f, index=False)
                header_written = True
            
            # Calculate how many rows we need from this chunk
            remaining_needed = sample_size - rows_sampled
            chunk_sample_size = min(
                int(len(chunk) * sample_percentage),
                remaining_needed
            )
            
            if chunk_sample_size > 0:
                # Sample from chunk
                chunk_sample = chunk.sample(
                    n=chunk_sample_size,
                    random_state=rng
                )
                chunk_sample.to_csv(f, header=False, index=False)
                rows_sampled += len(chunk_sample)
            
            if rows_sampled >= sample_size:
                break
    
    print(f"\nSample saved to: {sample_file}")
    print(f"Actual sample size: {rows_sampled:,} rows")
    
    return str(sample_file.absolute())

if __name__ == "__main__":
    # File paths
    input_file = r"C:\Users\55179\Desktop\Workspace_vscode\Analise_Dados\PPPP-Arbovirose\entrega\group_by_censitario_quarter.csv"
    output_dir = r"C:\Users\55179\Desktop\Workspace_vscode\DAMICORE\data"
    
    # Create 10% sample
    sample_path = create_sample(
        file_path=input_file,
        output_dir=output_dir,
        sample_percentage=0.1
    )
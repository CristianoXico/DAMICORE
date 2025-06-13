import numpy as np
from scipy.spatial.distance import pdist, squareform
import zlib
import pandas as pd
from joblib import Parallel, delayed
from tqdm import tqdm
from functools import lru_cache
import time
from dataclasses import dataclass
from typing import Dict, Any, List, Tuple
import multiprocessing
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import mmap

@dataclass
class ProcessingStats:
    total_time: float
    conversion_time: float
    matrix_calc_time: float
    matrix_size: tuple
    compression_ratio: float
    chunk_size: int

class NCDProcessor:
    def __init__(self, chunk_size=1000, n_jobs=None, verbose=True):
        self.chunk_size = chunk_size
        self.n_jobs = n_jobs or multiprocessing.cpu_count()
        self.verbose = verbose
        self.stats = None
        self._compression_cache = {}

    @lru_cache(maxsize=10000)
    def _compress_string(self, s: str) -> int:
        """Cached compression"""
        return len(zlib.compress(s.encode()))

    def _process_chunk(self, chunk_data: List[str], start_idx: int) -> Tuple[np.ndarray, int]:
        """Process a chunk of the distance matrix"""
        chunk_size = len(chunk_data)
        chunk_matrix = np.zeros((chunk_size, self.matrix_size))
        
        # Pre-calculate compressions for the chunk
        chunk_compressions = {
            i: self._compress_string(s) 
            for i, s in enumerate(chunk_data, start_idx)
        }
        
        # Calculate NCD for the chunk
        for i, x in enumerate(chunk_data):
            row_idx = start_idx + i
            x_compressed = chunk_compressions[row_idx]
            
            # Use vectorized operations where possible
            for j in range(row_idx + 1, self.matrix_size):
                if j not in self._compression_cache:
                    self._compression_cache[j] = self._compress_string(self.all_data[j])
                y_compressed = self._compression_cache[j]
                
                # Calculate combined compression
                xy_compressed = self._compress_string(x + self.all_data[j])
                
                # Calculate NCD
                ncd = (xy_compressed - min(x_compressed, y_compressed)) / max(x_compressed, y_compressed)
                chunk_matrix[i, j] = ncd
        
        return chunk_matrix, start_idx

    def process_dataframe(self, df: pd.DataFrame) -> Tuple[np.ndarray, List[str]]:
        """Process DataFrame with optimized NCD calculation"""
        start_time = time.time()
        
        # Validate input
        if df.empty:
            raise ValueError("Empty DataFrame provided")
        
        # Convert data to strings efficiently
        conv_start = time.time()
        self.labels = df.columns.tolist()
        
        # Optimize string conversion
        with ThreadPoolExecutor(max_workers=self.n_jobs) as executor:
            futures = []
            for col in df.columns:
                futures.append(executor.submit(lambda x: x.astype(str), df[col]))
            string_cols = [f.result() for f in futures]
        
        self.all_data = [','.join(row) for row in zip(*string_cols)]
        self.matrix_size = len(self.all_data)
        conversion_time = time.time() - conv_start
        
        # Calculate distance matrix in parallel chunks
        matrix_start = time.time()
        self.matrix = np.zeros((self.matrix_size, self.matrix_size))
        
        # Process chunks in parallel
        chunks = [
            (self.all_data[i:i + self.chunk_size], i)
            for i in range(0, self.matrix_size, self.chunk_size)
        ]
        
        with ProcessPoolExecutor(max_workers=self.n_jobs) as executor:
            futures = []
            for chunk_data, start_idx in chunks:
                futures.append(executor.submit(self._process_chunk, chunk_data, start_idx))
            
            # Process results as they complete
            for future in tqdm(futures, desc="Processing chunks", disable=not self.verbose):
                chunk_matrix, start_idx = future.result()
                self.matrix[start_idx:start_idx + len(chunk_matrix)] = chunk_matrix
        
        # Mirror the matrix
        self.matrix = self.matrix + self.matrix.T
        
        matrix_time = time.time() - matrix_start
        
        # Update stats
        self.stats = ProcessingStats(
            total_time=time.time() - start_time,
            conversion_time=conversion_time,
            matrix_calc_time=matrix_time,
            matrix_size=(self.matrix_size, self.matrix_size),
            compression_ratio=self._calculate_compression_ratio(),
            chunk_size=self.chunk_size
        )
        
        return self.matrix, self.labels

    def _calculate_compression_ratio(self) -> float:
        """Calculate average compression ratio"""
        if not self.all_data:
            return 0.0
        sample_size = min(1000, len(self.all_data))
        samples = np.random.choice(self.all_data, sample_size)
        original_size = sum(len(s.encode()) for s in samples)
        compressed_size = sum(len(zlib.compress(s.encode())) for s in samples)
        return compressed_size / original_size

def main(input_file):
    if not os.path.isfile(input_file):
        print(f"Arquivo não encontrado: {input_file}")
        return

    # Carrega apenas as primeiras 100 linhas para teste
    df = pd.read_csv(input_file, sep=';', nrows=100)
    processor = NCDProcessor()
    matrix, labels = processor.process_dataframe(df)

    # Salvar matriz em um arquivo CSV
    output_file = os.path.splitext(input_file)[0] + '_ncd_matrix_test.csv'
    np.savetxt(output_file, matrix, delimiter=';', fmt='%.6f', header=';' + ';'.join(labels), comments='')
    print(f"Matriz de distância NCD salva em: {output_file}")

if __name__ == "__main__":
    if len(sys.argv) < 3 or sys.argv[1] != "--input":
        print("Uso: python main.py --input <caminho_para_o_arquivo_csv>")
    else:
        input_path = sys.argv[2]
        main(input_path)
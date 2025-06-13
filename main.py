import pandas as pd
import numpy as np
from src.core.ncd_processor import NCDProcessor
from src.core.community_detector import NewmanCommunityDetector
import networkx as nx
from tqdm import tqdm
import multiprocessing
from pathlib import Path
import argparse
from typing import Dict, Any, Tuple
import psutil

def get_file_category(file_path: str) -> Tuple[str, int]:
    """
    Determina a categoria do arquivo e chunk_size recomendado
    
    Categorias:
    - Pequeno: < 100MB
    - Médio: 100MB - 1GB
    - Grande: 1GB - 10GB
    - Muito Grande: > 10GB
    
    Args:
        file_path: Caminho do arquivo
    Returns:
        Tuple[categoria, chunk_size]
    """
    file_size = Path(file_path).stat().st_size
    available_memory = psutil.virtual_memory().available
    
    # Tamanhos em bytes
    SIZE_100MB = 100 * 1024 * 1024
    SIZE_1GB = 1024 * 1024 * 1024
    SIZE_10GB = 10 * SIZE_1GB
    
    if file_size < SIZE_100MB:
        return "pequeno", 500
    elif file_size < SIZE_1GB:
        return "médio", 1000
    elif file_size < SIZE_10GB:
        return "grande", 2000
    else:
        return "muito grande", 5000

def run_damicore(input_file: str, chunk_size: int = None, output_dir: str = 'results') -> Dict[str, Any]:
    """
    Executa o pipeline DAMICORE com otimizações para arquivos grandes
    
    Args:
        input_file: Caminho para o arquivo CSV
        chunk_size: Tamanho do chunk para processamento paralelo
        output_dir: Diretório para salvar resultados
    
    Returns:
        Dict com resultados e estatísticas
    """
    # Analisa tamanho do arquivo
    category, recommended_chunk = get_file_category(input_file)
    chunk_size = chunk_size or recommended_chunk
    
    print(f"\nAnálise do arquivo:")
    print(f"- Categoria: {category}")
    print(f"- Chunk size: {chunk_size}")
    
    # Criar diretório de saída
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    print("\n1. Carregando dados...")
    # Usar dtypes otimizados e chunks para arquivos grandes
    df = pd.read_csv(input_file, 
                     dtype_backend='pyarrow',
                     low_memory=True)
    
    print(f"Dados carregados: {df.shape[0]:,} linhas x {df.shape[1]:,} colunas")
    
    # Inicializa processador NCD otimizado
    print("\n2. Calculando matriz NCD...")
    ncd = NCDProcessor(
        chunk_size=chunk_size,
        n_jobs=multiprocessing.cpu_count(),
        verbose=True
    )
    
    # Processa dados em paralelo
    distance_matrix, labels = ncd.process_dataframe(df)
    
    # Salva matriz NCD com timestamp
    timestamp = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
    output_ncd = output_path / f"ncd_matrix_{timestamp}.npy"
    np.save(output_ncd, distance_matrix)
    print(f"Matriz NCD salva em: {output_ncd}")
    
    # Detecção de comunidades
    print("\n3. Detectando comunidades...")
    detector = NewmanCommunityDetector()
    communities = detector.detect_communities(distance_matrix)
    
    # Análise das comunidades
    print("\n4. Analisando resultados...")
    metrics = detector.get_metrics()
    
    print(f"\nEstatísticas:")
    print(f"- Número de comunidades: {metrics['n_communities']}")
    print(f"- Modularidade: {metrics['modularity']:.4f}")
    print(f"- Clustering médio: {metrics['avg_clustering']:.4f}")
    print(f"- Densidade do grafo: {metrics['density']:.4f}")
    
    return {
        'distance_matrix': distance_matrix,
        'communities': communities,
        'labels': labels,
        'metrics': metrics
    }

def main():
    parser = argparse.ArgumentParser(description='DAMICORE Pipeline para arquivos grandes')
    parser.add_argument('input', help='Caminho para o arquivo CSV de entrada')
    parser.add_argument('--chunk-size', type=int, default=1000, 
                      help='Tamanho do chunk para processamento')
    parser.add_argument('--output-dir', default='results',
                      help='Diretório para salvar resultados')
    
    args = parser.parse_args()
    return run_damicore(args.input, args.chunk_size, args.output_dir)

if __name__ == "__main__":
    exit(main())
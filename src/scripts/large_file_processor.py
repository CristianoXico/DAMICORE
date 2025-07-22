"""
Processador de arquivos grandes sem pandas para evitar estouro de memória
"""

import csv
import random
import sys
from collections import defaultdict

# Aumenta o limite de campo do CSV para lidar com arquivos muito grandes
csv.field_size_limit(sys.maxsize)

def process_large_file_without_pandas(file_path, chunk_size):
    """
    Processa arquivo CSV muito grande linha por linha, sem usar pandas
    para evitar estouro de memória
    """
    print(f"🔥 Processando arquivo linha-a-linha: {file_path}")
    
    chunks = []
    current_chunk = []
    headers = None
    line_count = 0
    
    with open(file_path, 'r', encoding='utf-8') as file:
        csv_reader = csv.reader(file)
        
        # Lê cabeçalho
        headers = next(csv_reader)
        print(f"📋 Cabeçalho lido: {len(headers)} colunas")
        
        for row in csv_reader:
            # Garante que a linha tenha o mesmo número de colunas do cabeçalho
            if len(row) != len(headers):
                row = row + [''] * (len(headers) - len(row))  # Preenche com strings vazias
                row = row[:len(headers)]  # Trunca se for maior
            
            current_chunk.append(row)
            line_count += 1
            
            # Quando o chunk está cheio, cria um "DataFrame" simulado
            if len(current_chunk) >= chunk_size:
                # Converte para formato similar ao pandas DataFrame
                chunk_dict = {}
                for i, header in enumerate(headers):
                    chunk_dict[str(i)] = [row[i] if i < len(row) else '' for row in current_chunk]
                
                # Cria objeto simulando pandas DataFrame
                class MockDataFrame:
                    def __init__(self, data, headers):
                        self.data = data
                        self.headers = headers
                        self.columns = list(data.keys())
                        self.shape = (len(current_chunk), len(headers))
                    
                    def __getitem__(self, key):
                        return self.data[key]
                    
                    def sample(self, n, replace=True, random_state=None):
                        if random_state is not None:
                            random.seed(random_state)
                        
                        # Amostragem bootstrap
                        indices = [random.randint(0, len(self.data[self.columns[0]])-1) for _ in range(n)]
                        
                        sampled_data = {}
                        for col in self.columns:
                            sampled_data[col] = [self.data[col][i] for i in indices]
                        
                        return MockDataFrame(sampled_data, self.headers)
                    
                    def copy(self):
                        return MockDataFrame(self.data.copy(), self.headers)
                    
                    def map(self, func):
                        # Aplica função a todos os valores
                        new_data = {}
                        for col in self.columns:
                            new_data[col] = [func(val) for val in self.data[col]]
                        return MockDataFrame(new_data, self.headers)
                
                mock_df = MockDataFrame(chunk_dict, headers)
                chunks.append(mock_df)
                
                print(f"📦 Chunk criado: {len(current_chunk)} linhas, {len(headers)} colunas")
                current_chunk = []
                
                # Libera memória
                import gc
                gc.collect()
    
    # Processa último chunk se houver dados restantes
    if current_chunk:
        chunk_dict = {}
        for i, header in enumerate(headers):
            chunk_dict[str(i)] = [row[i] if i < len(row) else '' for row in current_chunk]
        
        mock_df = MockDataFrame(chunk_dict, headers)
        chunks.append(mock_df)
        print(f"📦 Último chunk criado: {len(current_chunk)} linhas, {len(headers)} colunas")
    
    print(f"✅ Processamento concluído: {line_count} linhas em {len(chunks)} chunks")
    
    # Retorna iterador que simula o comportamento do pandas
    return iter(chunks)

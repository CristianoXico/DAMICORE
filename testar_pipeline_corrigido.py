import pandas as pd
import numpy as np
import os
import sys
import logging
import zlib
from typing import List, Dict, Any, Tuple
from pipeline_novo import visualize_consensus_trees, configurar_logging

# Configura logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def calcular_ncd_entre_textos(textos: List[str], rotulos: List[str] = None) -> Tuple[np.ndarray, List[str]]:
    """
    Calcula a matriz NCD entre uma lista de textos.
    
    Args:
        textos: Lista de strings contendo os textos a serem comparados
        rotulos: Lista de rótulos para os textos (opcional)
        
    Returns:
        Tupla (matriz_ncd, rotulos)
    """
    n = len(textos)
    if n < 2:
        raise ValueError("Pelo menos 2 textos são necessários para calcular a matriz NCD")
    
    # Se não houver rótulos, cria uns genéricos
    if rotulos is None:
        rotulos = [f"doc_{i+1}" for i in range(n)]
    elif len(rotulos) != n:
        raise ValueError("O número de rótulos deve ser igual ao número de textos")
    
    # Inicializa a matriz NCD
    ncd_mat = np.zeros((n, n))
    
    # Função para calcular tamanho comprimido
    def compressed_size(s: str) -> int:
        return len(zlib.compress(s.encode('utf-8')))
    
    # Pré-calcula os tamanhos comprimidos
    logger.info("Calculando tamanhos comprimidos...")
    sizes = [compressed_size(t) for t in textos]
    
    # Preenche a matriz
    logger.info("Calculando distâncias NCD...")
    for i in range(n):
        for j in range(i, n):  # Apenas metade superior + diagonal
            if i == j:
                ncd_mat[i, j] = 0.0  # Diagonal principal é zero
            else:
                try:
                    # Tamanho da concatenação
                    c_xy = compressed_size(textos[i] + textos[j])
                    c_x = sizes[i]
                    c_y = sizes[j]
                    
                    # Calcula NCD normalizado
                    if c_x == 0 or c_y == 0:
                        ncd = 1.0  # Máxima distância se um dos tamanhos for zero
                    else:
                        ncd = (c_xy - min(c_x, c_y)) / max(c_x, c_y)
                        ncd = max(0.0, min(1.0, ncd))  # Garante entre 0 e 1
                    
                    ncd_mat[i, j] = ncd
                    ncd_mat[j, i] = ncd  # Mantém a simetria
                    
                except Exception as e:
                    logger.error(f"Erro ao calcular NCD entre {i} e {j}: {e}")
                    ncd = 1.0  # Máxima distância em caso de erro
                    ncd_mat[i, j] = ncd
                    ncd_mat[j, i] = ncd
    
    return ncd_mat, rotulos

def processar_documentos(arquivo_csv: str, coluna_texto: str = 'texto', coluna_id: str = 'documento') -> Tuple[np.ndarray, List[str]]:
    """
    Processa um arquivo CSV contendo documentos para gerar uma matriz NCD.
    
    Args:
        arquivo_csv: Caminho para o arquivo CSV
        coluna_texto: Nome da coluna que contém o texto dos documentos
        coluna_id: Nome da coluna que contém os IDs dos documentos
        
    Returns:
        Tupla (matriz_ncd, rotulos)
    """
    try:
        logger.info(f"Carregando arquivo: {arquivo_csv}")
        df = pd.read_csv(arquivo_csv)
        
        # Verifica se as colunas necessárias existem
        if coluna_texto not in df.columns:
            raise ValueError(f"A coluna '{coluna_texto}' não foi encontrada no arquivo.")
        
        # Usa a coluna de ID se existir, senão usa o índice
        if coluna_id in df.columns:
            rotulos = df[coluna_id].astype(str).tolist()
        else:
            rotulos = [f"doc_{i+1}" for i in range(len(df))]
        
        # Extrai os textos
        textos = df[coluna_texto].astype(str).tolist()
        
        logger.info(f"Processando {len(textos)} documentos...")
        logger.info(f"Exemplo de rótulos: {rotulos[:3]}...")
        logger.info(f"Exemplo de textos: {[t[:50] + '...' for t in textos[:1]]}...")
        
        # Calcula a matriz NCD diretamente
        logger.info("Iniciando cálculo da matriz NCD...")
        matriz_ncd, rotulos_ncd = calcular_ncd_entre_textos(textos, rotulos)
        
        logger.info(f"Matriz NCD gerada com sucesso! Dimensões: {matriz_ncd.shape}")
        logger.info(f"Rótulos: {rotulos_ncd[:5]}..." if len(rotulos_ncd) > 5 else f"Rótulos: {rotulos_ncd}")
        
        # Exibe uma prévia da matriz
        if len(matriz_ncd) <= 10:
            logger.info("\nPrévia da matriz NCD (diagonal superior):")
            for i in range(min(5, len(matriz_ncd))):
                logger.info(f"{rotulos_ncd[i]}: {matriz_ncd[i, :5].round(3)}...")
        
        return matriz_ncd, rotulos_ncd
        
    except Exception as e:
        logger.error(f"Erro ao processar documentos: {str(e)}", exc_info=True)
        raise

def main():
    """Função principal para testar o pipeline."""
    try:
        # Configura o logging
        configurar_logging()
        
        logger.info("=" * 60)
        logger.info("INICIANDO PROCESSAMENTO DO PIPELINE")
        logger.info("=" * 60)
        
        # 1. Processar documentos e calcular matriz NCD
        logger.info("\n[1/3] Processando documentos e calculando matriz NCD...")
        arquivo_csv = "test_data/portugues/dados_portugues.csv"
        
        if not os.path.exists(arquivo_csv):
            logger.error(f"Arquivo não encontrado: {arquivo_csv}")
            logger.error("Certifique-se de que o arquivo existe ou forneça um caminho válido.")
            return
            
        matriz_ncd, rotulos = processar_documentos(arquivo_csv)
        
        # Verifica se a matriz NCD foi gerada corretamente
        if matriz_ncd is None or len(rotulos) == 0:
            logger.error("Falha ao gerar a matriz NCD. Verifique os dados de entrada.")
            return
            
        logger.info(f"Matriz NCD gerada com sucesso! Dimensões: {matriz_ncd.shape}")
        logger.info(f"Exemplo de rótulos: {rotulos[:3]}...")
        
        # 2. Gerar visualização da árvore de consenso
        logger.info("\n[2/3] Gerando visualização da árvore de consenso...")
        
        # Cria o diretório de saída se não existir
        output_dir = 'output/consenso_corrigido'
        os.makedirs(output_dir, exist_ok=True)
        
        # Chama a função de visualização
        logger.info("Chamando visualize_consensus_trees...")
        try:
            resultados = visualize_consensus_trees(
                ncd_mat=matriz_ncd,  # Passa a matriz NCD
                labels=rotulos  # Passa os rótulos dos documentos
            )
            
            if resultados and 'arquivos_gerados' in resultados:
                logger.info("\n✅ Visualizações geradas com sucesso!")
                logger.info("\n📂 Arquivos gerados:")
                for key, path in resultados['arquivos_gerados'].items():
                    if os.path.exists(path):
                        logger.info(f"   - {key}: {path}")
                    else:
                        logger.warning(f"   - {key}: ARQUIVO NÃO ENCONTRADO EM {path}")
                        
                # Copia os arquivos para o diretório de saída
                for key, src_path in resultados['arquivos_gerados'].items():
                    if os.path.exists(src_path):
                        dest_path = os.path.join(output_dir, os.path.basename(src_path))
                        try:
                            import shutil
                            shutil.copy2(src_path, dest_path)
                            logger.info(f"   - Copiado para: {dest_path}")
                        except Exception as copy_err:
                            logger.error(f"Erro ao copiar {src_path} para {dest_path}: {str(copy_err)}")
            else:
                logger.warning("\n⚠️  Nenhum resultado retornado pela função visualize_consensus_trees.")
                
        except Exception as viz_err:
            logger.error(f"\n❌ ERRO durante a geração das visualizações: {str(viz_err)}", exc_info=True)
            
    except Exception as e:
        logger.error(f"\n❌ ERRO durante a execução do pipeline: {str(e)}", exc_info=True)
    finally:
        logger.info("\n✅ Processamento concluído!")
    return 0

if __name__ == "__main__":
    main()

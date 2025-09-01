import argparse
import glob
import logging
import multiprocessing as mp
import os
import signal
import subprocess
import sys
import time
import traceback
from pathlib import Path
from typing import List, Optional, Dict, Any

# Configura logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(), logging.FileHandler("damicore_chunked.log")],
)
logger = logging.getLogger(__name__)

# Configuração de timeouts (segundos)
SUBPROCESS_TIMEOUT = 3600  # 1 hora
SUBPROCESS_RETRIES = 3

# Tamanho do chunk padrão (MB)
DEFAULT_CHUNK_SIZE_MB = 100

# Configura o caminho para o executável DAMICORE
try:
    DAMICORE = str(Path(__file__).resolve().parent.parent / "damicore.py")
    if not os.path.exists(DAMICORE):
        raise FileNotFoundError(f"DAMICORE não encontrado em: {DAMICORE}")
except Exception as e:
    logger.error(str(e))
    sys.exit(1)


def split_file_by_size(
    input_file: str, output_dir: str, chunk_size_mb: int = 10
) -> List[str]:
    """Divide um arquivo em pedaços menores.

    Args:
        input_file: Caminho para o arquivo de entrada
        output_dir: Diretório de saída para os chunks
        chunk_size_mb: Tamanho máximo de cada chunk em MB

    Returns:
        Lista com os caminhos dos arquivos gerados
    """
    try:
        os.makedirs(output_dir, exist_ok=True)
        chunk_size = chunk_size_mb * 1024 * 1024  # Convert MB to bytes
        output_files = []

        with open(input_file, "r", encoding="utf-8") as f:
            header = f.readline()
            if not header:
                return []

            chunk_num = 1
            current_chunk_size = 0
            current_chunk = [header]

            for line in f:
                line_size = len(line.encode("utf-8"))

                if (
                    current_chunk_size + line_size > chunk_size
                    and len(current_chunk) > 1
                ):
                    # Save current chunk
                    chunk_path = os.path.join(output_dir, f"chunk_{chunk_num:04d}.csv")
                    with open(chunk_path, "w", encoding="utf-8") as chunk_file:
                        chunk_file.writelines(current_chunk)
                    output_files.append(chunk_path)

                    # Start new chunk
                    chunk_num += 1
                    current_chunk = [header, line]
                    current_chunk_size = len(header) + line_size
                else:
                    current_chunk.append(line)
                    current_chunk_size += line_size

            # Save the last chunk if not empty
            if len(current_chunk) > 1:
                chunk_path = os.path.join(output_dir, f"chunk_{chunk_num:04d}.csv")
                with open(chunk_path, "w", encoding="utf-8") as chunk_file:
                    chunk_file.writelines(current_chunk)
                output_files.append(chunk_path)

        return output_files
    except Exception as e:
        logger.error("Erro ao dividir o arquivo: %s", str(e), exc_info=True)
        raise


def run_command_with_retry(
    cmd: List[str], max_retries: int = 3, retry_delay: int = 5, timeout: int = 3600
) -> bool:
    """Executa um comando com tratamento de erros e retentativas."""
    for attempt in range(max_retries):
        try:
            logger.debug("Executando comando: %s", " ".join(cmd))
            result = subprocess.run(
                cmd, check=True, capture_output=True, text=True, timeout=timeout
            )
            logger.debug("Saída do comando: %s", result.stdout)
            return result.returncode == 0

        except subprocess.CalledProcessError as e:
            logger.error(
                "Erro ao executar comando (tentativa %d/%d): %s",
                attempt + 1,
                max_retries,
                str(e),
            )
            logger.debug("Erro detalhado: %s", e.stderr)
            if attempt < max_retries - 1:
                logger.info(
                    "Aguardando %d segundos antes de tentar novamente...", retry_delay
                )
                time.sleep(retry_delay)
        except Exception as e:
            logger.error("Erro inesperado: %s", str(e))

        if attempt < max_retries - 1:
            wait_time = 5 * (attempt + 1)
            logger.info(
                "Aguardando %d segundos antes de tentar novamente...", wait_time
            )
            time.sleep(wait_time)

    return False


def process_chunk(
    chunk_id: int, input_file: str, results_dir: str, num_bootstraps: int = 22
) -> bool:
    """
    Processa um chunk do arquivo de entrada, gerando apenas as saídas essenciais.

    Args:
        chunk_id: ID do chunk
        input_file: Caminho para o arquivo de entrada
        results_dir: Diretório de saída para os resultados
        num_bootstraps: Número de bootstraps para o DAMICORE (não utilizado atualmente)

    Returns:
        True se o processamento foi bem-sucedido, False caso contrário
    """
    try:
        # Cria diretório de saída para o chunk
        chunk_result_dir = os.path.join(results_dir, f"chunk_{chunk_id:04d}")
        os.makedirs(chunk_result_dir, exist_ok=True)

        # Verifica se o chunk já foi processado
        chunk_result_file = os.path.join(chunk_result_dir, "tree.newick")
        if os.path.exists(chunk_result_file):
            logger.info(f"Chunk {chunk_id} já processado anteriormente")
            return True
        
        # Verifica se já existe um resultado final
        consensus_output = os.path.join(results_dir, "consensus_tree.newick")
        if os.path.exists(consensus_output):
            logger.info("Arquivo de consenso já existe: %s", consensus_output)
            return True

        # Cria diretório temporário para entrada do DAMICORE
        damicore_input_dir = os.path.join(chunk_result_dir, "damicore_input")
        os.makedirs(damicore_input_dir, exist_ok=True)
        
        # Lê o arquivo CSV e adiciona ruído aleatório para evitar desvio padrão zero
        import random
        import pandas as pd
        
        # Lê o arquivo CSV
        df = pd.read_csv(input_file)
        
        # Adiciona ruído aleatório a colunas numéricas com valores iguais
        for col in df.select_dtypes(include=['float64', 'int64']).columns:
            if df[col].nunique() == 1:  # Se todos os valores forem iguais
                noise = [random.uniform(-0.0001, 0.0001) for _ in range(len(df))]
                df[col] = df[col] + noise
        
        # Cria um diretório para os arquivos de entrada do DAMICORE
        chunk_input_dir = os.path.join(damicore_input_dir, f"chunk_{chunk_id:04d}_input")
        os.makedirs(chunk_input_dir, exist_ok=True)
        
        # Salva cada coluna como um arquivo separado para o DAMICORE processar
        logger.info(f"Processando {len(df.columns)} colunas do chunk {chunk_id}")
        for col_idx, col in enumerate(df.columns):
            col_file = os.path.join(chunk_input_dir, f"col_{col_idx:04d}.txt")
            df[[col]].to_csv(col_file, index=False, header=False)
            
            # Log a cada 10 colunas para acompanhar o progresso
            if (col_idx + 1) % 10 == 0 or (col_idx + 1) == len(df.columns):
                logger.info(f"  - Processadas {col_idx + 1}/{len(df.columns)} colunas")
        
        # Configura o comando para executar o DAMICORE
        logger.info(f"Iniciando execução do DAMICORE para o chunk {chunk_id} com {len(df.columns)} colunas")
        
        # Garante que o diretório de saída existe
        os.makedirs(os.path.dirname(chunk_result_file), exist_ok=True)
        
        # Configura o comando DAMICORE para processar todas as colunas
        cmd = [
            sys.executable,
            DAMICORE,
            "-c", "gzip",  # Usa compressão gzip
            "--tree-output", chunk_result_file,
            "--parallel",   # Usa processamento paralelo
            "--all-columns", # Garante que todas as colunas serão processadas
            chunk_input_dir
        ]
        
        # Log detalhado do comando e ambiente
        logger.info("Executando DAMICORE no chunk %d com %d colunas", chunk_id, len(df.columns))
        logger.debug("Comando completo: %s", " ".join(cmd))
        logger.debug("Diretório de trabalho: %s", os.getcwd())
        logger.debug("Arquivos no diretório de entrada (%d): %s", 
                    len(os.listdir(chunk_input_dir)), 
                    ", ".join(os.listdir(chunk_input_dir)[:10]) + ("..." if len(os.listdir(chunk_input_dir)) > 10 else ""))
        
        try:
            # Calcula o timeout baseado no tamanho do arquivo em MB
            # Baseado em observações empíricas:
            # - 1MB: ~5 minutos
            # - 10MB: ~15 minutos
            # - 100MB: ~60 minutos
            # - 200MB: ~120 minutos
            # Fórmula: base_timeout = min(14400, max(300, file_size_mb * 60))  # Entre 5 minutos e 4 horas
            file_size_mb = os.path.getsize(input_file) / (1024 * 1024)  # Tamanho em MB
            base_timeout = min(14400, max(300, file_size_mb * 60))  # 5 min to 4 hours
            
            # Ajusta o timeout com base no número de colunas (arquivos no diretório de entrada)
            num_columns = len([f for f in os.listdir(chunk_input_dir) if f.startswith('col_')])
            logger.info(f"Encontradas {num_columns} colunas no diretório de entrada")
            
            # Ajuste mais agressivo para arquivos com muitas colunas
            if num_columns > 100:
                column_factor = 2.0 + (num_columns / 100)  # Aumenta 1% por coluna acima de 100
            else:
                column_factor = 1.0 + (num_columns / 50)   # Aumenta 1% por coluna acima de 50
                
            adaptive_timeout = int(base_timeout * column_factor)
            
            # Log detalhado do cálculo do timeout
            logger.debug(f"Base timeout: {base_timeout}s, Column factor: {column_factor:.2f}, Adaptive timeout: {adaptive_timeout}s")
            
            logger.info(
                "Chunk %d: %.2f MB, %d colunas, timeout ajustado para %d segundos (%.1f horas)",
                chunk_id, file_size_mb, num_columns, adaptive_timeout, adaptive_timeout/3600
            )
            
            # Executa o comando com timeout adaptativo e captura saída em tempo real
            logger.info(f"Iniciando execução do DAMICORE (timeout: {adaptive_timeout}s)")
            
            # Usamos Popen para capturar saída em tempo real
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            # Captura saída em tempo real
            stdout_lines = []
            stderr_lines = []
            
            # Função para ler linhas em tempo real
            def read_output(pipe, lines, label):
                for line in pipe:
                    lines.append(line)
                    logger.debug(f"DAMICORE {label}: {line.strip()}")
            
            # Inicia threads para capturar saída
            import threading
            stdout_thread = threading.Thread(
                target=read_output, 
                args=(process.stdout, stdout_lines, 'stdout')
            )
            stderr_thread = threading.Thread(
                target=read_output, 
                args=(process.stderr, stderr_lines, 'stderr')
            )
            
            stdout_thread.daemon = True
            stderr_thread.daemon = True
            stdout_thread.start()
            stderr_thread.start()
            
            # Aguarda o processo terminar ou timeout
            try:
                process.wait(timeout=adaptive_timeout)
                return_code = process.returncode
            except subprocess.TimeoutExpired:
                logger.error(f"Timeout de {adaptive_timeout}s atingido para o chunk {chunk_id}")
                # Tenta terminar o processo de forma limpa
                process.terminate()
                try:
                    process.wait(timeout=30)
                except subprocess.TimeoutExpired:
                    logger.warning("Processo não terminou após 30s, forçando término...")
                    process.kill()
                return False
                
            # Aguarda as threads terminarem
            stdout_thread.join(timeout=5)
            stderr_thread.join(timeout=5)
            
            # Cria objeto de resultado compatível
            result = subprocess.CompletedProcess(
                args=cmd,
                returncode=return_code,
                stdout=''.join(stdout_lines),
                stderr=''.join(stderr_lines)
            )
            
            logger.debug("Saída do comando: %s", result.stdout)
            
            success = True
        except subprocess.CalledProcessError as e:
            logger.error(
                "Erro ao executar comando (tentativa %d/%d): %s",
                1,
                1,
                str(e),
            )
            logger.debug("Erro detalhado: %s", e.stderr)
            success = False
        except Exception as e:
            logger.error("Erro inesperado: %s", str(e))
            success = False

        if not success:
            logger.error("Falha ao processar o chunk %d", chunk_id)
            return False
            
        # Verifica se o arquivo da árvore foi gerado
        if not os.path.exists(chunk_result_file):
            logger.error("Arquivo de árvore não foi gerado para o chunk %d", chunk_id)
            return False
            
        logger.info("Chunk %d processado com sucesso", chunk_id)
        return True

    except Exception as e:
        logger.error("Erro durante o processamento do chunk %d: %s", chunk_id, str(e))
        logger.debug("Traceback: %s", traceback.format_exc())
        return False
        return False


def signal_handler(signum, frame):
    """Manipulador para sinais de interrupção."""
    logger.warning("Recebido sinal %d. Encerrando...", signum)
    sys.exit(1)


def calculate_tree_similarity(consensus, tree):
    """Calcula a similaridade entre a árvore de consenso e uma árvore individual.
    
    Args:
        consensus: Árvore de consenso
        tree: Árvore individual para comparação
        
    Returns:
        dict: Dicionário com métricas de similaridade
    """
    try:
        # Calcula a distância de Robinson-Foulds normalizada
        rf = consensus.treenode.robinson_foulds(tree.treenode, unrooted_trees=True)[0]
        max_rf = consensus.treenode.robinson_foulds(tree.treenode, unrooted_trees=True)[1]
        rf_norm = rf / max_rf if max_rf > 0 else 0.0
        
        # Calcula a distância de distância de ramos
        # Padroniza os comprimentos dos ramos primeiro
        cons_tree = consensus.copy()
        comp_tree = tree.copy()
        
        for t in [cons_tree, comp_tree]:
            for node in t.treenode.traverse():
                if not node.is_leaf() and not node.is_root():
                    if node.dist is None:
                        node.dist = 0.0
        
        # Calcula a distância euclidiana entre os comprimentos dos ramos
        def get_branch_lengths(t):
            return [node.dist for node in t.treenode.traverse() 
                   if not node.is_root() and node.dist is not None]
        
        cons_lengths = get_branch_lengths(cons_tree)
        comp_lengths = get_branch_lengths(comp_tree)
        
        # Preenche com zeros se os comprimentos tiverem tamanhos diferentes
        max_len = max(len(cons_lengths), len(comp_lengths))
        cons_lengths.extend([0] * (max_len - len(cons_lengths)))
        comp_lengths.extend([0] * (max_len - len(comp_lengths)))
        
        # Calcula a distância euclidiana normalizada
        import numpy as np
        euclidean_dist = np.linalg.norm(np.array(cons_lengths) - np.array(comp_lengths))
        max_euclidean = np.linalg.norm(np.ones(max_len) * max(max(cons_lengths), max(comp_lengths)))
        euclidean_norm = euclidean_dist / max_euclidean if max_euclidean > 0 else 0.0
        
        # Similaridade geral (1 - média das distâncias normalizadas)
        similarity = 1 - ((rf_norm + euclidean_norm) / 2)
        
        return {
            'rf_distance': rf,
            'rf_normalized': rf_norm,
            'euclidean_distance': float(euclidean_dist),
            'euclidean_normalized': float(euclidean_norm),
            'similarity_score': float(similarity)
        }
    except Exception as e:
        logger.error(f"Erro ao calcular similaridade: {str(e)}")
        return None

def consolidate_results(results_dir: str) -> None:
    """Consolida os resultados dos chunks processados gerando apenas as saídas finais.
    
    Saídas geradas:
    - results_dir/consensus_tree.newick: Árvore de consenso final
    - results_dir/Consensus_tree/: Visualizações da árvore de consenso
    - results_dir/Cloud_tree/: Visualização da nuvem de árvores
    - results_dir/tree_similarity.txt: Análise de similaridade

    Args:
        results_dir: Diretório base contendo os resultados
    """
    # Cria diretórios de saída
    consensus_dir = os.path.join(results_dir, "Consensus_tree")
    cloud_dir = os.path.join(results_dir, "Cloud_tree")
    os.makedirs(consensus_dir, exist_ok=True)
    os.makedirs(cloud_dir, exist_ok=True)

    # Caminhos dos arquivos de saída
    consensus_output = os.path.join(results_dir, "consensus_tree.newick")
    similarity_file = os.path.join(results_dir, "tree_similarity.txt")
    
    # Verifica se já existe um arquivo de consenso
    if os.path.exists(consensus_output):
        logger.info("Arquivo de consenso já existe: %s", consensus_output)
        return

    # Lista todos os diretórios de chunks processados que contêm árvores
    chunk_trees = []
    chunk_dirs = sorted(glob.glob(os.path.join(results_dir, "chunk_*")))
    
    for chunk_dir in chunk_dirs:
        tree_file = os.path.join(chunk_dir, "tree.newick")
        if os.path.exists(tree_file):
            chunk_trees.append(tree_file)
    
    if not chunk_trees:
        logger.warning("Nenhuma árvore de chunk válida encontrada")
        return
    
    logger.info("Consolidando %d/%d chunks processados", len(chunk_trees), len(chunk_dirs))
    
    try:
        import toytree
        
        # Carrega todas as árvores
        trees = [toytree.tree(tree_file) for tree_file in chunk_trees]
        
        # Gera a árvore de consenso usando o método multitree
        mtree = toytree.mtree(trees)
        consensus_tree = mtree.get_consensus_tree(
            min_support=0.8,  # 80% de suporte mínimo
            name_func=lambda x: f"{x*100:.0f}%"
        )
        consensus_newick = consensus_tree.write()
        
        # Salva a árvore de consenso
        with open(consensus_output, 'w', encoding='utf-8') as f:
            f.write(consensus_newick)
        logger.info("Árvore de consenso (80%%) gerada em: %s", consensus_output)
        
        # Carrega a árvore de consenso para visualização
        consensus = toytree.tree(consensus_newick)
        
        # Gera visualizações da árvore de consenso (PDF e PNG)
        for fmt in ['pdf', 'png']:
            plot_path = os.path.join(consensus_dir, f"consensus_tree.{fmt}")
            
            # Configura o estilo dos rótulos com base no número de dicas
            n_tips = len(consensus.get_tip_labels())
            if n_tips <= 50:
                tip_labels_style = {"font-size": "10px", "max-width": 40}
                width, height = 1000, 700
            elif n_tips <= 100:
                tip_labels_style = {"font-size": "9px", "max-width": 35}
                width, height = 1200, 900
            else:
                tip_labels_style = {"font-size": "8px", "max-width": 30}
                width, height = 1600, 1200
            
            # Desenha a árvore de consenso
            canvas, axes, mark = consensus.draw(
                width=width,
                height=height,
                node_labels='support',
                node_sizes=10,
                node_colors='lightgray',
                tip_labels_style=tip_labels_style,
                tip_labels_align=True,
                scale_bar=True,
                use_edge_lengths=True
            )
            
            # Adiciona título
            axes.text(
                0.5, 1.02,
                "Consensus Tree (80% support)",
                horizontalalignment='center',
                transform=axes.transAxes,
                fontsize=12
            )
            
            # Salva a visualização
            canvas.save(plot_path)
            logger.info("Visualização da árvore de consenso salva em: %s", plot_path)
        
        # Gera visualização da nuvem de árvores
        if len(trees) > 1:  # Só gera se houver mais de uma árvore
            try:
                # Configura o estilo dos rótulos com base no número de dicas
                n_tips = len(trees[0].get_tip_labels()) if trees else 0
                if n_tips <= 50:
                    tip_style = {"font-size": "8px", "max-width": 30}
                    width, height = 1200, 900
                elif n_tips <= 100:
                    tip_style = {"font-size": "7px", "max-width": 25}
                    width, height = 1500, 1200
                else:
                    tip_style = {"font-size": "6px", "max-width": 20}
                    width, height = 2000, 1500
                
                # Limita o número de árvores a serem exibidas para evitar sobrecarga
                max_trees = min(9, len(trees))  # Máximo de 9 árvores (3x3 grid)
                
                # Cria a grade de árvores
                mtree = toytree.mtree(trees[:max_trees])
                canvas, axes, _ = mtree.draw_tree_grid(
                    width=width,
                    height=height,
                    start=0,
                    ncols=3,  # Sempre 3 colunas para melhor visualização
                    tip_labels_style=tip_style,
                    node_sizes=8,
                    node_colors='lightgray',
                    use_edge_lengths=True,
                    scale_bar=True,
                    node_labels='support' if hasattr(trees[0], 'support') else None
                )
                
                # Adiciona título
                axes[0].text(
                    0.5, 1.08,
                    f"Cloud Tree - {len(trees)} trees (showing {max_trees})",
                    horizontalalignment='center',
                    transform=axes[0].transAxes,
                    fontsize=12
                )
                
                # Salva as visualizações
                for fmt in ['pdf', 'png']:
                    cloud_path = os.path.join(cloud_dir, f"cloud_tree.{fmt}")
                    canvas.save(cloud_path)
                    logger.info("Visualização da nuvem de árvores salva em: %s", cloud_path)
                    
            except Exception as e:
                logger.warning("Não foi possível gerar a nuvem de árvores: %s", str(e), exc_info=True)
        
        # Gera análise de similaridade
        with open(similarity_file, 'w', encoding='utf-8') as f:
            f.write("Análise de Similaridade entre Árvores\n")
            f.write("="*50 + "\n\n")
            
            f.write(f"{'Chunk':<15} {'RF Dist.':<15} {'RF Norm.':<15} "
                   f"{'Eucl. Dist.':<15} {'Eucl. Norm.':<15} "
                   f"{'Similaridade':<15}\n")
            f.write("-"*90 + "\n")
            
            total_similarity = 0.0
            valid_trees = 0
            
            for i, tree in enumerate(trees):
                similarity = calculate_tree_similarity(consensus, tree)
                if similarity:
                    chunk_name = f"chunk_{i+1:04d}"
                    f.write(f"{chunk_name:<15} {similarity['rf_distance']:<15.2f} {similarity['rf_normalized']:<15.4f} "
                           f"{similarity['euclidean_distance']:<15.4f} {similarity['euclidean_normalized']:<15.4f} "
                           f"{similarity['similarity_score']*100:<14.2f}%\n")
                    total_similarity += similarity['similarity_score']
                    valid_trees += 1
            
            if valid_trees > 0:
                avg_similarity = (total_similarity / valid_trees) * 100
                f.write("\n" + "="*90 + "\n")
                f.write(f"Média de similaridade: {avg_similarity:.2f}%\n")
                
                if avg_similarity >= 90:
                    quality = "Excelente"
                elif avg_similarity >= 75:
                    quality = "Boa"
                elif avg_similarity >= 50:
                    quality = "Razoável"
                else:
                    quality = "Baixa"
                    
                f.write(f"Qualidade do consenso: {quality}\n")
        
        logger.info("Análise de similaridade salva em: %s", similarity_file)
        
    except ImportError:
        logger.error("Erro: toytree não encontrado. É necessário instalar o pacote toytree.")
        raise
    except Exception as e:
        logger.error("Erro ao gerar resultados consolidados: %s", str(e), exc_info=True)
        raise
        logger.info("Usando árvore do primeiro chunk como fallback: %s", consensus_output)


def main() -> None:
    """Função principal do script."""
    # Configura manipuladores de sinal
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    parser = argparse.ArgumentParser(
        description=("DAMICORE em modo chunked " "(para arquivos grandes)."),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--input", required=True, help="Arquivo CSV de entrada (grande)"
    )
    parser.add_argument(
        "--workdir",
        required=True,
        help="Diretório de trabalho para arquivos temporários e resultados",
    )
    parser.add_argument(
        "--chunk-size-mb",
        type=int,
        default=DEFAULT_CHUNK_SIZE_MB,
        help="Tamanho máximo de cada chunk em MB (padrão: %(default)sMB)",
    )
    parser.add_argument(
        "--n-processes",
        type=int,
        default=max(1, mp.cpu_count() - 1),
        help="Número de processos em paralelo (padrão: CPUs disponíveis - 1)",
    )
    parser.add_argument(
        "--compressor",
        default="gzip",
        choices=["gzip", "bzip2", "lzma", "zstd"],
        help="Compressor usado pelo DAMICORE",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Ativa modo debug com mais informações de log",
    )

    args = parser.parse_args()

    # Configura nível de log
    if args.debug:
        logger.setLevel(logging.DEBUG)
        logger.debug("Modo debug ativado")
    logger.info("Iniciando processamento de %s", args.input)
    logger.info("Diretório de trabalho: %s", args.workdir)
    logger.info("Usando %d processos paralelos", args.n_processes)
    logger.info("Tamanho do chunk: %dMB", args.chunk_size_mb)
    logger.info("Compressor: %s", args.compressor)

    try:
        # Usa um hash do caminho absoluto do arquivo de entrada para criar um diretório consistente
        input_abs_path = os.path.abspath(args.input)
        import hashlib
        input_hash = hashlib.md5(input_abs_path.encode('utf-8')).hexdigest()
        
        # Cria um diretório baseado no hash do caminho do arquivo
        workdir = os.path.join(args.workdir, f"{os.path.basename(args.input)}_{input_hash[:8]}")
        
        # Define os subdiretórios
        chunks_dir = os.path.join(workdir, "chunks")
        results_dir = os.path.join(workdir, "damicore_results")
        final_dir = os.path.join(workdir, "final")

        for directory in [chunks_dir, results_dir, final_dir]:
            os.makedirs(directory, exist_ok=True)
            logger.debug("Diretório criado/verificado: %s", directory)

        # 1. Dividir arquivo em chunks
        logger.info("Dividindo arquivo em chunks...")
        chunk_files = split_file_by_size(args.input, chunks_dir, args.chunk_size_mb)

        if not chunk_files:
            logger.error(
                "Nenhum chunk foi criado. Verifique o tamanho do chunk e o "
                "arquivo de entrada."
            )
            sys.exit(1)

        logger.info("%d chunks criados com sucesso", len(chunk_files))

        # 2. Processar em paralelo apenas os chunks não processados
        logger.info("Verificando chunks já processados...")
        
        # Filtra apenas os chunks que ainda não foram processados
        chunks_to_process = []
        for i, chunk_path in enumerate(chunk_files, 1):
            chunk_id = f"{i:04d}"
            chunk_result_dir = os.path.join(results_dir, f"chunk_{chunk_id}")
            chunk_tree = os.path.join(chunk_result_dir, "tree.newick")
            
            if os.path.exists(chunk_tree):
                logger.debug("Chunk %s já processado anteriormente", chunk_id)
            else:
                chunks_to_process.append((i, chunk_path, results_dir, 22))  # 22 bootstraps
        
        if not chunks_to_process:
            logger.info("Todos os chunks já foram processados anteriormente")
        else:
            logger.info("Processando %d/%d chunks em paralelo...", 
                       len(chunks_to_process), len(chunk_files))
            
            successful_chunks = 0
            with mp.Pool(args.n_processes) as pool:
                results = pool.starmap(process_chunk, chunks_to_process)
                successful_chunks = sum(1 for r in results if r is not None)
            
            logger.info("%d novos chunks processados com sucesso", successful_chunks)
        
        # Conta o total de chunks processados (antigos + novos)
        processed_chunks = sum(1 for i in range(1, len(chunk_files) + 1)
                             if os.path.exists(os.path.join(results_dir, f"chunk_{i:04d}", "tree.newick")))
        successful_chunks = processed_chunks

        logger.info(
            "Processamento concluído: %d/%d chunks processados com sucesso",
            successful_chunks,
            len(chunk_files),
        )

        if successful_chunks == 0:
            logger.error("Nenhum chunk foi processado com sucesso")
            sys.exit(1)

        # 3. Consolidar e gerar imagens
        logger.info("Consolidando resultados...")
        consolidate_results(results_dir)
        logger.info("Processamento concluído com sucesso!")

    except Exception as e:
        logger.critical("Erro fatal: %s", str(e), exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()

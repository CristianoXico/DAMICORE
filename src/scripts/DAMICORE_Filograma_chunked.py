import argparse
import glob
import logging
import multiprocessing as mp
import os
import signal
import subprocess
import sys
import time
from pathlib import Path
from typing import List

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

# Usa caminho relativo a partir da localização deste script
DAMICORE = str(Path(__file__).parent.parent / "damicore.py")
if not os.path.exists(DAMICORE):
    logger.error(f"DAMICORE não encontrado em: {DAMICORE}")
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
    Processa um chunk do arquivo de entrada.

    Args:
        chunk_id: ID do chunk
        input_file: Caminho para o arquivo de entrada
        results_dir: Diretório de saída para os resultados
        num_bootstraps: Número de bootstraps para o DAMICORE

    Returns:
        True se o processamento foi bem-sucedido, False caso contrário
    """
    try:
        # Cria diretório de saída para o chunk
        chunk_result_dir = os.path.join(results_dir, f"chunk_{chunk_id:04d}")
        os.makedirs(chunk_result_dir, exist_ok=True)

        # Verifica se o chunk já foi processado
        final_dir = os.path.join(results_dir, "final")
        os.makedirs(final_dir, exist_ok=True)  # Garante que o diretório final existe
        consensus_output = os.path.join(final_dir, "consensus_tree.newick")
        
        # Verifica se o chunk já foi processado anteriormente
        chunk_result_file = os.path.join(results_dir, f"chunk_{chunk_id:04d}", "tree.newick")
        if os.path.exists(chunk_result_file):
            logger.info(f"Chunk {chunk_id} já processado anteriormente")
            return True
        
        if os.path.exists(consensus_output):
            logger.info("Arquivo de consenso já existe: %s", consensus_output)
            return True

        # Create a temporary directory for DAMICORE input
        damicore_input_dir = os.path.join(chunk_result_dir, "damicore_input")
        os.makedirs(damicore_input_dir, exist_ok=True)
        
        # Read the input file and add small random noise to avoid zero stddev
        import random
        import pandas as pd
        
        # Read the CSV file
        df = pd.read_csv(input_file)
        
        # Add small random noise to numeric columns to avoid zero stddev
        for col in df.select_dtypes(include=['float64', 'int64']).columns:
            if df[col].nunique() == 1:  # If all values are the same
                noise = [random.uniform(-0.0001, 0.0001) for _ in range(len(df))]
                df[col] = df[col] + noise
        
        # Save the processed file
        input_copy = os.path.join(damicore_input_dir, f"chunk_{chunk_id:04d}.txt")
        df.to_csv(input_copy, index=False)
        
        # Create a second copy with slightly different noise
        for col in df.select_dtypes(include=['float64', 'int64']).columns:
            noise = [random.uniform(-0.0001, 0.0001) for _ in range(len(df))]
            df[col] = df[col] + noise
            
        input_copy2 = os.path.join(damicore_input_dir, f"chunk_{chunk_id:04d}_copy.txt")
        df.to_csv(input_copy2, index=False)
        
        # Run DAMICORE on the directory containing the files
        cmd = [
            sys.executable,
            DAMICORE,
            "-c", "gzip",
            "--ncd-output", os.path.join(chunk_result_dir, "ncd_matrix.csv"),
            "--tree-output", os.path.join(chunk_result_dir, "tree.newick"),
            "--graph-image", os.path.join(chunk_result_dir, "graph.png"),
            damicore_input_dir  # Pass the directory, not the file
        ]
        
        # Note: Bootstrap sampling would need to be implemented separately
        if num_bootstraps > 0:
            logger.warning("Bootstrap sampling is not directly supported in this version. "
                         f"Using single run with {num_bootstraps} bootstraps not implemented.")
            logger.info("Consider running DAMICORE multiple times with different samples "
                       "for bootstrap analysis.")

        logger.info(f"Processando chunk {chunk_id}: {input_file}")
        success = run_command_with_retry(cmd)

        if not success:
            logger.error("Falha ao processar o chunk %d", chunk_id)
            return False

        try:
            from ete3 import Tree

            # Load generated trees
            tree_files = glob.glob(os.path.join(chunk_result_dir, "*tree.newick"))
            trees = []
            for tree_file in tree_files:
                try:
                    tree = Tree(tree_file)
                    trees.append(tree)
                except Exception as e:
                    logger.warning("Erro ao carregar árvore %s: %s", tree_file, str(e))

            if trees:
                # Create final directory if it does not exist
                os.makedirs(final_dir, exist_ok=True)

                # Save consensus tree
                consensus_tree = Tree()
                consensus_tree.consensus(trees)
                consensus_tree.write(outfile=consensus_output)
                logger.info("Árvore de consenso salva em: %s", consensus_output)
                success = True
            else:
                logger.error("Nenhuma árvore válida encontrada para gerar consenso")
                success = False

        except ImportError:
            logger.error("Módulo ete3 não encontrado. Instale com: pip install ete3")
            success = False
        except Exception as e:
            logger.error("Erro ao gerar árvore de consenso: %s", str(e))
            success = False

        if success:
            logger.info("Resultados consolidados com sucesso em %s", final_dir)

        return success

    except Exception as e:
        logger.error("Erro durante o processamento do chunk: %s", str(e))
        try:
            import traceback

            logger.debug("Traceback: %s", traceback.format_exc())
        except ImportError:
            pass
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
    """Consolida os resultados dos chunks processados.

    Args:
        results_dir: Diretório base contendo os resultados
    """
    # Cria diretório final se não existir
    final_dir = os.path.join(results_dir, "final")
    os.makedirs(final_dir, exist_ok=True)

    # Verifica se já existe um arquivo de consenso
    consensus_output = os.path.join(final_dir, "consensus_tree.newick")
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
        # Tenta importar toytree
        import toytree
        
        # Carrega todas as árvores
        trees = [toytree.tree(tree_file) for tree_file in chunk_trees]
        
        # Cria um objeto mtree (multi-tree) com as árvores
        mtree = toytree.mtree(trees)
        
        # Gera árvore de consenso com 80% de suporte mínimo
        consensus = mtree.get_consensus(
            min_support=0.8,  # 80% de suporte mínimo
            rooted=True       # Mantém a raiz
        )
        
        # Salva a árvore de consenso
        consensus.write(consensus_output)
        logger.info("Árvore de consenso (80%%) gerada em: %s", consensus_output)
        
        # Gera visualização da árvore de consenso
        plot_path = os.path.join(final_dir, "consensus_tree.png")
        canvas = consensus.draw(
            width=1200,
            height=800,
            node_labels="support",
            node_sizes=12,
            node_style={"stroke": "#262626"},
            tip_labels_style={"font-size": "10px"}
        )
        canvas.save(plot_path)
        logger.info("Visualização da árvore de consenso salva em: %s", plot_path)
        
        # Calcula similaridade entre árvores
        similarity_file = os.path.join(final_dir, "tree_similarity.txt")
        with open(similarity_file, 'w', encoding='utf-8') as f:
            f.write("Análise de Similaridade entre Árvores\n")
            f.write("="*50 + "\n\n")
            
            # Cabeçalho
            f.write(f"{'Chunk':<15} {'RF Dist.':<15} {'RF Norm.':<15} "
                   f"{'Eucl. Dist.':<15} {'Eucl. Norm.':<15} "
                   f"{'Similaridade':<15}\n")
            f.write("-"*90 + "\n")
            
            # Calcula similaridade para cada árvore
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
            
            # Média de similaridade
            if valid_trees > 0:
                avg_similarity = (total_similarity / valid_trees) * 100
                f.write("\n" + "="*90 + "\n")
                f.write(f"Média de similaridade: {avg_similarity:.2f}%\n")
                
                # Classificação de qualidade
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
        logger.warning("toytree não encontrado. Usando árvore do primeiro chunk como consenso.")
        import shutil
        shutil.copy2(chunk_trees[0], consensus_output)
        logger.info("Árvore de consenso gerada a partir do primeiro chunk: %s", consensus_output)
    except Exception as e:
        logger.error("Erro ao gerar árvore de consenso: %s", str(e))
        import shutil
        shutil.copy2(chunk_trees[0], consensus_output)
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

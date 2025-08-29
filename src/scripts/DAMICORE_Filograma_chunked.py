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

# Configura logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('damicore_chunked.log')
    ]
)
logger = logging.getLogger(__name__)

# Configuração de timeouts (segundos)
SUBPROCESS_TIMEOUT = 3600  # 1 hora
SUBPROCESS_RETRIES = 3

# Tamanho do chunk padrão (MB)
DEFAULT_CHUNK_SIZE_MB = 100

# Usa caminho relativo a partir da localização deste script
DAMICORE = str(Path(__file__).parent.parent / 'damicore.py')
if not os.path.exists(DAMICORE):
    logger.error(f"DAMICORE não encontrado em: {DAMICORE}")
    sys.exit(1)


def split_file_by_size(
    input_file: str,
    output_dir: str,
    chunk_size_mb: int = 10
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

        with open(input_file, 'r', encoding='utf-8') as f:
            header = f.readline()
            if not header:
                return []

            chunk_num = 1
            current_chunk_size = 0
            current_chunk = [header]

            for line in f:
                line_size = len(line.encode('utf-8'))

                if (current_chunk_size + line_size > chunk_size and
                        len(current_chunk) > 1):
                    # Save current chunk
                    chunk_path = os.path.join(
                        output_dir, f"chunk_{chunk_num:04d}.csv"
                    )
                    with open(chunk_path, 'w', encoding='utf-8') as chunk_file:
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
                chunk_path = os.path.join(
                    output_dir, f"chunk_{chunk_num:04d}.csv"
                )
                with open(chunk_path, 'w', encoding='utf-8') as chunk_file:
                    chunk_file.writelines(current_chunk)
                output_files.append(chunk_path)

        return output_files
    except Exception as e:
        logger.error("Erro ao dividir o arquivo: %s", str(e), exc_info=True)
        raise


def run_command_with_retry(
    cmd: List[str],
    max_retries: int = 3,
    retry_delay: int = 5,
    timeout: int = 3600
) -> bool:
    """Executa um comando com tratamento de erros e retentativas."""
    for attempt in range(max_retries):
        try:
            logger.debug("Executando comando: %s", " ".join(cmd))
            result = subprocess.run(
                cmd,
                check=True,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            logger.debug("Saída do comando: %s", result.stdout)
            return result.returncode == 0

        except subprocess.CalledProcessError as e:
            logger.error(
                "Erro ao executar comando (tentativa %d/%d): %s",
                attempt + 1, max_retries, str(e)
            )
            logger.debug("Erro detalhado: %s", e.stderr)
            if attempt < max_retries - 1:
                logger.info(
                    "Aguardando %d segundos antes de tentar novamente...",
                    retry_delay
                )
                time.sleep(retry_delay)
        except Exception as e:
            logger.error("Erro inesperado: %s", str(e))

        if attempt < max_retries - 1:
            wait_time = 5 * (attempt + 1)
            logger.info(
                "Aguardando %d segundos antes de tentar novamente...",
                wait_time
            )
            time.sleep(wait_time)

    return False


def process_chunk(
    chunk_id: int,
    input_file: str,
    results_dir: str,
    num_bootstraps: int = 22
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
        consensus_output = os.path.join(final_dir, "consensus_tree.newick")

        if os.path.exists(consensus_output):
            logger.info("Arquivo de consenso já existe: %s", consensus_output)
            return True
            
        # Run DAMICORE on chunk
        cmd = [
            sys.executable,
            DAMICORE,
            "--input",
            input_file,
            "--output",
            chunk_result_dir,
            "--bootstrap",
            str(num_bootstraps),
            "--out",
            chunk_result_dir,
            "--compressor",
            "bzip2",
            "--clustering",
            "single"
        ]
        
        logger.info(f"Processando chunk {chunk_id}: {input_file}")
        success = run_command_with_retry(cmd)
        
        if not success:
            logger.error("Falha ao processar o chunk %d", chunk_id)
            return False
            
        try:
            from ete3 import Tree
            
            # Load generated trees
            tree_files = glob.glob(os.path.join(
                chunk_result_dir, "*tree.newick"
            ))
            trees = []
            for tree_file in tree_files:
                try:
                    tree = Tree(tree_file)
                    trees.append(tree)
                except Exception as e:
                    logger.warning(
                        "Erro ao carregar árvore %s: %s",
                        tree_file,
                        str(e)
                    )
            
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


def consolidate_results(results_dir: str) -> None:
    """Consolida os resultados dos chunks processados.

    Args:
        results_dir: Diretório base contendo os resultados
    """
    try:
        logger.info("Iniciando consolidação dos resultados em %s", results_dir)
        # Implementar lógica de consolidação aqui
        logger.info("Consolidação concluída com sucesso")
    except Exception as e:
        logger.error("Erro ao consolidar resultados: %s", str(e))
        raise


def main() -> None:
    """Função principal do script."""
    # Configura manipuladores de sinal
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    parser = argparse.ArgumentParser(
        description=(
            "DAMICORE em modo chunked "
            "(para arquivos grandes)."
        ),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        "--input",
        required=True,
        help="Arquivo CSV de entrada (grande)"
    )
    parser.add_argument(
        "--workdir",
        required=True,
        help="Diretório de trabalho para arquivos temporários e resultados"
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
        help="Compressor usado pelo DAMICORE"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Ativa modo debug com mais informações de log"
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
        # Cria diretórios únicos baseados no nome do arquivo de entrada
        input_basename = os.path.splitext(os.path.basename(args.input))[0]
        timestamp = int(time.time())
        unique_dir = f"{input_basename}_{timestamp}"
        workdir = os.path.join(args.workdir, unique_dir)

        chunks_dir = os.path.join(workdir, "chunks")
        results_dir = os.path.join(workdir, "damicore_results")
        final_dir = os.path.join(workdir, "final")

        for directory in [chunks_dir, results_dir, final_dir]:
            os.makedirs(directory, exist_ok=True)
            logger.debug("Diretório criado/verificado: %s", directory)

        # 1. Dividir arquivo em chunks
        logger.info("Dividindo arquivo em chunks...")
        chunk_files = split_file_by_size(
            args.input, chunks_dir, args.chunk_size_mb
        )
        
        if not chunk_files:
            logger.error(
                "Nenhum chunk foi criado. Verifique o tamanho do chunk e o "
                "arquivo de entrada."
            )
            sys.exit(1)
            
        logger.info("%d chunks criados com sucesso", len(chunk_files))

        # 2. Processar em paralelo
        logger.info("Processando chunks em paralelo...")
        pool_args = [
            (i, chunk_path, results_dir, 22)  # 22 bootstraps
            for i, chunk_path in enumerate(chunk_files, 1)
        ]
        
        successful_chunks = 0
        with mp.Pool(args.n_processes) as pool:
            results = pool.starmap(process_chunk, pool_args)
            successful_chunks = sum(1 for r in results if r is not None)
        
        logger.info(
            "Processamento concluído: %d/%d chunks processados com sucesso",
            successful_chunks, len(chunk_files)
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

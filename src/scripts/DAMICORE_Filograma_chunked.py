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
from typing import List, Tuple, Optional

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
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


def split_file_by_size(input_file: str, output_dir: str, chunk_size_mb: int) -> List[Tuple[int, str]]:
    """
    Divide o arquivo CSV em chunks de tamanho aproximado (MB).
    
    Args:
        input_file: Caminho para o arquivo CSV de entrada
        output_dir: Diretório para salvar os chunks
        chunk_size_mb: Tamanho máximo de cada chunk em MB
        
    Returns:
        Lista de tuplas (chunk_id, caminho_do_arquivo)
    """
    try:
        os.makedirs(output_dir, exist_ok=True)
        chunk_files = []
        chunk_size = chunk_size_mb * 1024 * 1024
        
        if not os.path.exists(input_file):
            raise FileNotFoundError(f"Arquivo de entrada não encontrado: {input_file}")
            
        if os.path.getsize(input_file) == 0:
            raise ValueError(f"O arquivo de entrada está vazio: {input_file}")

        with open(input_file, "r", encoding="utf-8") as f:
            header = f.readline()
            if not header:
                raise ValueError("O arquivo de entrada está vazio ou não contém cabeçalho")
                
            chunk_id = 0
            out_path = os.path.join(output_dir, f"resample_chunk_{chunk_id:04d}.csv")
            out = open(out_path, "w", encoding="utf-8")
            out.write(header)
            written = len(header.encode("utf-8"))
            
            try:
                for line in f:
                    line_bytes = len(line.encode("utf-8"))
                    
                    # Se adicionar esta linha ultrapassar o tamanho do chunk, fecha o arquivo atual
                    if written + line_bytes > chunk_size and written > 0:
                        out.close()
                        chunk_files.append((chunk_id, out_path))
                        chunk_id += 1
                        out_path = os.path.join(output_dir, f"resample_chunk_{chunk_id:04d}.csv")
                        out = open(out_path, "w", encoding="utf-8")
                        out.write(header)
                        written = len(header.encode("utf-8"))
                    
                    out.write(line)
                    written += line_bytes
                
                # Adiciona o último chunk se não estiver vazio
                if written > len(header):
                    chunk_files.append((chunk_id, out_path))
                
            except Exception as e:
                out.close()
                os.remove(out_path)  # Remove o arquivo parcial em caso de erro
                raise e
            finally:
                if not out.closed:
                    out.close()
        
        if not chunk_files:
            raise RuntimeError("Nenhum chunk foi criado. Verifique o tamanho do chunk e o arquivo de entrada.")
            
        logger.info(f"Total de {len(chunk_files)} chunks criados em {output_dir}")
        return chunk_files
        
    except Exception as e:
        logger.error(f"Erro ao dividir o arquivo: {str(e)}", exc_info=True)
        # Limpa arquivos parciais em caso de erro
        for _, path in chunk_files:
            try:
                if os.path.exists(path):
                    os.remove(path)
            except Exception as cleanup_error:
                logger.warning(f"Não foi possível remover {path}: {cleanup_error}")
        raise


def run_command_with_retry(cmd: list, max_retries: int = 3, timeout: int = 3600) -> bool:
    """Executa um comando com tratamento de erros e retentativas."""
    for attempt in range(max_retries):
        try:
            logger.debug(f"Tentativa {attempt + 1}/{max_retries}: {' '.join(cmd)}")
            result = subprocess.run(
                cmd,
                check=True,
                timeout=timeout,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            if result.returncode == 0:
                if result.stdout:
                    logger.debug(f"Saída: {result.stdout}")
                return True
            logger.warning(f"Comando falhou com código {result.returncode}. Tentativa {attempt + 1}/{max_retries}")
            if result.stderr:
                logger.error(f"Erro: {result.stderr}")
        except subprocess.TimeoutExpired:
            logger.error(f"Timeout ao executar comando: {' '.join(cmd)}")
        except subprocess.CalledProcessError as e:
            logger.error(f"Erro ao executar comando: {e}")
            if e.stderr:
                logger.error(f"Detalhes do erro: {e.stderr}")
        except Exception as e:
            logger.error(f"Erro inesperado: {str(e)}", exc_info=True)
        
        if attempt < max_retries - 1:
            logger.info(f"Tentando novamente em 5 segundos...")
            time.sleep(5)
    
    return False

def process_chunk(chunk_id: int, chunk_path: str, output_dir: str, compressor: str = "gzip") -> Optional[str]:
    """
    Executa DAMICORE em um chunk.
    
    Args:
        chunk_id: ID do chunk
        chunk_path: Caminho para o arquivo do chunk
        output_dir: Diretório de saída
        compressor: Compressor a ser usado (padrão: gzip)
        
    Returns:
        Caminho para o arquivo .newick gerado ou None em caso de falha
    """
    try:
        # Verifica se o arquivo existe e não está vazio
        if not os.path.exists(chunk_path):
            logger.error(f"Arquivo do chunk {chunk_id} não encontrado: {chunk_path}")
            return None
            
        if os.path.getsize(chunk_path) == 0:
            logger.error(f"Arquivo do chunk {chunk_id} está vazio: {chunk_path}")
            return None
            
        # Lê o conteúdo do arquivo
        with open(chunk_path, 'r') as f:
            lines = f.readlines()
            
        # Verifica se o arquivo tem pelo menos 2 linhas (cabeçalho + dados)
        if len(lines) < 2:
            logger.error(f"Arquivo do chunk {chunk_id} não tem dados suficientes (menos de 2 linhas): {chunk_path}")
            return None
            
        output_tree = os.path.join(output_dir, f"resample_chunk_{chunk_id:04d}-tree.newick")
        logger.info(f"Processando chunk {chunk_id} → {output_tree}")
        
        # Cria um diretório temporário para o processamento
        temp_dir = os.path.join(os.path.dirname(chunk_path), f"temp_chunk_{chunk_id}")
        
        # Limpa diretório temporário se existir
        if os.path.exists(temp_dir):
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)
        
        os.makedirs(temp_dir, exist_ok=True)
        
        # Cria múltiplos arquivos a partir do chunk para atender ao requisito do DAMICORE
        # de ter múltiplos arquivos para comparação
        header = lines[0]
        data_lines = lines[1:]
        
        # Divide os dados em 5 partes iguais (ou menos se não houver dados suficientes)
        n_parts = min(5, len(data_lines))
        chunk_size = max(1, len(data_lines) // n_parts)
        
        for i in range(n_parts):
            start_idx = i * chunk_size
            end_idx = (i + 1) * chunk_size if i < n_parts - 1 else len(data_lines)
            
            part_data = [header] + data_lines[start_idx:end_idx]
            part_file = os.path.join(temp_dir, f"chunk_{chunk_id:04d}_part{i+1:02d}.csv")
            
            with open(part_file, 'w') as f:
                f.writelines(part_data)
                
            # Verifica se o arquivo foi criado corretamente
            if os.path.getsize(part_file) == 0:
                logger.error(f"Falha ao criar arquivo de dados: {part_file}")
                return None
        
        # Cria diretórios temporários necessários
        os.makedirs(os.path.join(temp_dir, 'tmp'), exist_ok=True)
        os.makedirs(os.path.join(temp_dir, 'ppmd_tmp'), exist_ok=True)
        
        # Verifica se existem arquivos no diretório temporário
        if not any(fname.endswith('.csv') for fname in os.listdir(temp_dir)):
            logger.error(f"Nenhum arquivo CSV válido encontrado em {temp_dir}")
            return None
        
        cmd = [
            sys.executable,  # Usa o mesmo interpretador Python
            DAMICORE,
            "--compressor", compressor,
            "--tree-output", output_tree,
            temp_dir  # Passa o diretório em vez do arquivo
        ]
        
        success = run_command_with_retry(
            cmd,
            max_retries=SUBPROCESS_RETRIES,
            timeout=SUBPROCESS_TIMEOUT
        )
        
        if not success or not os.path.exists(output_tree):
            logger.error(f"Falha ao processar chunk {chunk_id}")
            return None
            
        return output_tree
        
    except Exception as e:
        import traceback
        logger.error(f"Erro inesperado ao processar chunk {chunk_id}: {str(e)}")
        logger.debug(f"Traceback: {traceback.format_exc()}")
        return None


def consolidate_results(results_dir: str, final_dir: str) -> bool:
    """
    Coleta todos os arquivos .newick e gera visualizações finais.
    
    Args:
        results_dir: Diretório com os arquivos .newick
        final_dir: Diretório para salvar os resultados finais
        
    Returns:
        True se a consolidação foi bem-sucedida, False caso contrário
    """
    try:
        os.makedirs(final_dir, exist_ok=True)
        newick_files = sorted(glob.glob(os.path.join(results_dir, "*-tree.newick")))

        if not newick_files:
            logger.error("Nenhum arquivo .newick encontrado para consolidar!")
            return False

        logger.info(f"Consolidando {len(newick_files)} árvores...")
        success = True

        # 1. Gera árvore consenso
        consensus_output = os.path.join(final_dir, "consensus_tree.newick")
        if not os.path.exists(consensus_output):
            cmd = [
                sys.executable,
                DAMICORE,
                "--consensus-tree",
                "--output", consensus_output,
                "--input-trees"
            ] + newick_files
            
            if not run_command_with_retry(cmd, max_retries=2, timeout=SUBPROCESS_TIMEOUT):
                logger.warning("Falha ao gerar árvore de consenso")
                success = False
        else:
            logger.info(f"Arquivo de consenso já existe: {consensus_output}")

        # 2. Gera nuvem de árvores
        cloud_output = os.path.join(final_dir, "cloud_tree.png")
        if not os.path.exists(cloud_output):
            cmd = [
                sys.executable,
                DAMICORE,
                "--cloud-tree",
                "--output", cloud_output,
                "--input-trees"
            ] + newick_files
            
            if not run_command_with_retry(cmd, max_retries=2, timeout=SUBPROCESS_TIMEOUT):
                logger.warning("Falha ao gerar nuvem de árvores")
                success = False
        else:
            logger.info(f"Arquivo de nuvem já existe: {cloud_output}")

        if success:
            logger.info(f"Resultados consolidados com sucesso em {final_dir}")
        else:
            logger.warning("Algumas operações de consolidação falharam")
            
        return success
        
    except Exception as e:
        logger.error(f"Erro durante a consolidação: {str(e)}", exc_info=True)
        return False


def signal_handler(signum, frame):
    """Manipulador para sinais de interrupção."""
    logger.warning(f"Recebido sinal {signum}. Encerrando...")
    sys.exit(1)

def main() -> None:
    """Função principal do script."""
    # Configura manipuladores de sinal
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    parser = argparse.ArgumentParser(
        description="DAMICORE em modo chunked (para arquivos grandes).",
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
        help=f"Tamanho máximo de cada chunk em MB (padrão: {DEFAULT_CHUNK_SIZE_MB}MB)",
    )
    parser.add_argument(
        "--n-processes",
        type=int,
        default=max(1, mp.cpu_count() - 1),
        help=f"Número de processos em paralelo (padrão: CPUs disponíveis - 1)",
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
    
    logger.info(f"Iniciando processamento de {args.input}")
    logger.info(f"Usando {args.n_processes} processos paralelos")
    logger.info(f"Tamanho do chunk: {args.chunk_size_mb}MB")
    logger.info(f"Compressor: {args.compressor}")
    
    try:
        # Cria diretórios necessários
        chunks_dir = os.path.join(args.workdir, "chunks")
        results_dir = os.path.join(args.workdir, "damicore_results")
        final_dir = os.path.join(args.workdir, "final")

        for directory in [chunks_dir, results_dir, final_dir]:
            os.makedirs(directory, exist_ok=True)
            logger.debug(f"Diretório criado/verificado: {directory}")

        # 1. Dividir arquivo em chunks
        logger.info("Dividindo arquivo em chunks...")
        chunk_files = split_file_by_size(args.input, chunks_dir, args.chunk_size_mb)
        
        if not chunk_files:
            logger.error("Nenhum chunk foi criado. Verifique o tamanho do chunk e o arquivo de entrada.")
            sys.exit(1)
            
        logger.info(f"{len(chunk_files)} chunks criados com sucesso")

        # 2. Processar em paralelo
        logger.info("Processando chunks em paralelo...")
        pool_args = [
            (cid, cpath, results_dir, args.compressor) for cid, cpath in chunk_files
        ]
        
        successful_chunks = 0
        with mp.Pool(args.n_processes) as pool:
            results = pool.starmap(process_chunk, pool_args)
            successful_chunks = sum(1 for r in results if r is not None)
        
        logger.info(f"Processamento concluído: {successful_chunks}/{len(chunk_files)} chunks processados com sucesso")
        
        if successful_chunks == 0:
            logger.error("Nenhum chunk foi processado com sucesso")
            sys.exit(1)

        # 3. Consolidar e gerar imagens
        logger.info("Consolidando resultados...")
        if not consolidate_results(results_dir, final_dir):
            logger.warning("Algumas operações de consolidação falharam")
            
        logger.info("Processamento concluído com sucesso!")
        
    except Exception as e:
        logger.critical(f"Erro fatal: {str(e)}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()

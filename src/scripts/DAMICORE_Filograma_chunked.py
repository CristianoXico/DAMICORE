import argparse
import glob
import json
import logging
import multiprocessing as mp
import os
import signal
import subprocess
import sys
import time
import traceback
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any, Union, Tuple

class CheckpointManager:
    """Gerenciador de checkpoint para retomada automática do pipeline"""
    
    def __init__(self, output_dir: str):
        """Inicializa o gerenciador de checkpoint
        
        Args:
            output_dir: Diretório onde o arquivo de checkpoint será salvo
        """
        self.output_dir = output_dir
        self.checkpoint_file = os.path.join(output_dir, "damicore_checkpoint.json")
        self.progress = self._load_checkpoint()
        
    def _load_checkpoint(self) -> Dict[str, Any]:
        """Carrega o checkpoint existente ou cria um novo"""
        if os.path.exists(self.checkpoint_file):
            try:
                with open(self.checkpoint_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Erro ao carregar checkpoint: {e}. Criando novo checkpoint.")
                return self._create_new_checkpoint()
        return self._create_new_checkpoint()
    
    def _create_new_checkpoint(self) -> Dict[str, Any]:
        """Cria uma nova estrutura de checkpoint"""
        return {
            "start_time": datetime.now().isoformat(),
            "last_updated": None,
            "status": "running",
            "completed_steps": [],
            "current_step": None,
            "chunks": {},
            "statistics": {
                "total_chunks": 0,
                "completed_chunks": 0,
                "failed_chunks": 0,
                "pending_chunks": 0
            },
            "metadata": {
                "version": "1.0",
                "created_with": "DAMICORE Chunked Processor"
            }
        }
    
    def save_checkpoint(self) -> bool:
        """Salva o checkpoint atual no arquivo"""
        try:
            self.progress["last_updated"] = datetime.now().isoformat()
            with open(self.checkpoint_file, 'w') as f:
                json.dump(self.progress, f, indent=2)
            return True
        except Exception as e:
            logger.error(f"Erro ao salvar checkpoint: {e}")
            return False
    
    def mark_step_completed(self, step_name: str) -> bool:
        """Marca uma etapa como concluída"""
        if step_name not in self.progress["completed_steps"]:
            self.progress["completed_steps"].append(step_name)
            return self.save_checkpoint()
        return True
    
    def is_step_completed(self, step_name: str) -> bool:
        """Verifica se uma etapa foi concluída"""
        return step_name in self.progress["completed_steps"]
    
    def update_chunk_status(self, chunk_id: str, status: str, 
                          error: Optional[str] = None) -> bool:
        """Atualiza o status de um chunk específico
        
        Args:
            chunk_id: ID do chunk
            status: Status atual ('pending', 'processing', 'completed', 'failed')
            error: Mensagem de erro, se houver
        """
        if chunk_id not in self.progress["chunks"]:
            self.progress["chunks"][chunk_id] = {
                "start_time": datetime.now().isoformat(),
                "status": status,
                "end_time": None,
                "error": None
            }
            self.progress["statistics"]["total_chunks"] += 1
            self.progress["statistics"]["pending_chunks"] += 1
        else:
            prev_status = self.progress["chunks"][chunk_id].get("status")
            
            # Atualiza contadores
            if prev_status == "completed":
                self.progress["statistics"]["completed_chunks"] -= 1
            elif prev_status == "failed":
                self.progress["statistics"]["failed_chunks"] -= 1
            elif prev_status == "processing":
                # Não altera contadores
                pass
            else:  # pending
                self.progress["statistics"]["pending_chunks"] -= 1
            
            # Atualiza status
            self.progress["chunks"][chunk_id]["status"] = status
            
            if status == "completed":
                self.progress["chunks"][chunk_id]["end_time"] = datetime.now().isoformat()
                self.progress["statistics"]["completed_chunks"] += 1
            elif status == "failed":
                self.progress["chunks"][chunk_id]["end_time"] = datetime.now().isoformat()
                self.progress["chunks"][chunk_id]["error"] = error
                self.progress["statistics"]["failed_chunks"] += 1
            elif status == "processing":
                self.progress["chunks"][chunk_id]["start_time"] = datetime.now().isoformat()
            else:  # pending
                self.progress["statistics"]["pending_chunks"] += 1
        
        return self.save_checkpoint()
    
    def get_pending_chunks(self) -> List[str]:
        """Retorna a lista de chunks pendentes"""
        return [
            chunk_id for chunk_id, chunk in self.progress["chunks"].items()
            if chunk.get("status") in ["pending", "failed"]
        ]
    
    def get_progress_summary(self) -> Dict[str, Any]:
        """Retorna um resumo do progresso atual"""
        stats = self.progress["statistics"]
        total = stats["total_chunks"] or 1  # Evita divisão por zero
        completed = stats["completed_chunks"]
        
        return {
            "total_chunks": stats["total_chunks"],
            "completed_chunks": completed,
            "failed_chunks": stats["failed_chunks"],
            "pending_chunks": stats["pending_chunks"],
            "progress_percentage": round((completed / total) * 100, 2) if total > 0 else 0,
            "start_time": self.progress.get("start_time"),
            "last_updated": self.progress.get("last_updated"),
            "current_step": self.progress.get("current_step")
        }
    
    def print_progress_summary(self) -> None:
        """Imprime um resumo do progresso atual"""
        summary = self.get_progress_summary()
        print("\n" + "=" * 80)
        print(" RESUMO DO PROGRESSO".center(80))
        print("=" * 80)
        print(f"Total de chunks:       {summary['total_chunks']}")
        print(f"Chunks concluídos:     {summary['completed_chunks']}")
        print(f"Chunks com falha:      {summary['failed_chunks']}")
        print(f"Chunks pendentes:      {summary['pending_chunks']}")
        print(f"Progresso:             {summary['progress_percentage']}%")
        print(f"Etapa atual:           {summary['current_step'] or 'N/A'}")
        print(f"Iniciado em:           {summary['start_time']}")
        print(f"Última atualização:    {summary['last_updated']}")
        print("=" * 80 + "\n")

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
        
        # Lê o arquivo CSV garantindo que todas as colunas sejam lidas
        import random
        import pandas as pd
        
        # Lê o arquivo CSV forçando todas as colunas a serem lidas como string
        # Isso evita que o pandas tente inferir tipos e acabe descartando colunas
        df = pd.read_csv(input_file, dtype=str, keep_default_na=False)
        
        # Converte colunas numéricas para float e adiciona ruído se necessário
        for col in df.columns:
            try:
                # Tenta converter para numérico
                df[col] = pd.to_numeric(df[col], errors='ignore')
                
                # Se for numérico, verifica se precisa adicionar ruído
                if pd.api.types.is_numeric_dtype(df[col]):
                    if df[col].nunique() == 1:  # Se todos os valores forem iguais
                        noise = [random.uniform(-0.0001, 0.0001) for _ in range(len(df))]
                        df[col] = df[col].astype(float) + noise
            except Exception as e:
                logger.debug(f"Não foi possível processar a coluna {col} como numérica: {str(e)}")
        
        logger.info(f"Total de colunas carregadas: {len(df.columns)}")
        logger.debug(f"Colunas: {', '.join(df.columns[:10])}{'...' if len(df.columns) > 10 else ''}")
        
        # Cria um diretório para os arquivos de entrada do DAMICORE
        chunk_input_dir = os.path.join(damicore_input_dir, f"chunk_{chunk_id:04d}_input")
        os.makedirs(chunk_input_dir, exist_ok=True)
        
        # Salva cada coluna como um arquivo separado para o DAMICORE processar
        logger.info(f"Processando {len(df.columns)} colunas do chunk {chunk_id}")
        col_files = []
        
        # Primeiro, limpa o diretório para garantir que não haja arquivos antigos
        for f in os.listdir(chunk_input_dir):
            if f.startswith('col_') and f.endswith('.txt'):
                try:
                    os.remove(os.path.join(chunk_input_dir, f))
                except Exception as e:
                    logger.warning(f"Não foi possível remover arquivo antigo {f}: {str(e)}")
        
        # Garante que o diretório está vazio
        time.sleep(1)  # Dá tempo para o sistema de arquivos
        
        # Processa as colunas em lotes para evitar problemas de memória
        batch_size = 10
        for batch_start in range(0, len(df.columns), batch_size):
            batch_end = min(batch_start + batch_size, len(df.columns))
            batch_columns = df.columns[batch_start:batch_end]
            
            # Processa cada coluna do lote atual
            for col_idx in range(batch_start, batch_end):
                col = df.columns[col_idx]
                col_file = os.path.join(chunk_input_dir, f"col_{col_idx:04d}.txt")
                try:
                    # Salva a coluna em um arquivo temporário primeiro
                    temp_file = f"{col_file}.tmp"
                    df[[col]].to_csv(temp_file, index=False, header=False)
                    
                    # Verifica se o arquivo foi criado corretamente
                    if not os.path.exists(temp_file) or os.path.getsize(temp_file) == 0:
                        logger.error(f"Erro ao salvar o arquivo temporário da coluna {col_idx}")
                        continue
                        
                    # Renomeia o arquivo temporário para o nome final
                    if os.path.exists(col_file):
                        os.remove(col_file)
                    os.rename(temp_file, col_file)
                    
                    # Verifica novamente após o rename
                    if not os.path.exists(col_file) or os.path.getsize(col_file) == 0:
                        logger.error(f"Arquivo final da coluna {col_idx} está vazio ou não foi criado")
                    else:
                        col_files.append(col_file)
                        
                except Exception as e:
                    logger.error(f"Erro ao processar coluna {col_idx} ({col}): {str(e)}")
                    # Tenta remover arquivos temporários em caso de erro
                    if os.path.exists(temp_file):
                        try:
                            os.remove(temp_file)
                        except:
                            pass
            
            # Log de progresso
            logger.info(f"  - Lote concluído: {min(batch_end, len(df.columns))}/{len(df.columns)} colunas processadas")
            
            # Pequena pausa entre lotes para evitar sobrecarga
            time.sleep(0.5)
        
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
            chunk_input_dir  # Já inclui todos os arquivos de colunas
        ]
        
        # Verifica os arquivos gerados
        saved_files = [f for f in os.listdir(chunk_input_dir) if f.startswith('col_') and f.endswith('.txt')]
        logger.info(f"Verificação final: {len(saved_files)} arquivos de coluna salvos em {chunk_input_dir}")
        
        # Log detalhado do comando e ambiente
        logger.info("Executando DAMICORE no chunk %d com %d colunas (arquivos: %d)", 
                   chunk_id, len(df.columns), len(saved_files))
        logger.debug("Comando completo: %s", " ".join(cmd))
        logger.debug("Diretório de trabalho: %s", os.getcwd())
        
        # Log das primeiras 10 colunas e últimas 10 colunas
        if len(saved_files) > 20:
            logger.debug("Primeiras 5 colunas: %s", ", ".join(sorted(saved_files)[:5]))
            logger.debug("...")
            logger.debug("Últimas 5 colunas: %s", ", ".join(sorted(saved_files)[-5:]))
        else:
            logger.debug("Arquivos de coluna: %s", ", ".join(sorted(saved_files)))
            
        # Verifica se há alguma inconsistência
        expected_files = {f"col_{i:04d}.txt" for i in range(len(df.columns))}
        actual_files = set(saved_files)
        missing_files = expected_files - actual_files
        extra_files = actual_files - expected_files
        
        if missing_files:
            logger.warning(f"Arquivos de coluna faltando: {len(missing_files)}/{len(expected_files)}")
            logger.debug(f"Exemplos de arquivos faltando: {list(missing_files)[:5]}")
            
            # Tenta recriar os arquivos faltantes
            for missing in list(missing_files)[:10]:  # Limita a 10 tentativas para não sobrecarregar
                try:
                    col_idx = int(missing[4:-4])  # Extrai o número do nome do arquivo
                    col = df.columns[col_idx]
                    col_file = os.path.join(chunk_input_dir, missing)
                    df[[col]].to_csv(col_file, index=False, header=False)
                    if os.path.exists(col_file) and os.path.getsize(col_file) > 0:
                        logger.info(f"Arquivo {missing} recriado com sucesso")
                        saved_files.append(missing)
                        actual_files.add(missing)
                        missing_files.remove(missing)
                except Exception as e:
                    logger.error(f"Falha ao recriar {missing}: {str(e)}")
        
        if extra_files:
            logger.warning(f"Arquivos de coluna extras encontrados: {len(extra_files)}")
            logger.debug(f"Exemplos de arquivos extras: {list(extra_files)[:5]}")
            
        if not saved_files:
            logger.error("NENHUM arquivo de coluna foi salvo corretamente!")
            return False
            
        # Verificação final
        if missing_files:
            logger.error(f"Ainda faltam {len(missing_files)} arquivos de coluna. Verifique os logs para mais detalhes.")
            # Continua mesmo com arquivos faltando, mas com aviso
            logger.warning("Continuando com arquivos disponíveis, mas resultados podem estar incompletos.")
        else:
            logger.info("Todas as colunas foram processadas com sucesso!")
        
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
            
            # Log detalhado do diretório de entrada do DAMICORE
            input_files = [f for f in os.listdir(chunk_input_dir) if f.startswith('col_') and f.endswith('.txt')]
            logger.info(f"Total de arquivos de coluna no diretório de entrada: {len(input_files)}")
            logger.debug(f"Primeiros 10 arquivos: {sorted(input_files)[:10]}")
            
            # Verifica se o número de arquivos corresponde ao número de colunas
            if len(input_files) != num_columns:
                logger.warning(f"Número de arquivos de coluna ({len(input_files)}) diferente do número de colunas esperado ({num_columns})")
                # Tenta recriar os arquivos faltantes
                for i in range(num_columns):
                    expected_file = f"col_{i:04d}.txt"
                    if expected_file not in input_files:
                        logger.warning(f"Arquivo de coluna faltando: {expected_file}")
                        try:
                            col = df.columns[i]
                            col_file = os.path.join(chunk_input_dir, expected_file)
                            df[[col]].to_csv(col_file, index=False, header=False)
                            logger.info(f"Recriado arquivo de coluna: {expected_file}")
                        except Exception as e:
                            logger.error(f"Falha ao recriar {expected_file}: {str(e)}")
            
            # Executa o comando com timeout adaptativo e captura saída em tempo real
            logger.info(f"Iniciando execução do DAMICORE (timeout: {adaptive_timeout}s)")
            logger.info(f"Comando: {' '.join(cmd)}")
            logger.info(f"Diretório de trabalho: {os.path.dirname(DAMICORE)}")
            
            # Cria pipes para capturar saída em tempo real
            import subprocess
            from subprocess import PIPE, STDOUT
            
            # Usamos Popen com pipes separados para stdout e stderr
            process = subprocess.Popen(
                cmd,
                cwd=os.path.dirname(DAMICORE),
                stdout=PIPE,
                stderr=PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            # Função para ler a saída em tempo real
            def read_output(pipe, lines, label):
                try:
                    for line in pipe:
                        line = line.strip()
                        if line:
                            logger.info(f"DAMICORE {label.upper()}: {line}")
                            lines.append(line)
                except Exception as e:
                    logger.error(f"Erro ao ler {label}: {str(e)}")
            
            # Inicia threads para capturar saída
            import threading
            stdout_lines = []
            stderr_lines = []
            
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
                logger.info(f"Aguardando término do DAMICORE (timeout: {adaptive_timeout}s)")
                process.wait(timeout=adaptive_timeout)
                return_code = process.returncode
                logger.info(f"DAMICORE finalizado com código {return_code}")
                
                # Verifica se o processo foi bem-sucedido
                if return_code != 0:
                    logger.error(f"DAMICORE falhou com código de saída {return_code}")
                    if "error" in '\n'.join(stderr_lines).lower():
                        logger.error("Erros encontrados na saída do DAMICORE:")
                        for line in stderr_lines[-20:]:  # Mostra os últimos 20 erros
                            logger.error(f"  {line}")
                    return False
                
            except subprocess.TimeoutExpired:
                logger.error(f"Timeout de {adaptive_timeout}s atingido para o chunk {chunk_id}")
                # Tenta terminar o processo de forma limpa
                process.terminate()
                try:
                    logger.info("Aguardando término limpo do processo...")
                    process.wait(timeout=30)
                except subprocess.TimeoutExpired:
                    logger.warning("Processo não terminou após 30s, forçando término...")
                    process.kill()
                    process.wait()
                
                # Log do estado final
                logger.error("Estado do diretório de saída:")
                try:
                    output_files = os.listdir(os.path.dirname(chunk_result_file) if chunk_result_file else '.')
                    logger.info(f"Arquivos de saída encontrados: {len(output_files)}")
                    logger.debug(f"Arquivos: {output_files}")
                except Exception as e:
                    logger.error(f"Erro ao listar diretório de saída: {str(e)}")
                
                return False
                
            finally:
                # Garante que as threads sejam finalizadas
                logger.debug("Finalizando threads de leitura...")
                stdout_thread.join(timeout=5)
                stderr_thread.join(timeout=5)
                
                # Fecha os pipes para evitar vazamentos
                if process.stdout:
                    process.stdout.close()
                if process.stderr:
                    process.stderr.close()
            
            # Cria objeto de resultado compatível
            result = subprocess.CompletedProcess(
                args=cmd,
                returncode=return_code,
                stdout='\n'.join(stdout_lines) if stdout_lines else '',
                stderr='\n'.join(stderr_lines) if stderr_lines else ''
            )
            
            # Log de diagnóstico
            if result.returncode == 0:
                logger.info("DAMICORE executado com sucesso!")
                if not os.path.exists(chunk_result_file):
                    logger.error(f"Arquivo de resultado não encontrado: {chunk_result_file}")
                    logger.info("Conteúdo do diretório de saída:")
                    try:
                        out_dir = os.path.dirname(chunk_result_file) or '.'
                        for f in os.listdir(out_dir):
                            logger.info(f"- {f}")
                    except Exception as e:
                        logger.error(f"Erro ao listar diretório: {str(e)}")
                    return False
                elif os.path.getsize(chunk_result_file) == 0:
                    logger.error(f"Arquivo de resultado vazio: {chunk_result_file}")
                    return False
                else:
                    logger.info(f"Arquivo de resultado gerado: {chunk_result_file} ({os.path.getsize(chunk_result_file)} bytes)")
                    return True
            
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

def generate_correlation_analysis(df, output_dir: str):
    """Gera análises de correlação avançadas.
    
    Gera:
    - correlation_matrix_pearson.png: Matriz de correlação de Pearson
    - correlation_matrix_spearman.png: Matriz de correlação de Spearman
    - pca_biplot.png: Biplot de Análise de Componentes Principais
    - hierarchical_clustering_dendrogram.png: Dendrograma de agrupamento hierárquico
    - correlation_network.png: Rede de correlações significativas
    
    Args:
        df: DataFrame com os dados
        output_dir: Diretório de saída para os gráficos
    """
    try:
        import matplotlib.pyplot as plt
        import seaborn as sns
        from sklearn.decomposition import PCA
        from scipy.cluster.hierarchy import dendrogram, linkage
        import networkx as nx
        import numpy as np
        
        os.makedirs(output_dir, exist_ok=True)
        
        # 1. Matriz de Correlação de Pearson
        plt.figure(figsize=(12, 10))
        corr_pearson = df.corr()
        sns.heatmap(corr_pearson, annot=True, cmap='coolwarm', center=0, 
                   fmt='.2f', linewidths=0.5)
        plt.title('Matriz de Correlação de Pearson')
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, 'correlation_matrix_pearson.png'), 
                   dpi=300, bbox_inches='tight')
        plt.close()
        
        # 2. Matriz de Correlação de Spearman
        plt.figure(figsize=(12, 10))
        corr_spearman = df.corr(method='spearman')
        sns.heatmap(corr_spearman, annot=True, cmap='viridis', center=0,
                   fmt='.2f', linewidths=0.5)
        plt.title('Matriz de Correlação de Spearman')
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, 'correlation_matrix_spearman.png'),
                   dpi=300, bbox_inches='tight')
        plt.close()
        
        # 3. PCA Biplot
        pca = PCA(n_components=2)
        pca_result = pca.fit_transform(df)
        
        plt.figure(figsize=(12, 10))
        plt.scatter(pca_result[:, 0], pca_result[:, 1], alpha=0.5)
        
        # Adiciona setas para as variáveis
        for i, feature in enumerate(df.columns):
            plt.arrow(0, 0, pca.components_[0, i] * 3, 
                     pca.components_[1, i] * 3, 
                     color='r', alpha=0.5)
            plt.text(pca.components_[0, i] * 3.2, 
                    pca.components_[1, i] * 3.2,
                    feature, color='r', ha='center', va='center')
        
        plt.xlabel(f'PC1 ({pca.explained_variance_ratio_[0]:.1%})')
        plt.ylabel(f'PC2 ({pca.explained_variance_ratio_[1]:.1%})')
        plt.title('PCA Biplot')
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, 'pca_biplot.png'), 
                   dpi=300, bbox_inches='tight')
        plt.close()
        
        # 4. Dendrograma de Agrupamento Hierárquico
        plt.figure(figsize=(15, 8))
        Z = linkage(df.T, 'ward')
        dendrogram(Z, labels=df.columns, leaf_rotation=90)
        plt.title('Dendrograma de Agrupamento Hierárquico')
        plt.xlabel('Variáveis')
        plt.ylabel('Distância')
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, 'hierarchical_clustering_dendrogram.png'),
                   dpi=300, bbox_inches='tight')
        plt.close()
        
        # 5. Rede de Correlações
        plt.figure(figsize=(15, 15))
        G = nx.Graph()
        
        # Adiciona arestas apenas para correlações significativas (|r| > 0.5)
        for i in range(len(corr_pearson.columns)):
            for j in range(i+1, len(corr_pearson.columns)):
                if abs(corr_pearson.iloc[i, j]) > 0.5:  # Ajuste o limiar conforme necessário
                    G.add_edge(corr_pearson.columns[i], corr_pearson.columns[j], 
                              weight=abs(corr_pearson.iloc[i, j]))
        
        # Layout da rede
        pos = nx.spring_layout(G, k=0.5, iterations=50)
        
        # Desenha a rede
        nx.draw_networkx_nodes(G, pos, node_size=700, node_color='skyblue')
        nx.draw_networkx_edges(G, pos, width=1.0, alpha=0.5, 
                             edge_color='gray')
        nx.draw_networkx_labels(G, pos, font_size=10, font_family='sans-serif')
        
        plt.title('Rede de Correlações (|r| > 0.5)')
        plt.axis('off')
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, 'correlation_network.png'),
                   dpi=300, bbox_inches='tight')
        plt.close()
        
        logger.info("Análises de correlação geradas com sucesso")
        return True
        
    except Exception as e:
        logger.error(f"Erro ao gerar análises de correlação: {str(e)}")
        logger.error(traceback.format_exc())
        return False

def consolidate_results(results_dir: str):
    """Consolida os resultados dos chunks processados gerando apenas as saídas finais.
    
    Saídas geradas:
    - results_dir/consensus_tree.newick: Árvore de consenso final
    - results_dir/Consensus_tree/: Visualizações da árvore de consenso
    - results_dir/Cloud_tree/: Visualização da nuvem de árvores
    - results_dir/tree_similarity.txt: Análise de similaridade
    - results_dir/correlation_analysis/: Análises de correlação avançadas

    Args:
        results_dir: Diretório base contendo os resultados
    """
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


def process_chunk_with_checkpoint(chunk_id: int, chunk_path: str, results_dir: str, 
                                num_bootstraps: int, checkpoint_manager: CheckpointManager) -> bool:
    """Processa um chunk com suporte a checkpoint.
    
    Args:
        chunk_id: ID do chunk
        chunk_path: Caminho para o arquivo do chunk
        results_dir: Diretório de saída
        num_bootstraps: Número de amostras bootstrap
        checkpoint_manager: Gerenciador de checkpoint
        
    Returns:
        True se o processamento foi bem-sucedido, False caso contrário
    """
    chunk_name = f"chunk_{chunk_id:04d}"
    
    try:
        # Verifica se o chunk já foi processado com sucesso
        if checkpoint_manager.progress["chunks"].get(chunk_name, {}).get("status") == "completed":
            logger.info(f"Chunk {chunk_name} já processado. Pulando...")
            return True
            
        # Atualiza status para processando
        checkpoint_manager.update_chunk_status(chunk_name, "processing")
        
        # Processa o chunk
        result = process_chunk(chunk_id, chunk_path, results_dir, num_bootstraps)
        
        if result:
            checkpoint_manager.update_chunk_status(chunk_name, "completed")
            logger.info(f"Chunk {chunk_name} processado com sucesso")
        else:
            checkpoint_manager.update_chunk_status(chunk_name, "failed", "Erro ao processar chunk")
            logger.error(f"Falha ao processar chunk {chunk_name}")
            
        return result
        
    except Exception as e:
        error_msg = f"Erro inesperado ao processar chunk {chunk_name}: {str(e)}"
        logger.error(error_msg)
        logger.error(traceback.format_exc())
        checkpoint_manager.update_chunk_status(chunk_name, "failed", error_msg)
        return False

def main() -> None:
    """Função principal do script com suporte a checkpoint e otimizações de memória."""
    # Configura manipuladores de sinal
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    parser = argparse.ArgumentParser(
        description=("DAMICORE em modo chunked (para arquivos grandes) com suporte a checkpoint"),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--input", 
        required=True, 
        help="Arquivo CSV de entrada (grande)"
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
        help=f"Tamanho máximo de cada chunk em MB (padrão: {DEFAULT_CHUNK_SIZE_MB}MB)",
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
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Retoma o processamento a partir do último checkpoint"
    )
    parser.add_argument(
        "--no-consolidate",
        action="store_true",
        help="Não executa a consolidação final dos resultados"
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
    logger.info("Modo retomada: %s", "Ativado" if args.resume else "Desativado")
    
    # Configurações de memória
    try:
        import resource
        import psutil
        
        # Aumenta o limite de memória para 90% da memória física disponível
        mem_limit = int(psutil.virtual_memory().available * 0.9)
        soft, hard = resource.getrlimit(resource.RLIMIT_AS)
        if soft != resource.RLIM_INFINITY:
            resource.setrlimit(resource.RLIMIT_AS, (mem_limit, hard))
            logger.info(f"Limite de memória definido para {mem_limit/1024/1024:.2f} MB")
    except Exception as e:
        logger.warning(f"Não foi possível configurar o limite de memória: {e}")
    
    # Configura garbage collector para ser mais agressivo
    import gc
    gc.set_threshold(50, 10, 10)  # Mais frequente, mas menos intensivo

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
        
        # Inicializa o gerenciador de checkpoint
        checkpoint_manager = CheckpointManager(workdir)
        
        try:
            # 1. Cria diretórios necessários
            for directory in [chunks_dir, results_dir, final_dir]:
                os.makedirs(directory, exist_ok=True)
                logger.debug("Diretório criado/verificado: %s", directory)
            
            # 2. Dividir arquivo em chunks (se não estiver em modo de retomada)
            chunk_files = []
            if not args.resume or not checkpoint_manager.is_step_completed("file_splitting"):
                logger.info("Dividindo arquivo em chunks...")
                checkpoint_manager.progress["current_step"] = "file_splitting"
                checkpoint_manager.save_checkpoint()
                
                # Limpa chunks antigos se não estiver em modo de retomada
                if not args.resume:
                    for f in glob.glob(os.path.join(chunks_dir, "chunk_*")):
                        if os.path.isfile(f):
                            os.remove(f)
                
                chunk_files = split_file_by_size(args.input, chunks_dir, args.chunk_size_mb)
                
                if not chunk_files:
                    logger.error("Nenhum chunk foi criado. Verifique o arquivo de entrada.")
                    sys.exit(1)
                
                logger.info("%d chunks criados com sucesso", len(chunk_files))
                checkpoint_manager.mark_step_completed("file_splitting")
            else:
                # Em modo de retomada, encontra os chunks existentes
                chunk_files = sorted(glob.glob(os.path.join(chunks_dir, "chunk_*")))
                logger.info("Retomando processamento de %d chunks existentes", len(chunk_files))
            
            # 3. Processar chunks em paralelo com suporte a checkpoint
            if not checkpoint_manager.is_step_completed("chunk_processing"):
                checkpoint_manager.progress["current_step"] = "chunk_processing"
                checkpoint_manager.save_checkpoint()
                
                logger.info("Verificando chunks já processados...")
                
                # Prepara argumentos para cada chunk
                chunks_to_process = []
                for i, chunk_path in enumerate(chunk_files, 1):
                    chunk_name = f"chunk_{i:04d}"
                    chunk_result_dir = os.path.join(results_dir, chunk_name)
                    chunk_tree = os.path.join(chunk_result_dir, "tree.newick")
                    
                    # Verifica se o chunk já foi processado com sucesso
                    if os.path.exists(chunk_tree) and \
                       checkpoint_manager.progress["chunks"].get(chunk_name, {}).get("status") == "completed":
                        logger.debug("Chunk %s já processado com sucesso anteriormente", chunk_name)
                    else:
                        chunks_to_process.append((i, chunk_path, results_dir, 22, checkpoint_manager))
                
                if not chunks_to_process:
                    logger.info("Todos os chunks já foram processados com sucesso")
                else:
                    logger.info("Processando %d/%d chunks em paralelo...", 
                              len(chunks_to_process), len(chunk_files))
                    
                    # Processa em lotes para evitar sobrecarga de memória
                    batch_size = max(1, args.n_processes * 2)
                    for batch_start in range(0, len(chunks_to_process), batch_size):
                        batch = chunks_to_process[batch_start:batch_start + batch_size]
                        logger.info("Processando lote %d/%d (%d chunks)", 
                                  batch_start // batch_size + 1,
                                  (len(chunks_to_process) - 1) // batch_size + 1,
                                  len(batch))
                        
                        with mp.Pool(processes=args.n_processes) as pool:
                            results = pool.starmap(process_chunk_with_checkpoint, batch)
                        
                        # Força coleta de lixo entre lotes
                        import gc
                        gc.collect()
                    
                    # Verifica resultados
                    successful_chunks = sum(1 for r in results if r is True)
                    logger.info("%d/%d chunks processados com sucesso no lote", 
                              successful_chunks, len(batch))
                
                checkpoint_manager.mark_step_completed("chunk_processing")
            
            # 4. Conta o total de chunks processados
            processed_chunks = sum(1 for i in range(1, len(chunk_files) + 1)
                                 if checkpoint_manager.progress["chunks"].get(f"chunk_{i:04d}", {}).get("status") == "completed")
            
            logger.info(
                "Processamento concluído: %d/%d chunks processados com sucesso",
                processed_chunks,
                len(chunk_files),
            )
            
            if processed_chunks == 0:
                logger.error("Nenhum chunk foi processado com sucesso")
                sys.exit(1)
            
            # 5. Consolidar e gerar imagens (se não estiver desativado)
            if not args.no_consolidate and not checkpoint_manager.is_step_completed("result_consolidation"):
                checkpoint_manager.progress["current_step"] = "result_consolidation"
                checkpoint_manager.save_checkpoint()
                
                logger.info("Consolidando resultados...")
                consolidate_results(results_dir)
                checkpoint_manager.mark_step_completed("result_consolidation")
            
            # Atualiza status final
            checkpoint_manager.progress["status"] = "completed"
            checkpoint_manager.progress["end_time"] = datetime.now().isoformat()
            checkpoint_manager.save_checkpoint()
            
            logger.info("\n" + "="*80)
            logger.info("PROCESSAMENTO CONCLUÍDO COM SUCESSO".center(80))
            logger.info("="*80)
            checkpoint_manager.print_progress_summary()
            
        except Exception as e:
            logger.critical("Erro durante o processamento: %s", str(e), exc_info=True)
            
            # Atualiza status de erro no checkpoint
            checkpoint_manager.progress["status"] = f"failed: {str(e)}"
            checkpoint_manager.save_checkpoint()
            checkpoint_manager.print_progress_summary()
            raise
            
    except Exception as e:
        logger.critical("Erro fatal: %s", str(e), exc_info=True)
        sys.exit(1)
        sys.exit(1)


if __name__ == "__main__":
    main()

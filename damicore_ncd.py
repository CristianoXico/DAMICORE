#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Módulo para geração de matriz NCD usando o método do DAMICORE.

Este módulo implementa a geração de matrizes de distância NCD (Normalized Compression Distance)
usando compressão gzip, seguindo a abordagem do DAMICORE.
"""

import os
import subprocess
import numpy as np
import tempfile
import shutil
import sys
import time
import logging
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Any, Union
from concurrent.futures import ProcessPoolExecutor, as_completed

# Configuração de logging

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('damicore_ncd.log')
    ]
)
logger = logging.getLogger(__name__)


def run_damicore(
    input_dir: Union[str, Path],
    output_dir: Union[str, Path],
    compressor: str = "gzip",
    timeout: int = 300,
    verbose: bool = False
) -> bool:
    """
    Executa o DAMICORE em um diretório de entrada.
    
    Args:
        input_dir: Caminho para o diretório contendo os arquivos de entrada
        output_dir: Diretório de saída para os resultados
        compressor: Algoritmo de compressão a ser usado (gzip, bzip2, ppmd)
        timeout: Tempo máximo (em segundos) para a execução do DAMICORE
        verbose: Se True, exibe saída detalhada do DAMICORE
        
    Returns:
        bool: True se a execução for bem-sucedida, False caso contrário
        
    Raises:
        FileNotFoundError: Se o diretório de entrada não existir ou estiver vazio
        ValueError: Se o compressor não for suportado
        RuntimeError: Se ocorrer um erro durante a execução
    """
    # Garante que o diretório de saída existe e tem permissões adequadas
    os.makedirs(output_dir, exist_ok=True, mode=0o755)
    if not os.access(output_dir, os.W_OK):
        raise PermissionError(f"Sem permissão de escrita no diretório de saída: {output_dir}")
    # Validação do compressor
    valid_compressors = ["gzip", "bzip2", "ppmd"]
    if compressor not in valid_compressors:
        error_msg = f"Compressor inválido: {compressor}. Use um dos seguintes: {', '.join(valid_compressors)}"
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    # Verifica se o diretório de saída existe, se não, cria
    try:
        os.makedirs(output_dir, exist_ok=True)
        logger.debug(f"Diretório de saída configurado: {output_dir}")
    except Exception as e:
        error_msg = f"Falha ao criar diretório de saída {output_dir}: {e}"
        logger.error(error_msg)
        raise RuntimeError(error_msg) from e
    
    # Caminho para o script DAMICORE
    try:
        damicore_script = Path(__file__).parent / "damicore_py3" / "damicore.py"
        if not damicore_script.exists():
            # Tenta encontrar o script em outros locais comuns
            possible_paths = [
                Path("damicore_py3") / "damicore.py",
                Path("damicore.py"),
                Path("damicore_py3") / "damicore" / "__main__.py"
            ]
            
            for path in possible_paths:
                if path.exists():
                    damicore_script = path
                    logger.info(f"Script DAMICORE encontrado em: {damicore_script}")
                    break
            else:
                error_msg = (
                    f"Script DAMICORE não encontrado. Procurou em:\n"
                    f"- {damicore_script}\n"
                    f"- {Path('damicore_py3/damicore.py')}\n"
                    f"- {Path('damicore.py')}\n"
                    f"- {Path('damicore_py3/damicore/__main__.py')}"
                )
                logger.error(error_msg)
                raise FileNotFoundError(error_msg)
    except Exception as e:
        error_msg = f"Erro ao localizar o script DAMICORE: {e}"
        logger.error(error_msg, exc_info=True)
        raise RuntimeError(error_msg) from e
    
    # Configura o comando para execução
    # Cria um nome de arquivo temporário para a saída
    # Usa apenas o nome do arquivo temporário, sem o caminho completo
    temp_filename = f"ncd_matrix_{os.urandom(8).hex()}.csv"
    temp_output = output_dir / temp_filename
    
    cmd = [
        sys.executable,  # Usa o mesmo interpretador Python
        str(damicore_script),
        "-c", compressor,
        "-o", str(temp_output),  # Usa um arquivo temporário para a saída
        str(input_dir)
    ]
    
    if verbose:
        cmd.append("--verbose")
    
    # Cria um diretório temporário para o DAMICORE
    temp_dir = None
    work_dir = None
    try:
        temp_dir = Path(tempfile.mkdtemp(prefix='damicore_tmp_'))
        work_dir = temp_dir / 'work'
        work_dir.mkdir(parents=True, exist_ok=True)
        logger.debug(f"Diretório temporário criado: {work_dir}")
    except Exception as e:
        error_msg = f"Falha ao criar diretório temporário: {e}"
        logger.error(error_msg, exc_info=True)
        if temp_dir and temp_dir.exists():
            shutil.rmtree(temp_dir, ignore_errors=True)
        raise RuntimeError(error_msg) from e
    
    try:
        # Define as variáveis de ambiente para o DAMICORE
        env = os.environ.copy()
        env.update({
            'TMP': str(work_dir),
            'TEMP': str(work_dir),
            'TMPDIR': str(work_dir),
            'PYTHONUNBUFFERED': '1',  # Garante saída em tempo real
            'PYTHONIOENCODING': 'utf-8'  # Força codificação UTF-8
        })
        
        # Executa o comando
        logger.info(f"Iniciando execução do DAMICORE com compressor {compressor}")
        logger.debug(f"Comando: {' '.join(str(c) for c in cmd)}")
        logger.debug(f"Diretório de trabalho: {work_dir}")
        logger.debug(f"Variáveis de ambiente: TMP={env.get('TMP')}, TEMP={env.get('TEMP')}, TMPDIR={env.get('TMPDIR')}")
        
        start_time = time.time()
        result = subprocess.run(
            cmd,
            check=False,  # Vamos tratar os erros manualmente
            capture_output=True,
            text=True,
            env=env,
            cwd=str(work_dir),
            timeout=timeout,
            encoding='utf-8',
            errors='replace'  # Trata erros de codificação
        )
        
        execution_time = time.time() - start_time
        logger.info(f"Execução do DAMICORE concluída em {execution_time:.2f} segundos")
        
        # Log da saída
        if result.stdout:
            logger.debug(f"Saída do DAMICORE:\n{result.stdout}")
        if result.stderr:
            logger.warning(f"Avisos/erros do DAMICORE:\n{result.stderr}")
        
        # Verifica o código de retorno
        if result.returncode != 0:
            error_msg = f"DAMICORE falhou com código de saída {result.returncode}"
            if result.stderr:
                error_msg += f":\n{result.stderr.strip()}"
            logger.error(error_msg)
            return False
        
        # Verifica se o arquivo de saída foi criado
        ncd_file = None
        
        # Primeiro verifica o arquivo temporário
        if temp_output.exists():
            ncd_file = temp_output
        else:
            # Se não encontrar, verifica por arquivos com nomes padrão
            for f in output_dir.iterdir():
                if f.name.endswith('_ncd.csv') or f.name == 'ncd_matrix.csv' or f.name.endswith('_ncd_matrix.csv'):
                    ncd_file = f
                    break
        
        if not ncd_file or not ncd_file.exists():
            # Lista os arquivos no diretório para ajudar no diagnóstico
            try:
                files = [f.name for f in output_dir.iterdir()]
                logger.error(f"Arquivos no diretório {output_dir}: {files}")
            except Exception as e:
                logger.error(f"Erro ao listar diretório {output_dir}: {e}")
                
            error_msg = f"Nenhum arquivo NCD encontrado em: {output_dir}"
            logger.error(error_msg)
            return False
            
        logger.info(f"Arquivo NCD gerado com sucesso: {ncd_file}")
        
        # Renomeia o arquivo para o nome final, se necessário
        final_output = output_dir / 'ncd_matrix.csv'
        if ncd_file != final_output:
            try:
                if final_output.exists():
                    final_output.unlink()
                ncd_file.rename(final_output)
                ncd_file = final_output
                logger.info(f"Arquivo NCD renomeado para: {ncd_file}")
            except Exception as e:
                logger.warning(f"Não foi possível renomear o arquivo {ncd_file} para {final_output}: {e}")
        
        return True
        
    except subprocess.TimeoutExpired:
        error_msg = f"Tempo limite excedido ({timeout}s) ao executar o DAMICORE"
        logger.error(error_msg)
        raise RuntimeError(error_msg) from None
        
    except subprocess.CalledProcessError as e:
        error_msg = f"Erro ao executar DAMICORE (código {e.returncode}): {e}"
        if e.stderr:
            error_msg += f"\nSaída de erro:\n{e.stderr}"
        logger.error(error_msg)
        return False
        
    except Exception as e:
        logger.error(f"Erro durante a execução do DAMICORE: {e}", exc_info=True)
        raise
    
    finally:
        # Limpeza dos diretórios temporários, se necessário
        if temp_dir is not None and temp_dir.exists():
            try:
                shutil.rmtree(temp_dir, ignore_errors=True)
                logger.debug(f"Diretório temporário removido: {temp_dir}")
            except Exception as e:
                logger.warning(f"Falha ao remover diretório temporário {temp_dir}: {e}")
                # Não levanta exceção para não sobrescrever o erro original

def process_directory(
    input_dir: Union[str, Path],
    output_base_dir: Union[str, Path],
    compressor: str = "gzip",
    max_workers: int = 4,
    cleanup: bool = True
) -> List[Dict[str, Any]]:
    """
    Processa todos os arquivos em um diretório usando o DAMICORE.
    
    Args:
        input_dir: Diretório contendo os arquivos de entrada
        output_base_dir: Diretório base para os resultados
        compressor: Algoritmo de compressão a ser usado (gzip, bzip2, ppmd)
        max_workers: Número máximo de processos paralelos
        cleanup: Se True, remove arquivos temporários após o processamento
        
    Returns:
        Lista de dicionários com os resultados do processamento
        
    Raises:
        FileNotFoundError: Se o diretório de entrada não existir
        ValueError: Se não houver arquivos para processar ou parâmetros forem inválidos
        RuntimeError: Se ocorrer um erro durante o processamento
    """
    logger.info(f"Iniciando processamento do diretório: {input_dir}")
    
    # Validação dos parâmetros de entrada
    try:
        input_dir = Path(input_dir).resolve()
        output_base_dir = Path(output_base_dir).resolve()
        
        if not input_dir.is_dir():
            error_msg = f"Diretório de entrada não encontrado: {input_dir}"
            logger.error(error_msg)
            raise FileNotFoundError(error_msg)
            
        if not isinstance(max_workers, int) or max_workers < 1:
            error_msg = f"max_workers deve ser um inteiro positivo, recebido: {max_workers}"
            logger.error(error_msg)
            raise ValueError(error_msg)
            
        if compressor not in ["gzip", "bzip2", "ppmd"]:
            error_msg = f"Compressor inválido: {compressor}. Use 'gzip', 'bzip2' ou 'ppmd'"
            logger.error(error_msg)
            raise ValueError(error_msg)

    except Exception as e:
        error_msg = f"Erro na validação dos parâmetros: {e}"
        logger.error(error_msg, exc_info=True)
        raise ValueError(error_msg) from e

    # Lista todos os arquivos no diretório de entrada
    try:
        arquivos = []
        for f in input_dir.iterdir():
            if f.is_file() and not f.name.startswith('.'):
                try:
                    # Verifica se o arquivo pode ser lido
                    with f.open('rb') as test_file:
                        test_file.read(1)  # Tenta ler o primeiro byte
                    arquivos.append(f)
                except (IOError, OSError) as e:
                    logger.warning(f"Não foi possível ler o arquivo {f.name}: {e}")

        if not arquivos:
            error_msg = f"Nenhum arquivo legível encontrado em: {input_dir}"
            logger.error(error_msg)
            raise FileNotFoundError(error_msg)

        logger.info(f"Total de {len(arquivos)} arquivos para processar")

    except Exception as e:
        error_msg = f"Erro ao listar arquivos em {input_dir}: {e}"
        logger.error(error_msg, exc_info=True)
        raise RuntimeError(error_msg) from e

    logger.info(f"Encontrados {len(arquivos)} arquivos para processar")

    # Cria o diretório de saída se não existir
    output_base_dir = Path(output_base_dir)
    output_base_dir.mkdir(parents=True, exist_ok=True)
    logger.debug(f"Diretório de saída: {output_base_dir}")

    # Converte para Path se necessário
    input_dir = Path(input_dir)
    output_base_dir = Path(output_base_dir)

    # Cria os diretórios necessários
    temp_input_dir = None
    temp_output_dir = None

    try:
        # Cria o diretório de saída
        output_base_dir.mkdir(parents=True, exist_ok=True)

        # Cria diretórios temporários
        temp_input_dir = Path(tempfile.mkdtemp(prefix='damicore_input_'))
        temp_output_dir = Path(tempfile.mkdtemp(prefix='damicore_output_'))

        # Garante permissões adequadas
        temp_input_dir.chmod(0o755)
        temp_output_dir.chmod(0o755)

        logger.debug(f"Diretório temporário de entrada: {temp_input_dir}")
        logger.debug(f"Diretório temporário de saída: {temp_output_dir}")

    except Exception as e:
        error_msg = f"Falha ao criar diretórios temporários: {e}"
        logger.error(error_msg, exc_info=True)
        # Limpeza em caso de erro
        for temp_dir in [temp_input_dir, temp_output_dir]:
            if temp_dir and temp_dir.exists():
                try:
                    shutil.rmtree(temp_dir, ignore_errors=True)
                except Exception as cleanup_error:
                    logger.warning(f"Falha ao limpar diretório temporário {temp_dir}: {cleanup_error}")
        raise RuntimeError(error_msg) from e

    try:
        # Cria links simbólicos ou cópias dos arquivos no diretório temporário
        for i, src_file in enumerate(arquivos):
            # Usa um nome curto para evitar problemas com caminhos longos
            dest_file = temp_input_dir / f"file_{i:04d}{src_file.suffix}"

            try:
                # Tenta criar um link simbólico primeiro (mais eficiente)
                if os.name == 'nt':  # Windows
                    import ctypes
                    if hasattr(ctypes, 'windll') and hasattr(ctypes.windll, 'kernel32'):
                        kdll = ctypes.windll.kernel32
                        if hasattr(kdll, 'CreateSymbolicLinkW'):
                            # Verifica se o usuário tem privilégios suficientes
                            if ctypes.windll.shell32.IsUserAnAdmin():
                                # Tenta criar o link simbólico
                                if kdll.CreateSymbolicLinkW(str(dest_file), str(src_file), 0):
                                    continue
                else:  # Unix/Linux/Mac
                    try:
                        dest_file.symlink_to(src_file)
                        continue
                    except OSError:
                        # Se falhar, tenta criar uma cópia
                        pass

                # Se chegou aqui, ou é Windows sem permissão ou o link simbólico falhou
                logger.debug(f"Criando cópia de {src_file} para {dest_file}")
                shutil.copy2(str(src_file), str(dest_file))
            except Exception as e:
                logger.warning(f"Erro ao processar arquivo {src_file}: {e}")
                continue
        
        # Executa o DAMICORE após processar todos os arquivos
        success = run_damicore(
            input_dir=temp_input_dir,
            output_dir=temp_output_dir,
            compressor=compressor,
            verbose=logger.getEffectiveLevel() <= logging.DEBUG
        )
            
        if not success:
            raise RuntimeError("Falha ao executar o DAMICORE")
        
        # Encontra o arquivo de saída gerado
        output_files = [f for f in temp_output_dir.iterdir() 
                      if f.name.endswith('_ncd.csv') or f.name == 'ncd_matrix.csv']
        
        if not output_files:
            raise FileNotFoundError("Nenhum arquivo de saída gerado pelo DAMICORE")
        
        # Usa o primeiro arquivo de saída encontrado
        ncd_file = output_files[0]
        logger.info(f"Arquivo NCD gerado: {ncd_file}")
        
        # Verifica se o arquivo tem conteúdo válido
        try:
            file_size = ncd_file.stat().st_size
            if file_size == 0:
                error_msg = f"Arquivo NCD está vazio: {ncd_file}"
                logger.error(error_msg)
                raise RuntimeError(error_msg)
                
            # Lê as primeiras linhas para verificar o conteúdo
            with ncd_file.open('r', encoding='utf-8') as f:
                first_lines = [next(f) for _ in range(min(5, sum(1 for _ in ncd_file.open(encoding='utf-8'))))]
                logger.debug(f"Primeiras linhas do arquivo {ncd_file}: {first_lines}")
                
        except Exception as e:
            error_msg = f"Erro ao verificar o conteúdo do arquivo {ncd_file}: {e}"
            logger.error(error_msg, exc_info=True)
            raise RuntimeError(error_msg) from e
        
        # Copia o arquivo NCD para o diretório de saída
        dest_file = output_base_dir / ncd_file.name
        try:
            shutil.copy2(str(ncd_file), str(dest_file))
            logger.info(f"Arquivo NCD copiado para: {dest_file}")
        except Exception as e:
            error_msg = f"Falha ao copiar arquivo NCD para {dest_file}: {e}"
            logger.error(error_msg, exc_info=True)
            raise RuntimeError(error_msg) from e
        
        # Retorna as informações do processamento
        return [{
            'input_dir': str(input_dir),
            'output_dir': str(output_base_dir),
            'ncd_file': str(dest_file),
            'mapping_file': str(mapping_file),
            'temp_dir': str(temp_input_dir),
            'success': True,
            'file_size': file_size
        }]
        
    except Exception as e:
        logger.error(f"Erro durante a execução do DAMICORE: {e}", exc_info=True)
        raise
    
    finally:
        # Limpeza dos diretórios temporários, se necessário
        if cleanup:
            for temp_dir in [temp_input_dir, temp_output_dir]:
                if temp_dir and temp_dir.exists():
                    try:
                        shutil.rmtree(temp_dir, ignore_errors=True)
                        logger.debug(f"Diretório temporário removido: {temp_dir}")
                    except Exception as e:
                        logger.warning(f"Falha ao remover diretório temporário {temp_dir}: {e}")
                        # Não levanta exceção para não sobrescrever o erro original


def load_ncd_matrices(results: List[Dict[str, Any]]) -> Tuple[np.ndarray, List[str]]:
    """
    Carrega as matrizes NCD geradas pelo DAMICORE.
    
    Args:
        results: Lista de dicionários com os resultados do processamento
        
    Returns:
        Tupla contendo:
        - Matriz NCD (numpy.ndarray): Matriz de distâncias NCD
        - Lista de rótulos (List[str]): Nomes dos arquivos processados
        
    Raises:
        ValueError: Se nenhum resultado for fornecido ou se os dados forem inconsistentes
        RuntimeError: Se ocorrer um erro ao processar as matrizes
    """
    if not results:
        raise ValueError("Nenhum resultado fornecido para carregar a matriz NCD")
    
    ncd_matrices = []
    processed_files = set()
    
    for result in results:
        if not result.get('success'):
            logger.warning(f"Resultado marcado como falha: {result.get('file', 'desconhecido')}")
            continue
            
        ncd_file = result.get('ncd_file')
        if not ncd_file:
            logger.warning("Chave 'ncd_file' não encontrada no resultado")
            continue
            
        if not Path(ncd_file).exists():
            logger.warning(f"Arquivo NCD não encontrado: {ncd_file}")
            continue
            
        file_size = Path(ncd_file).stat().st_size
        if file_size == 0:
            logger.warning(f"Arquivo NCD vazio: {ncd_file}")
            continue
            
        logger.info(f"Carregando matriz NCD de: {ncd_file} ({file_size/1024:.2f} KB)")
        
        try:
            # Tenta detectar automaticamente o separador
            with open(ncd_file, 'r', encoding='utf-8') as f:
                first_line = f.readline().strip()
                sep = ',' if ',' in first_line else '\t' if '\t' in first_line else None
            
            if sep is None:
                logger.warning(f"Separador não detectado no arquivo {ncd_file}, usando padrão CSV")
                sep = ','
            
            # Lê o arquivo CSV
            df = pd.read_csv(
                ncd_file, 
                header=None, 
                sep=sep,
                dtype=np.float64,
                engine='python',
                on_bad_lines='warn'
            )
            
            # Remove linhas/colunas vazias
            df = df.dropna(how='all').dropna(axis=1, how='all')
            
            # Converte para array numpy
            matrix = df.values
            
            # Validação básica da matriz
            if matrix.size == 0:
                logger.warning(f"Matriz vazia no arquivo: {ncd_file}")
                continue
                
            if matrix.shape[0] != matrix.shape[1]:
                logger.warning(
                    f"Matriz não quadrada em {ncd_file}: {matrix.shape}. "
                    "Ajustando para matriz quadrada."
                )
                # Ajusta para matriz quadrada pegando o menor tamanho
                min_dim = min(matrix.shape)
                matrix = matrix[:min_dim, :min_dim]
            
            # Verifica valores inválidos
            if np.any(np.isnan(matrix)) or np.any(np.isinf(matrix)):
                logger.warning(
                    f"Valores NaN ou infinitos encontrados em {ncd_file}. "
                    "Substituindo por 1.0 (distância máxima)."
                )
                matrix = np.nan_to_num(matrix, nan=1.0, posinf=1.0, neginf=1.0)
            
            # Garante simetria (matriz de distância deve ser simétrica)
            if not np.allclose(matrix, matrix.T, rtol=1e-5, atol=1e-8):
                logger.warning(
                    f"Matriz não simétrica em {ncd_file}. "
                    "Forçando simetria calculando (M + M.T) / 2"
                )
                matrix = (matrix + matrix.T) / 2
            
            # Garante diagonal zero
            np.fill_diagonal(matrix, 0.0)
            
            ncd_matrices.append(matrix)
            processed_files.add(ncd_file)
            
            logger.info(
                f"Matriz {len(ncd_matrices)} carregada: {matrix.shape} "
                f"(min={np.min(matrix):.4f}, max={np.max(matrix):.4f}, "
                f"mean={np.mean(matrix):.4f})"
            )
            
        except Exception as e:
            logger.error(f"Erro ao processar arquivo {ncd_file}: {e}", exc_info=True)
            continue
    
    if not ncd_matrices:
        error_msg = "Nenhuma matriz NCD válida pôde ser carregada"
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    # Se houver apenas uma matriz, retorna-a com os rótulos
    if len(ncd_matrices) == 1:
        # Extrai os nomes dos arquivos sem extensão
        labels = [Path(f).stem for f in processed_files]
        return ncd_matrices[0], labels
    
    # Se houver múltiplas matrizes, calcula a média
    try:
        logger.info(f"Calculando média de {len(ncd_matrices)} matrizes NCD")
        
        # Verifica se todas as matrizes têm o mesmo formato
        shapes = {m.shape for m in ncd_matrices}
        if len(shapes) > 1:
            logger.warning(
                f"Matrizes com formatos diferentes encontrados: {shapes}. "
                "Redimensionando para o menor tamanho comum."
            )
            min_rows = min(m.shape[0] for m in ncd_matrices)
            min_cols = min(m.shape[1] for m in ncd_matrices)
            ncd_matrices = [m[:min_rows, :min_cols] for m in ncd_matrices]
        
        # Calcula a média das matrizes
        avg_matrix = np.mean(ncd_matrices, axis=0)
        
        # Garante propriedades básicas
        np.fill_diagonal(avg_matrix, 0.0)  # Diagonal zero
        
        # Garante simetria
        if not np.allclose(avg_matrix, avg_matrix.T, rtol=1e-5, atol=1e-8):
            avg_matrix = (avg_matrix + avg_matrix.T) / 2
        
        logger.info(
            f"Matriz NCD final: {avg_matrix.shape} "
            f"(min={np.min(avg_matrix):.4f}, max={np.max(avg_matrix):.4f}, "
            f"mean={np.mean(avg_matrix):.4f})"
        )
        
        # Extrai os rótulos dos arquivos processados
        labels = [Path(f).stem for f in processed_files]
        return avg_matrix, labels
        
    except Exception as e:
        error_msg = f"Erro ao calcular média das matrizes NCD: {e}"
        logger.error(error_msg, exc_info=True)
        raise RuntimeError(error_msg) from e


def generate_ncd_matrix(
    input_dir: Union[str, Path],
    output_dir: Optional[Union[str, Path]] = None,
    compressor: str = "gzip",
    max_workers: int = 4,
    cleanup: bool = True,
    timeout: int = 600,
    verbose: bool = False
) -> Tuple[np.ndarray, List[str]]:
    """
    Gera a matriz NCD a partir de um diretório de arquivos usando o DAMICORE.

    Esta função é o ponto de entrada principal para geração de matrizes NCD. Ela:
    1. Valida os parâmetros de entrada
    2. Configura diretórios temporários se necessário
    3. Processa os arquivos de entrada em paralelo
    4. Gera a matriz NCD usando o algoritmo especificado
    5. Retorna a matriz e os rótulos correspondentes

    Args:
        input_dir: Diretório contendo os arquivos de entrada a serem processados
        output_dir: Diretório para salvar os resultados (opcional, usa temporário se None)
        compressor: Algoritmo de compressão a ser usado ('gzip', 'bzip2' ou 'ppmd')
        max_workers: Número máximo de processos paralelos para processamento
        cleanup: Se True, remove arquivos temporários após o processamento
        timeout: Tempo máximo (em segundos) para cada operação de compressão
        verbose: Se True, exibe saída detalhada durante o processamento
        
    Returns:
        Tuple[np.ndarray, List[str]]: 
            - Matriz NCD (numpy.ndarray) com as distâncias normalizadas entre os arquivos
            - Lista de rótulos (nomes dos arquivos sem extensão) correspondentes às linhas/colunas
            
    Raises:
        FileNotFoundError: Se o diretório de entrada não existir ou estiver vazio
        ValueError: Se os parâmetros forem inválidos ou não for possível gerar a matriz
        RuntimeError: Se ocorrer um erro durante o processamento
        
    Exemplo:
        >>> matriz, rotulos = generate_ncd_matrix(
        ...     input_dir="./dados",
        ...     compressor="gzip",
        ...     max_workers=4
        ... )
    """
    start_time = time.time()
    logger.info(
        f"Iniciando geração de matriz NCD com os parâmetros: "
        f"input_dir={input_dir}, compressor={compressor}, "
        f"max_workers={max_workers}, cleanup={cleanup}"
    )
    
    # Validação dos parâmetros
    if not isinstance(input_dir, str) or not input_dir.strip():
        error_msg = f"Diretório de entrada inválido: {input_dir}"
        logger.error(error_msg)
        raise ValueError(error_msg)
        
    if not os.path.isdir(input_dir):
        error_msg = f"Diretório de entrada não encontrado: {input_dir}"
        logger.error(error_msg)
        raise FileNotFoundError(error_msg)
    
    if compressor not in ["gzip", "bzip2", "ppmd"]:
        error_msg = f"Compressor inválido: {compressor}. Use 'gzip', 'bzip2' ou 'ppmd'"
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    if not isinstance(max_workers, int) or max_workers < 1:
        error_msg = f"max_workers deve ser um inteiro positivo, recebido: {max_workers}"
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    # Lista os arquivos de entrada
    try:
        input_files = sorted([
            f for f in os.listdir(input_dir) 
            if os.path.isfile(os.path.join(input_dir, f)) and not f.startswith('.')
        ])
        
        if not input_files:
            error_msg = f"Nenhum arquivo encontrado no diretório: {input_dir}"
            logger.error(error_msg)
            raise FileNotFoundError(error_msg)
            
        logger.info(f"Encontrados {len(input_files)} arquivos em {input_dir}")
        
        # Verifica se há arquivos suficientes
        if len(input_files) < 2:
            error_msg = "São necessários pelo menos 2 arquivos para gerar uma matriz NCD"
            logger.error(error_msg)
            raise ValueError(error_msg)
            
        # Verifica tamanho total dos arquivos
        total_size = sum(os.path.getsize(os.path.join(input_dir, f)) for f in input_files)
        logger.info(f"Tamanho total dos arquivos: {total_size/1024/1024:.2f} MB")
        
    except Exception as e:
        error_msg = f"Erro ao listar arquivos em {input_dir}: {e}"
        logger.error(error_msg, exc_info=True)
        raise RuntimeError(error_msg) from e
    
    # Configura diretório de saída
    temp_dir = None
    is_temp = False  # Inicializa a variável com valor padrão
    try:
        if output_dir is None:
            temp_dir = tempfile.mkdtemp(prefix="damicore_ncd_")
            output_dir = os.path.join(temp_dir, "results")
            is_temp = True
            logger.debug(f"Usando diretório temporário: {output_dir}")
        else:
            os.makedirs(output_dir, exist_ok=True)
            is_temp = False
            logger.debug(f"Usando diretório de saída: {output_dir}")
    except Exception as e:
        error_msg = f"Falha ao configurar diretório de saída: {e}"
        logger.error(error_msg, exc_info=True)
        if temp_dir and os.path.exists(temp_dir):
            shutil.rmtree(temp_dir, ignore_errors=True)
        raise RuntimeError(error_msg) from e
    
    try:
        logger.info(f"Iniciando processamento com compressor: {compressor}")
        
        # Processa o diretório de entrada
        results = process_directory(
            input_dir=input_dir,
            output_base_dir=output_dir,
            compressor=compressor,
            max_workers=max_workers
        )

        if not results:
            error_msg = "Nenhum resultado de processamento retornado"
            logger.error(error_msg)
            raise RuntimeError(error_msg)
            
        if not results[0].get('success', False):
            error_msg = "Falha ao processar os arquivos com o DAMICORE"
            if 'error' in results[0]:
                error_msg += f": {results[0]['error']}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)

        # Carrega a matriz NCD gerada e os rótulos
        logger.info("Carregando matriz NCD gerada...")
        ncd_matrix, labels = load_ncd_matrices(results)
        
        # Se não houver rótulos, gera com base nos nomes dos arquivos de entrada
        if not labels:
            labels = [os.path.splitext(f)[0] for f in input_files]
        
        # Verifica consistência entre matriz e rótulos
        if ncd_matrix.shape[0] != ncd_matrix.shape[1]:
            logger.warning(f"A matriz NCD não é quadrada: {ncd_matrix.shape}")
        
        # Ajusta os rótulos se necessário
        if ncd_matrix.shape[0] != len(labels):
            logger.warning(
                f"Número de rótulos ({len(labels)}) não corresponde ao tamanho da matriz "
                f"({ncd_matrix.shape[0]}). Ajustando..."
            )
            if len(labels) > ncd_matrix.shape[0]:
                labels = labels[:ncd_matrix.shape[0]]
            else:
                # Adiciona rótulos genéricos se necessário
                labels.extend([f"item_{i}" for i in range(len(labels), ncd_matrix.shape[0])])
        
        # Validação final da matriz
        if np.any(np.isnan(ncd_matrix)) or np.any(np.isinf(ncd_matrix)):
            logger.warning("Valores inválidos (NaN/Inf) encontrados na matriz. Substituindo...")
            ncd_matrix = np.nan_to_num(ncd_matrix, nan=1.0, posinf=1.0, neginf=1.0)
        
        # Garante propriedades da matriz de distância
        np.fill_diagonal(ncd_matrix, 0.0)  # Diagonal zero
        
        # Log de estatísticas finais
        exec_time = time.time() - start_time
        logger.info(
            f"Matriz NCD gerada com sucesso em {exec_time:.2f} segundos. "
            f"Dimensões: {ncd_matrix.shape}, "
            f"Média: {np.mean(ncd_matrix):.4f}, "
            f"Mín: {np.min(ncd_matrix):.4f}, "
            f"Máx: {np.max(ncd_matrix):.4f}"
        )
        
        return ncd_matrix, labels
        
    except Exception as e:
        error_msg = f"Erro ao gerar matriz NCD: {e}"
        logger.error(error_msg, exc_info=True)
        raise RuntimeError(error_msg) from e
        
    finally:
        # Limpeza de recursos temporários
        if cleanup and is_temp and temp_dir and os.path.exists(temp_dir):
            try:
                shutil.rmtree(temp_dir, ignore_errors=True)
                logger.debug(f"Diretório temporário removido: {temp_dir}")
            except Exception as e:
                logger.warning(f"Não foi possível remover o diretório temporário {temp_dir}: {e}")
        elif not cleanup and is_temp and temp_dir:
            logger.info(f"Arquivos temporários mantidos em: {temp_dir}")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Gera matriz NCD usando o método do DAMICORE')
    parser.add_argument('input_dir', type=str, help='Diretório contendo os arquivos de entrada')
    parser.add_argument('-o', '--output-dir', type=str, help='Diretório de saída (opcional)')
    parser.add_argument('-c', '--compressor', type=str, default='gzip', 
                       choices=['gzip', 'bzip2', 'lzma'], 
                       help='Algoritmo de compressão a ser usado')
    parser.add_argument('-j', '--jobs', type=int, default=4,
                       help='Número de trabalhos paralelos')
    parser.add_argument('-v', '--verbose', action='store_true',
                       help='Habilita saída detalhada')
    
    args = parser.parse_args()
    
    # Configura o nível de log
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logger.setLevel(log_level)
    
    try:
        ncd_matrix, labels = generate_ncd_matrix(
            input_dir=args.input_dir,
            output_dir=args.output_dir,
            compressor=args.compressor,
            max_workers=args.jobs
        )
        
        print("\nMatriz NCD gerada com sucesso!")
        print(f"Dimensões: {ncd_matrix.shape}")
        print(f"Rótulos: {', '.join(labels)}\n")
        
    except Exception as e:
        logger.error(f"Falha ao gerar matriz NCD: {str(e)}")
        sys.exit(1)

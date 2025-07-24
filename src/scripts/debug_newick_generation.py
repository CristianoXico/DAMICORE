#!/usr/bin/env python3
"""
Script de Diagnóstico para Falha na Geração de Arquivos Newick
==============================================================

Este script diagnostica por que as fatias do DAMICORE_File_Slicer_Processor.py
estão falhando na geração de arquivos .newick, mesmo após execução bem-sucedida
do DAMICORE.

Funcionalidades:
- Analisa estrutura de diretórios de saída
- Verifica permissões de arquivos e diretórios
- Examina logs de execução do DAMICORE
- Testa execução manual de uma fatia
- Identifica arquivos temporários e intermediários
- Verifica integridade dos dados de entrada
"""

import os
import sys
import json
import subprocess
import glob
import stat
from pathlib import Path
from datetime import datetime

def print_header(title):
    """Imprime cabeçalho formatado"""
    print(f"\n{'='*60}")
    print(f"🔍 {title}")
    print(f"{'='*60}")

def print_section(title):
    """Imprime seção formatada"""
    print(f"\n{'─'*40}")
    print(f"📋 {title}")
    print(f"{'─'*40}")

def check_directory_structure(base_dir):
    """Analisa estrutura de diretórios de saída"""
    print_section("Estrutura de Diretórios")
    
    if not os.path.exists(base_dir):
        print(f"❌ Diretório base não existe: {base_dir}")
        return False
    
    print(f"✅ Diretório base existe: {base_dir}")
    
    # Lista todos os subdiretórios
    subdirs = []
    for item in os.listdir(base_dir):
        item_path = os.path.join(base_dir, item)
        if os.path.isdir(item_path):
            subdirs.append(item)
    
    print(f"📁 Subdiretórios encontrados: {len(subdirs)}")
    for subdir in sorted(subdirs)[:10]:  # Mostra apenas os primeiros 10
        print(f"   - {subdir}")
    
    if len(subdirs) > 10:
        print(f"   ... e mais {len(subdirs) - 10} diretórios")
    
    return True

def check_slice_directory(slice_dir):
    """Analisa diretório específico de uma fatia"""
    print_section(f"Análise da Fatia: {os.path.basename(slice_dir)}")
    
    if not os.path.exists(slice_dir):
        print(f"❌ Diretório da fatia não existe: {slice_dir}")
        return False
    
    print(f"✅ Diretório da fatia existe: {slice_dir}")
    
    # Lista todos os arquivos na fatia
    all_files = []
    for root, dirs, files in os.walk(slice_dir):
        for file in files:
            file_path = os.path.join(root, file)
            rel_path = os.path.relpath(file_path, slice_dir)
            file_size = os.path.getsize(file_path)
            all_files.append((rel_path, file_size))
    
    print(f"📄 Total de arquivos: {len(all_files)}")
    
    # Categoriza arquivos por extensão
    extensions = {}
    for file_path, file_size in all_files:
        ext = os.path.splitext(file_path)[1].lower()
        if ext not in extensions:
            extensions[ext] = []
        extensions[ext].append((file_path, file_size))
    
    for ext, files in sorted(extensions.items()):
        print(f"   {ext or '(sem extensão)'}: {len(files)} arquivos")
        
        # Mostra detalhes dos arquivos .newick
        if ext == '.newick':
            print(f"      🎯 Arquivos .newick encontrados:")
            for file_path, file_size in files[:5]:  # Mostra primeiros 5
                print(f"         - {file_path} ({file_size} bytes)")
                
                # Verifica conteúdo do arquivo newick
                full_path = os.path.join(slice_dir, file_path)
                try:
                    with open(full_path, 'r') as f:
                        content = f.read().strip()
                        if content:
                            print(f"           ✅ Conteúdo válido ({len(content)} chars)")
                            # Mostra primeiros 100 caracteres
                            preview = content[:100] + "..." if len(content) > 100 else content
                            print(f"           📝 Preview: {preview}")
                        else:
                            print(f"           ❌ Arquivo vazio")
                except Exception as e:
                    print(f"           ❌ Erro ao ler: {e}")
    
    return len(extensions.get('.newick', [])) > 0

def check_permissions(directory):
    """Verifica permissões de arquivos e diretórios"""
    print_section("Verificação de Permissões")
    
    try:
        # Verifica permissões do diretório principal
        dir_stat = os.stat(directory)
        dir_perms = stat.filemode(dir_stat.st_mode)
        print(f"📁 Diretório: {directory}")
        print(f"   Permissões: {dir_perms}")
        print(f"   Owner: UID {dir_stat.st_uid}, GID {dir_stat.st_gid}")
        
        # Verifica se podemos escrever no diretório
        if os.access(directory, os.W_OK):
            print(f"   ✅ Escrita permitida")
        else:
            print(f"   ❌ Escrita negada")
        
        # Verifica permissões de alguns arquivos
        file_count = 0
        for root, dirs, files in os.walk(directory):
            for file in files[:3]:  # Verifica apenas primeiros 3 arquivos
                file_path = os.path.join(root, file)
                try:
                    file_stat = os.stat(file_path)
                    file_perms = stat.filemode(file_stat.st_mode)
                    print(f"📄 {os.path.relpath(file_path, directory)}: {file_perms}")
                    file_count += 1
                except Exception as e:
                    print(f"❌ Erro ao verificar {file}: {e}")
            
            if file_count >= 3:
                break
                
    except Exception as e:
        print(f"❌ Erro ao verificar permissões: {e}")

def check_checkpoint_status(base_dir):
    """Verifica status do checkpoint"""
    print_section("Status do Checkpoint")
    
    checkpoint_file = os.path.join(base_dir, "pipeline_progress.json")
    
    if not os.path.exists(checkpoint_file):
        print(f"❌ Arquivo de checkpoint não encontrado: {checkpoint_file}")
        return None
    
    try:
        with open(checkpoint_file, 'r') as f:
            checkpoint_data = json.load(f)
        
        print(f"✅ Checkpoint carregado: {checkpoint_file}")
        print(f"📊 Status do pipeline: {checkpoint_data.get('pipeline_status', 'unknown')}")
        print(f"🕐 Última atualização: {checkpoint_data.get('last_updated', 'unknown')}")
        
        slices_status = checkpoint_data.get('slices_status', {})
        total_slices = len(slices_status)
        completed_slices = sum(1 for status in slices_status.values() if status == 'completed')
        failed_slices = sum(1 for status in slices_status.values() if status == 'failed')
        pending_slices = sum(1 for status in slices_status.values() if status == 'pending')
        
        print(f"📈 Fatias totais: {total_slices}")
        print(f"   ✅ Concluídas: {completed_slices}")
        print(f"   ❌ Falhadas: {failed_slices}")
        print(f"   ⏳ Pendentes: {pending_slices}")
        
        # Mostra detalhes das fatias falhadas
        if failed_slices > 0:
            print(f"\n🔍 Fatias falhadas:")
            for slice_name, status in slices_status.items():
                if status == 'failed':
                    print(f"   - {slice_name}")
        
        return checkpoint_data
        
    except Exception as e:
        print(f"❌ Erro ao ler checkpoint: {e}")
        return None

def test_single_slice_execution(slice_dir, filograma_script_path):
    """Testa execução manual de uma fatia"""
    print_section("Teste de Execução Manual")
    
    # Procura arquivo CSV da fatia
    csv_files = glob.glob(os.path.join(slice_dir, "*.csv"))
    
    if not csv_files:
        print(f"❌ Nenhum arquivo CSV encontrado em: {slice_dir}")
        return False
    
    csv_file = csv_files[0]
    print(f"📄 Arquivo CSV encontrado: {os.path.basename(csv_file)}")
    
    # Verifica se o arquivo CSV tem conteúdo
    try:
        with open(csv_file, 'r') as f:
            lines = f.readlines()
        print(f"📊 Linhas no CSV: {len(lines)}")
        
        if len(lines) < 2:
            print(f"❌ CSV tem poucas linhas para processamento")
            return False
            
    except Exception as e:
        print(f"❌ Erro ao ler CSV: {e}")
        return False
    
    # Testa execução do DAMICORE_Filograma_script.py
    if not os.path.exists(filograma_script_path):
        print(f"❌ Script Filograma não encontrado: {filograma_script_path}")
        return False
    
    print(f"🚀 Testando execução do DAMICORE_Filograma_script.py...")
    print(f"   Script: {filograma_script_path}")
    print(f"   Arquivo: {csv_file}")
    
    try:
        # Executa o script com timeout de 5 minutos para teste
        cmd = [sys.executable, filograma_script_path, csv_file]
        print(f"   Comando: {' '.join(cmd)}")
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300,  # 5 minutos
            cwd=slice_dir
        )
        
        print(f"📤 Código de saída: {result.returncode}")
        
        if result.stdout:
            print(f"📝 Saída padrão:")
            print(result.stdout[:1000])  # Primeiros 1000 caracteres
        
        if result.stderr:
            print(f"⚠️ Saída de erro:")
            print(result.stderr[:1000])  # Primeiros 1000 caracteres
        
        # Verifica se arquivos newick foram gerados após execução
        newick_files_after = glob.glob(os.path.join(slice_dir, "**/*.newick"), recursive=True)
        print(f"🎯 Arquivos .newick após execução: {len(newick_files_after)}")
        
        for newick_file in newick_files_after[:3]:
            rel_path = os.path.relpath(newick_file, slice_dir)
            file_size = os.path.getsize(newick_file)
            print(f"   - {rel_path} ({file_size} bytes)")
        
        return result.returncode == 0 and len(newick_files_after) > 0
        
    except subprocess.TimeoutExpired:
        print(f"⏰ Execução expirou após 5 minutos")
        return False
    except Exception as e:
        print(f"❌ Erro na execução: {e}")
        return False

def main():
    """Função principal do diagnóstico"""
    print_header("Diagnóstico de Falha na Geração de Arquivos Newick")
    
    # Configurações
    if len(sys.argv) > 1:
        base_dir = sys.argv[1]
    else:
        base_dir = input("📁 Digite o caminho do diretório de resultados: ").strip()
    
    if not base_dir:
        print("❌ Diretório não especificado")
        return
    
    print(f"🎯 Analisando diretório: {base_dir}")
    
    # Verifica estrutura de diretórios
    if not check_directory_structure(base_dir):
        return
    
    # Verifica status do checkpoint
    checkpoint_data = check_checkpoint_status(base_dir)
    
    # Verifica permissões
    check_permissions(base_dir)
    
    # Analisa algumas fatias específicas
    slice_dirs = []
    for item in os.listdir(base_dir):
        item_path = os.path.join(base_dir, item)
        if os.path.isdir(item_path) and item.startswith('slice_'):
            slice_dirs.append(item_path)
    
    if slice_dirs:
        print_section("Análise de Fatias Específicas")
        
        # Analisa primeiras 3 fatias
        for i, slice_dir in enumerate(sorted(slice_dirs)[:3]):
            has_newick = check_slice_directory(slice_dir)
            
            if not has_newick and i == 0:  # Testa execução manual na primeira fatia sem newick
                filograma_script = os.path.join(
                    os.path.dirname(os.path.dirname(__file__)), 
                    "scripts", 
                    "DAMICORE_Filograma_script.py"
                )
                test_single_slice_execution(slice_dir, filograma_script)
    
    # Resumo final
    print_header("Resumo do Diagnóstico")
    
    total_newick_files = 0
    for slice_dir in slice_dirs:
        newick_files = glob.glob(os.path.join(slice_dir, "**/*.newick"), recursive=True)
        total_newick_files += len(newick_files)
    
    print(f"📊 Total de fatias analisadas: {len(slice_dirs)}")
    print(f"🎯 Total de arquivos .newick encontrados: {total_newick_files}")
    
    if total_newick_files == 0:
        print(f"\n❌ PROBLEMA IDENTIFICADO: Nenhum arquivo .newick foi gerado")
        print(f"🔧 Possíveis causas:")
        print(f"   - Falha na execução do DAMICORE")
        print(f"   - Problemas de permissão de escrita")
        print(f"   - Dados de entrada inválidos")
        print(f"   - Timeout durante processamento")
        print(f"   - Erro no script DAMICORE_Filograma_script.py")
    else:
        print(f"\n✅ Alguns arquivos .newick foram encontrados")
        print(f"🔧 Investigar por que nem todas as fatias geraram arquivos")
    
    print(f"\n🕐 Diagnóstico concluído em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()

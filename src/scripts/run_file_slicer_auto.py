#!/usr/bin/env python3
"""
Script automatizado para executar o DAMICORE_File_Slicer_Processor.py
sem interação manual, fornecendo as respostas automaticamente.
"""

import subprocess
import sys
import os

def run_file_slicer():
    """Executa o File Slicer com respostas automatizadas"""
    
    # Caminho do arquivo CSV
    csv_file = "/media/cristiano-xico/sandbox/data_projects/aggrada-inct-fome-2025-06-20-city-yearly.csv"
    
    # Respostas automatizadas
    responses = [
        csv_file,  # Caminho do arquivo CSV
        "s",       # Usar drive externo
        "s",       # Confirmar drive externo detectado
        "s",       # Continuar processamento anterior
    ]
    
    # Preparar entrada
    input_data = "\n".join(responses) + "\n"
    
    # Executar o script
    script_path = "/home/cristiano-xico/github/CristianoXico/DAMICORE/src/scripts/DAMICORE_File_Slicer_Processor.py"
    
    print("🚀 Iniciando DAMICORE File Slicer Processor...")
    print(f"📁 Arquivo: {csv_file}")
    print("💾 Drive externo: Habilitado")
    print("=" * 80)
    
    try:
        # Executar o processo
        process = subprocess.Popen(
            [sys.executable, script_path],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            cwd=os.path.dirname(script_path)
        )
        
        # Enviar respostas e capturar saída
        output, _ = process.communicate(input=input_data, timeout=3600)  # 1 hora timeout
        
        print(output)
        
        if process.returncode == 0:
            print("\n✅ Pipeline executado com sucesso!")
        else:
            print(f"\n❌ Pipeline falhou com código: {process.returncode}")
            
        return process.returncode
        
    except subprocess.TimeoutExpired:
        print("\n⏰ Timeout - Pipeline ainda em execução...")
        process.kill()
        return 1
    except Exception as e:
        print(f"\n❌ Erro durante execução: {e}")
        return 1

if __name__ == "__main__":
    exit_code = run_file_slicer()
    sys.exit(exit_code)

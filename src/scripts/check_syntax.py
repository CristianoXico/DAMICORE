#!/usr/bin/env python3
"""
Script diagnóstico para verificar problemas de sintaxe no DAMICORE_Filograma_script.py
"""

import os
import sys
import tokenize
import ast

def check_syntax(file_path):
    """Verifica a sintaxe de um arquivo Python."""
    print(f"Verificando sintaxe de: {file_path}")
    
    # Verificar se o arquivo existe
    if not os.path.exists(file_path):
        print(f"❌ Arquivo não encontrado: {file_path}")
        return False
    
    # Verificar versão do Python
    print(f"Versão do Python: {sys.version}")
    
    # Tentar analisar o arquivo com ast
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            source = f.read()
        
        ast.parse(source)
        print("✅ Análise AST: OK")
    except SyntaxError as e:
        print(f"❌ Erro de sintaxe (AST): {e}")
        print(f"  Linha {e.lineno}, coluna {e.offset}: {e.text}")
        return False
    
    # Tentar tokenizar o arquivo
    try:
        with open(file_path, 'rb') as f:
            tokens = list(tokenize.tokenize(f.readline))
        print(f"✅ Tokenização: OK ({len(tokens)} tokens)")
    except tokenize.TokenError as e:
        print(f"❌ Erro de tokenização: {e}")
        return False
    except IndentationError as e:
        print(f"❌ Erro de indentação: {e}")
        return False
    
    # Verificar linhas específicas mencionadas no erro
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Verificar a linha 536 e arredores
        start_line = max(1, 536 - 5)
        end_line = min(len(lines), 536 + 5)
        
        print(f"\nExaminando linhas {start_line}-{end_line}:")
        for i in range(start_line-1, end_line):
            if i < len(lines):
                print(f"{i+1}: {lines[i].rstrip()}")
        
    except Exception as e:
        print(f"❌ Erro ao ler linhas: {e}")
    
    return True

if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(__file__))
    filograma_path = os.path.join(script_dir, "DAMICORE_Filograma_script.py")
    
    success = check_syntax(filograma_path)
    
    if success:
        print("\n✅ Nenhum erro de sintaxe detectado!")
    else:
        print("\n❌ Erros de sintaxe encontrados!")
    
    # Verificar se há problemas com a execução via subprocess
    print("\nTestando execução via subprocess:")
    import subprocess
    
    try:
        result = subprocess.run(
            ["python3", "-m", "py_compile", filograma_path],
            capture_output=True,
            text=True,
            check=True
        )
        print(f"✅ Compilação via subprocess: OK")
        if result.stdout:
            print(f"Saída: {result.stdout}")
    except subprocess.CalledProcessError as e:
        print(f"❌ Erro na compilação via subprocess:")
        print(f"Código de saída: {e.returncode}")
        print(f"Saída: {e.stdout}")
        print(f"Erro: {e.stderr}")

#!/usr/bin/env python3
"""
Script de teste para verificar se o DAMICORE_Filograma_script.py restaurado não tem erros de sintaxe
"""

import os
import subprocess
import sys

def test_syntax():
    """Testa a sintaxe do DAMICORE_Filograma_script.py"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    filograma_path = os.path.join(script_dir, "DAMICORE_Filograma_script.py")
    
    # Verificar se o script existe
    if not os.path.exists(filograma_path):
        print(f"❌ Script não encontrado: {filograma_path}")
        return False
    
    # Testar sintaxe com python -m py_compile
    print(f"📋 Testando sintaxe do script: {filograma_path}")
    
    cmd = ["python3", "-m", "py_compile", filograma_path]
    print(f"🔧 Comando: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True
        )
        
        # Verificar resultado
        if result.returncode == 0:
            print(f"✅ Sintaxe do script verificada com sucesso")
            return True
        else:
            print(f"❌ Erro de sintaxe no script")
            print("📋 Saída de erro:")
            print(result.stderr)
            return False
    except Exception as e:
        print(f"❌ Erro ao verificar sintaxe: {e}")
        return False

if __name__ == "__main__":
    success = test_syntax()
    
    if success:
        print("\n✅ Teste de sintaxe concluído com sucesso!")
        sys.exit(0)
    else:
        print("\n❌ Teste de sintaxe falhou!")
        sys.exit(1)

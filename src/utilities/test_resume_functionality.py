#!/usr/bin/env python3
"""
Script de teste para validar a funcionalidade de retomada automática do DAMICORE.

Este script testa:
1. Criação de arquivo de progresso
2. Simulação de interrupção
3. Retomada automática do processamento
4. Relatórios de progresso
"""

import os
import sys
import tempfile
import shutil
import pandas as pd
from pathlib import Path

# Adiciona o diretório de scripts ao path
script_dir = Path(__file__).parent
sys.path.append(str(script_dir))

from resume_processor import (
    create_progress_file, 
    update_progress, 
    get_resume_point,
    get_progress_summary,
    mark_pipeline_completed
)


def create_test_csv(file_path, rows=1000, cols=20):
    """Cria um arquivo CSV de teste."""
    print(f"📝 Criando arquivo CSV de teste: {rows} linhas, {cols} colunas")
    
    # Dados simulados
    data = {}
    for i in range(cols):
        data[f'col_{i}'] = [f'value_{i}_{j}' for j in range(rows)]
    
    df = pd.DataFrame(data)
    df.to_csv(file_path, index=False)
    print(f"✅ Arquivo criado: {file_path}")


def test_resume_functionality():
    """Testa a funcionalidade de retomada automática."""
    print("🧪 TESTE DE FUNCIONALIDADE DE RETOMADA AUTOMÁTICA")
    print("=" * 60)
    
    # Cria diretório temporário para teste
    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"📁 Diretório temporário: {temp_dir}")
        
        # Cria arquivo CSV de teste
        csv_file = os.path.join(temp_dir, "test_data.csv")
        create_test_csv(csv_file, rows=500, cols=10)
        
        # Cria diretórios de trabalho
        damicore_dir = os.path.join(temp_dir, "damicore_analysis")
        os.makedirs(damicore_dir, exist_ok=True)
        
        # Teste 1: Criação de arquivo de progresso
        print("\n🔧 TESTE 1: Criação de arquivo de progresso")
        total_chunks = 5
        bootstrap_samples = 3
        
        create_progress_file(damicore_dir, total_chunks, bootstrap_samples)
        
        progress_file = os.path.join(damicore_dir, "pipeline_progress.json")
        if os.path.exists(progress_file):
            print("✅ Arquivo de progresso criado com sucesso")
        else:
            print("❌ Falha ao criar arquivo de progresso")
            return False
        
        # Teste 2: Simulação de progresso parcial
        print("\n🔧 TESTE 2: Simulação de progresso parcial")
        
        # Simula processamento de alguns chunks/amostras
        for chunk_idx in range(2):  # Processa apenas 2 chunks
            for sample_idx in range(bootstrap_samples):
                # Simula sucesso em algumas amostras
                if chunk_idx == 0 or sample_idx < 2:
                    update_progress(damicore_dir, chunk_idx, sample_idx, status="completed")
                else:
                    update_progress(damicore_dir, chunk_idx, sample_idx, status="failed")
        
        # Teste 3: Verificação de resumo de progresso
        print("\n🔧 TESTE 3: Verificação de resumo de progresso")
        summary = get_progress_summary(damicore_dir)
        print(f"📊 {summary}")
        
        # Teste 4: Determinação do ponto de retomada
        print("\n🔧 TESTE 4: Determinação do ponto de retomada")
        resume_chunk, pending_samples = get_resume_point(damicore_dir, total_chunks, bootstrap_samples)
        
        print(f"🔄 Ponto de retomada: chunk {resume_chunk}")
        print(f"🔄 Amostras pendentes por chunk: {len(pending_samples)} chunks com trabalho pendente")
        
        # Mostra detalhes das amostras pendentes
        for chunk_idx, samples in pending_samples.items():
            if samples:
                print(f"   - Chunk {chunk_idx}: amostras {samples}")
        
        # Teste 5: Simulação de retomada e conclusão
        print("\n🔧 TESTE 5: Simulação de retomada e conclusão")
        
        # Completa o processamento pendente
        for chunk_idx, samples in pending_samples.items():
            for sample_idx in samples:
                update_progress(damicore_dir, chunk_idx, sample_idx, status="completed")
                print(f"   ✅ Completado: chunk {chunk_idx}, amostra {sample_idx}")
        
        # Marca pipeline como completado
        mark_pipeline_completed(damicore_dir)
        
        # Teste 6: Verificação final
        print("\n🔧 TESTE 6: Verificação final")
        final_summary = get_progress_summary(damicore_dir)
        print(f"📊 {final_summary}")
        
        # Verifica se não há mais trabalho pendente
        final_resume_chunk, final_pending = get_resume_point(damicore_dir, total_chunks, bootstrap_samples)
        if final_resume_chunk is None:
            print("✅ Nenhum trabalho pendente - pipeline completamente finalizado")
        else:
            print(f"⚠️  Ainda há trabalho pendente no chunk {final_resume_chunk}")
            return False
        
        print("\n🎉 TODOS OS TESTES PASSARAM COM SUCESSO!")
        return True


def test_edge_cases():
    """Testa casos extremos da funcionalidade de retomada."""
    print("\n🧪 TESTE DE CASOS EXTREMOS")
    print("=" * 40)
    
    with tempfile.TemporaryDirectory() as temp_dir:
        damicore_dir = os.path.join(temp_dir, "damicore_analysis")
        os.makedirs(damicore_dir, exist_ok=True)
        
        # Teste: Diretório sem arquivo de progresso
        print("🔧 Teste: Diretório sem arquivo de progresso")
        summary = get_progress_summary(damicore_dir)
        print(f"📊 {summary}")
        
        resume_chunk, pending = get_resume_point(damicore_dir, 2, 2)
        if resume_chunk is not None:  # Deve retornar chunk 0 pois não há progresso
            print("✅ Corretamente detectou ausência de progresso - iniciando do chunk 0")
        else:
            print("❌ Falha ao detectar ausência de progresso")
            return False
        
        # Teste: Pipeline já completado
        print("\n🔧 Teste: Pipeline já completado")
        create_progress_file(damicore_dir, 2, 2)
        
        # Completa todo o trabalho (usando os mesmos parâmetros do teste principal)
        for chunk_idx in range(5):
            for sample_idx in range(3):
                update_progress(damicore_dir, chunk_idx, sample_idx, status="completed")
        
        mark_pipeline_completed(damicore_dir)
        
        summary = get_progress_summary(damicore_dir)
        print(f"📊 {summary}")
        
        resume_chunk, pending = get_resume_point(damicore_dir, 5, 3)
        if resume_chunk is None:
            print("✅ Corretamente detectou pipeline completado")
        else:
            print("❌ Falha ao detectar pipeline completado")
            return False
        
        print("✅ Casos extremos testados com sucesso!")
        return True


def main():
    """Função principal de teste."""
    print("🚀 INICIANDO TESTES DE FUNCIONALIDADE DE RETOMADA AUTOMÁTICA")
    print("=" * 80)
    
    try:
        # Testa funcionalidade básica
        if not test_resume_functionality():
            print("❌ Falha nos testes básicos")
            return 1
        
        # Testa casos extremos
        if not test_edge_cases():
            print("❌ Falha nos testes de casos extremos")
            return 1
        
        print("\n🎉 TODOS OS TESTES CONCLUÍDOS COM SUCESSO!")
        print("✅ A funcionalidade de retomada automática está funcionando corretamente")
        return 0
        
    except Exception as e:
        print(f"❌ Erro durante os testes: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())

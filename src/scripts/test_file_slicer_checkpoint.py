#!/usr/bin/env python3
"""
Test script for DAMICORE File Slicer Processor checkpoint system.
Tests the enhanced checkpoint functionality with adaptive resamples and visualization.
"""

import os
import sys
import tempfile
import shutil
import pandas as pd
import numpy as np
from pathlib import Path

# Add the scripts directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from DAMICORE_File_Slicer_Processor import FileSlicerProgress, calculate_adaptive_resamples


def create_test_csv(file_path, num_rows=250, num_cols=10):
    """Create a test CSV file with random data."""
    print(f"📝 Criando arquivo de teste: {num_rows} linhas, {num_cols} colunas")
    
    # Generate random data
    np.random.seed(42)  # For reproducible results
    data = np.random.rand(num_rows, num_cols)
    
    # Create column names
    columns = [f'var_{i+1}' for i in range(num_cols)]
    
    # Create DataFrame and save
    df = pd.DataFrame(data, columns=columns)
    df.to_csv(file_path, index=False)
    
    print(f"✅ Arquivo criado: {file_path}")
    return file_path


def test_checkpoint_initialization():
    """Test checkpoint system initialization."""
    print("\n" + "="*60)
    print("🧪 TESTE 1: Inicialização do Sistema de Checkpoint")
    print("="*60)
    
    with tempfile.TemporaryDirectory() as temp_dir:
        progress_file = os.path.join(temp_dir, "test_progress.json")
        
        # Initialize progress manager
        progress_manager = FileSlicerProgress(progress_file)
        
        # Test initialization
        total_slices = 5
        adaptive_resamples = calculate_adaptive_resamples(total_slices)
        progress_manager.initialize_progress(total_slices, "test.csv", adaptive_resamples)
        
        # Verify initialization
        assert progress_manager.progress_data['total_slices'] == total_slices
        assert progress_manager.progress_data['adaptive_resamples'] == adaptive_resamples
        assert progress_manager.progress_data['original_file'] == "test.csv"
        assert 'completed_slices' in progress_manager.progress_data
        assert 'failed_slices' in progress_manager.progress_data
        
        print(f"✅ Checkpoint inicializado: {total_slices} fatias, {adaptive_resamples} resamples")
        print(f"✅ Arquivo de progresso criado: {progress_file}")
        
        return True


def test_slice_processing_simulation():
    """Test slice processing with checkpoint updates."""
    print("\n" + "="*60)
    print("🧪 TESTE 2: Simulação de Processamento com Checkpoint")
    print("="*60)
    
    with tempfile.TemporaryDirectory() as temp_dir:
        progress_file = os.path.join(temp_dir, "test_progress.json")
        
        # Initialize progress manager
        progress_manager = FileSlicerProgress(progress_file)
        total_slices = 3
        adaptive_resamples = calculate_adaptive_resamples(total_slices)
        progress_manager.initialize_progress(total_slices, "test.csv", adaptive_resamples)
        
        # Simulate processing slices
        print("🔄 Simulando processamento de fatias...")
        
        # Process slice 0 successfully
        progress_manager.mark_slice_started(0)
        newick_files = ["slice_0_resample_00.newick", "slice_0_resample_01.newick"]
        progress_manager.mark_slice_completed(0, newick_files)
        print("✅ Fatia 0: processada com sucesso")
        
        # Process slice 1 with failure
        progress_manager.mark_slice_started(1)
        progress_manager.mark_slice_failed(1, "Erro de teste simulado")
        print("❌ Fatia 1: falhou (simulado)")
        
        # Check pending slices
        pending = progress_manager.get_pending_slices()
        failed = progress_manager.get_failed_slices()
        assert 0 not in pending  # Completed
        assert 1 in failed       # Failed (in failed list)
        assert 2 in pending      # Not started
        
        print(f"📊 Fatias pendentes: {pending}")
        print(f"📊 Fatias falhadas: {failed}")
        
        # Test retry functionality
        progress_manager.retry_failed_slices()
        pending_after_retry = progress_manager.get_pending_slices()
        failed_after_retry = progress_manager.get_failed_slices()
        assert 1 in pending_after_retry  # Should be pending after retry
        assert len(failed_after_retry) == 0  # Failed list should be cleared
        
        print("🔄 Retry de fatias falhadas: OK")
        
        # Complete remaining slices
        progress_manager.mark_slice_started(1)
        progress_manager.mark_slice_completed(1, ["slice_1_resample_00.newick"])
        
        progress_manager.mark_slice_started(2)
        progress_manager.mark_slice_completed(2, ["slice_2_resample_00.newick"])
        
        # Mark pipeline as completed
        progress_manager.mark_pipeline_completed()
        
        # Verify completion
        final_pending = progress_manager.get_pending_slices()
        assert len(final_pending) == 0
        assert progress_manager.progress_data.get('status') == 'completed'
        
        print("✅ Pipeline marcado como concluído")
        
        return True


def test_adaptive_resamples_calculation():
    """Test adaptive resamples calculation for different slice counts."""
    print("\n" + "="*60)
    print("🧪 TESTE 3: Cálculo de Resamples Adaptativos")
    print("="*60)
    
    test_cases = [
        (1, 23),    # 1 slice -> 23 resamples
        (5, 20),    # 5 slices -> 20 resamples
        (10, 15),   # 10 slices -> 15 resamples
        (20, 10),   # 20 slices -> 10 resamples
        (50, 7),    # 50 slices -> 7 resamples
        (100, 5),   # 100 slices -> 5 resamples
        (200, 3),   # 200 slices -> 3 resamples
    ]
    
    for num_slices, expected_resamples in test_cases:
        actual_resamples = calculate_adaptive_resamples(num_slices)
        assert actual_resamples == expected_resamples, f"Falha: {num_slices} fatias -> {actual_resamples} (esperado: {expected_resamples})"
        print(f"✅ {num_slices:3d} fatias -> {actual_resamples:2d} resamples")
    
    return True


def test_progress_summary():
    """Test progress summary generation."""
    print("\n" + "="*60)
    print("🧪 TESTE 4: Geração de Resumo de Progresso")
    print("="*60)
    
    with tempfile.TemporaryDirectory() as temp_dir:
        progress_file = os.path.join(temp_dir, "test_progress.json")
        
        # Initialize and simulate some progress
        progress_manager = FileSlicerProgress(progress_file)
        total_slices = 4
        adaptive_resamples = calculate_adaptive_resamples(total_slices)
        progress_manager.initialize_progress(total_slices, "test.csv", adaptive_resamples)
        
        # Complete some slices
        progress_manager.mark_slice_completed(0, ["file1.newick", "file2.newick"])
        progress_manager.mark_slice_completed(1, ["file3.newick"])
        progress_manager.mark_slice_failed(2, "Erro de teste")
        
        # Get summary
        summary = progress_manager.get_progress_summary()
        
        # Verify summary
        assert summary['total'] == 4
        assert summary['completed'] == 2
        assert summary['failed'] == 1
        assert summary['pending'] == 1
        assert summary['completion_rate'] == 50.0
        
        print(f"✅ Resumo gerado corretamente:")
        print(f"   📊 Total: {summary['total']}")
        print(f"   ✅ Concluídas: {summary['completed']}")
        print(f"   ❌ Falhadas: {summary['failed']}")
        print(f"   ⏳ Pendentes: {summary['pending']}")
        print(f"   📈 Taxa de conclusão: {summary['completion_rate']:.1f}%")
        
        return True


def test_backup_and_recovery():
    """Test backup file creation and recovery."""
    print("\n" + "="*60)
    print("🧪 TESTE 5: Backup e Recuperação")
    print("="*60)
    
    with tempfile.TemporaryDirectory() as temp_dir:
        progress_file = os.path.join(temp_dir, "test_progress.json")
        backup_file = progress_file + ".backup"
        
        # Initialize progress manager
        progress_manager = FileSlicerProgress(progress_file)
        progress_manager.initialize_progress(2, "test.csv", 10)
        
        # Make a change to trigger backup creation
        progress_manager.mark_slice_completed(0, ["test1.newick", "test2.newick"])
        
        # Verify backup was created
        assert os.path.exists(backup_file), "Arquivo de backup não foi criado"
        print("✅ Arquivo de backup criado")
        
        # Simulate corruption of main file
        with open(progress_file, 'w') as f:
            f.write("invalid json")
        
        # Create new progress manager (should recover from backup)
        progress_manager2 = FileSlicerProgress(progress_file)
        
        # Verify recovery
        assert progress_manager2.progress_data['total_slices'] == 2
        assert progress_manager2.progress_data['original_file'] == "test.csv"
        
        print("✅ Recuperação do backup funcionou corretamente")
        
        return True


def run_all_tests():
    """Run all checkpoint system tests."""
    print("🚀 INICIANDO TESTES DO SISTEMA DE CHECKPOINT")
    print("="*80)
    
    tests = [
        ("Inicialização", test_checkpoint_initialization),
        ("Processamento com Checkpoint", test_slice_processing_simulation),
        ("Resamples Adaptativos", test_adaptive_resamples_calculation),
        ("Resumo de Progresso", test_progress_summary),
        ("Backup e Recuperação", test_backup_and_recovery),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, "✅ PASSOU", None))
        except Exception as e:
            results.append((test_name, "❌ FALHOU", str(e)))
    
    # Print results summary
    print("\n" + "="*80)
    print("📊 RESUMO DOS TESTES")
    print("="*80)
    
    passed = 0
    failed = 0
    
    for test_name, status, error in results:
        print(f"{status} {test_name}")
        if error:
            print(f"    Erro: {error}")
        
        if "PASSOU" in status:
            passed += 1
        else:
            failed += 1
    
    print("="*80)
    print(f"🎯 RESULTADO FINAL: {passed} passou, {failed} falhou")
    
    if failed == 0:
        print("🎉 TODOS OS TESTES PASSARAM! Sistema de checkpoint está funcionando corretamente.")
        return True
    else:
        print("⚠️  Alguns testes falharam. Verifique os erros acima.")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)

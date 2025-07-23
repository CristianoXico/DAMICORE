#!/usr/bin/env python3
"""
Test script for external drive integration in DAMICORE File Slicer Processor.
Tests the external drive detection, configuration, and output directory functions.
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

import DAMICORE_File_Slicer_Processor as slicer_module
from DAMICORE_File_Slicer_Processor import (
    detect_external_drive, 
    get_output_directory
)


def create_test_csv(file_path, num_rows=50, num_cols=5):
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


def test_external_drive_detection():
    """Test external drive detection functionality."""
    print("\n" + "="*60)
    print("🧪 TESTE 1: Detecção de Drive Externo")
    print("="*60)
    
    # Test detection function
    detected_drive = detect_external_drive()
    
    if detected_drive:
        print(f"✅ Drive externo detectado: {detected_drive}")
        
        # Verify the detected path exists and is writable
        if os.path.exists(detected_drive) and os.path.isdir(detected_drive):
            print(f"✅ Caminho válido: {detected_drive}")
            
            # Test write permission
            test_file = os.path.join(detected_drive, "test_write_permission.tmp")
            try:
                with open(test_file, 'w') as f:
                    f.write("test")
                os.remove(test_file)
                print("✅ Permissão de escrita: OK")
                return True, detected_drive
            except Exception as e:
                print(f"❌ Erro de permissão de escrita: {e}")
                return False, detected_drive
        else:
            print(f"❌ Caminho inválido: {detected_drive}")
            return False, detected_drive
    else:
        print("ℹ️  Nenhum drive externo detectado automaticamente")
        return False, None


def test_output_directory_local():
    """Test output directory generation for local storage."""
    print("\n" + "="*60)
    print("🧪 TESTE 2: Diretório de Saída (Local)")
    print("="*60)
    
    # Create a temporary CSV file
    with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as tmp_file:
        test_csv = tmp_file.name
    
    try:
        create_test_csv(test_csv)
        
        # Test with local storage (global variables should be False/None by default)
        original_use_external = slicer_module.USE_EXTERNAL_DRIVE
        original_external_path = slicer_module.EXTERNAL_DRIVE_PATH
        
        # Force local storage
        slicer_module.USE_EXTERNAL_DRIVE = False
        slicer_module.EXTERNAL_DRIVE_PATH = None
        
        output_dir = get_output_directory(test_csv)
        
        # Verify output directory structure
        expected_base = os.path.dirname(os.path.abspath(test_csv))
        csv_basename = os.path.splitext(os.path.basename(test_csv))[0]
        expected_dir = os.path.join(expected_base, f"{csv_basename}_sliced_results")
        
        assert output_dir == expected_dir, f"Esperado: {expected_dir}, Obtido: {output_dir}"
        
        print(f"✅ Diretório local gerado corretamente: {output_dir}")
        
        # Restore original values
        slicer_module.USE_EXTERNAL_DRIVE = original_use_external
        slicer_module.EXTERNAL_DRIVE_PATH = original_external_path
        
        return True
        
    finally:
        # Cleanup
        if os.path.exists(test_csv):
            os.remove(test_csv)


def test_output_directory_external():
    """Test output directory generation for external storage."""
    print("\n" + "="*60)
    print("🧪 TESTE 3: Diretório de Saída (Drive Externo)")
    print("="*60)
    
    # Create a temporary CSV file
    with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as tmp_file:
        test_csv = tmp_file.name
    
    # Create a temporary directory to simulate external drive
    with tempfile.TemporaryDirectory() as temp_external_dir:
        try:
            create_test_csv(test_csv)
            
            # Test with external storage
            original_use_external = slicer_module.USE_EXTERNAL_DRIVE
            original_external_path = slicer_module.EXTERNAL_DRIVE_PATH
            
            # Force external storage
            slicer_module.USE_EXTERNAL_DRIVE = True
            slicer_module.EXTERNAL_DRIVE_PATH = temp_external_dir
            
            output_dir = get_output_directory(test_csv)
            
            # Verify output directory structure
            csv_basename = os.path.splitext(os.path.basename(test_csv))[0]
            expected_dir = os.path.join(temp_external_dir, "DAMICORE_RESULTS", f"{csv_basename}_sliced_results")
            
            assert output_dir == expected_dir, f"Esperado: {expected_dir}, Obtido: {output_dir}"
            
            print(f"✅ Diretório externo gerado corretamente: {output_dir}")
            
            # Restore original values
            slicer_module.USE_EXTERNAL_DRIVE = original_use_external
            slicer_module.EXTERNAL_DRIVE_PATH = original_external_path
            
            return True
            
        finally:
            # Cleanup
            if os.path.exists(test_csv):
                os.remove(test_csv)


def test_directory_creation():
    """Test actual directory creation with both local and external paths."""
    print("\n" + "="*60)
    print("🧪 TESTE 4: Criação de Diretórios")
    print("="*60)
    
    # Create a temporary CSV file
    with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as tmp_file:
        test_csv = tmp_file.name
    
    try:
        create_test_csv(test_csv)
        
        # Test local directory creation
        slicer_module.USE_EXTERNAL_DRIVE = False
        slicer_module.EXTERNAL_DRIVE_PATH = None
        
        local_output_dir = get_output_directory(test_csv)
        os.makedirs(local_output_dir, exist_ok=True)
        
        assert os.path.exists(local_output_dir), f"Diretório local não foi criado: {local_output_dir}"
        print(f"✅ Diretório local criado: {local_output_dir}")
        
        # Test external directory creation
        with tempfile.TemporaryDirectory() as temp_external_dir:
            USE_EXTERNAL_DRIVE = True
            EXTERNAL_DRIVE_PATH = temp_external_dir
            
            external_output_dir = get_output_directory(test_csv)
            os.makedirs(external_output_dir, exist_ok=True)
            
            assert os.path.exists(external_output_dir), f"Diretório externo não foi criado: {external_output_dir}"
            print(f"✅ Diretório externo criado: {external_output_dir}")
        
        # Cleanup local directory
        if os.path.exists(local_output_dir):
            shutil.rmtree(local_output_dir)
        
        return True
        
    finally:
        # Cleanup
        if os.path.exists(test_csv):
            os.remove(test_csv)


def test_space_calculation():
    """Test space calculation for external drives."""
    print("\n" + "="*60)
    print("🧪 TESTE 5: Cálculo de Espaço Disponível")
    print("="*60)
    
    # Test with current directory (should always work)
    current_dir = os.getcwd()
    
    try:
        statvfs = os.statvfs(current_dir)
        free_space_gb = (statvfs.f_frsize * statvfs.f_bavail) / (1024**3)
        
        print(f"✅ Espaço livre em {current_dir}: {free_space_gb:.1f} GB")
        
        # Verify the calculation makes sense (should be positive)
        assert free_space_gb > 0, "Espaço livre deve ser positivo"
        
        return True
        
    except Exception as e:
        print(f"❌ Erro ao calcular espaço: {e}")
        return False


def run_all_tests():
    """Run all external drive integration tests."""
    print("🚀 INICIANDO TESTES DE INTEGRAÇÃO DE DRIVE EXTERNO")
    print("="*80)
    
    tests = [
        ("Detecção de Drive Externo", test_external_drive_detection),
        ("Diretório Local", test_output_directory_local),
        ("Diretório Externo", test_output_directory_external),
        ("Criação de Diretórios", test_directory_creation),
        ("Cálculo de Espaço", test_space_calculation),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            if isinstance(result, tuple):
                # For external drive detection which returns (success, path)
                success, extra_info = result
                results.append((test_name, "✅ PASSOU" if success else "ℹ️  INFO", extra_info))
            else:
                results.append((test_name, "✅ PASSOU" if result else "❌ FALHOU", None))
        except Exception as e:
            results.append((test_name, "❌ FALHOU", str(e)))
    
    # Print results summary
    print("\n" + "="*80)
    print("📊 RESUMO DOS TESTES")
    print("="*80)
    
    passed = 0
    failed = 0
    info = 0
    
    for test_name, status, error in results:
        print(f"{status} {test_name}")
        if error and "FALHOU" in status:
            print(f"    Erro: {error}")
        elif error and "INFO" in status:
            print(f"    Info: {error}")
        
        if "PASSOU" in status:
            passed += 1
        elif "FALHOU" in status:
            failed += 1
        else:
            info += 1
    
    print("="*80)
    print(f"🎯 RESULTADO FINAL: {passed} passou, {failed} falhou, {info} informativos")
    
    if failed == 0:
        print("🎉 TODOS OS TESTES CRÍTICOS PASSARAM! Integração de drive externo está funcionando.")
        return True
    else:
        print("⚠️  Alguns testes falharam. Verifique os erros acima.")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)

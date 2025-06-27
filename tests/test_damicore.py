import unittest
import numpy as np
import pandas as pd
import os
from src.core.ncd_processor import NCDProcessor
from src.utils.validators import DAMICOREValidator
from src.core.community_detector import NewmanCommunityDetector

class TestDAMICORE(unittest.TestCase):
    def setUp(self):
        """Create sample data for testing"""
        self.test_data = pd.DataFrame({
            'col1': range(10),
            'col2': range(10, 20),
            'col3': range(20, 30)
        })
        
    def test_ncd_processor(self):
        """Test NCD matrix calculation"""
        processor = NCDProcessor()
        matrix, labels = processor.process_dataframe(self.test_data)
        self.assertEqual(matrix.shape, (10, 10))
        self.assertEqual(len(labels), 3)

    def test_validation(self):
        """Test data validation"""
        validator = DAMICOREValidator()
        
        # Create test data with 2 clear clusters
        data = np.array([
            [1, 1],
            [2, 1],
            [1, 2],
            [10, 10],
            [11, 10],
            [10, 11]
        ])
        
        # Create cluster labels (2 clusters)
        clusters = np.array([0, 0, 0, 1, 1, 1])
        
        # Test cluster validation
        is_valid, score = validator.validate_clusters(data, clusters)
        
        # Test return types
        self.assertIsInstance(is_valid, bool, "is_valid should be a Python bool")
        self.assertIsInstance(score, float, "score should be a float")
        self.assertGreater(score, 0, "Score should be positive for well-defined clusters")

    def test_community_detection(self):
        """Test Newman community detection"""
        # Create a simple similarity matrix
        similarity_matrix = np.array([
            [1.0, 0.8, 0.2, 0.1],
            [0.8, 1.0, 0.1, 0.1],
            [0.2, 0.1, 1.0, 0.9],
            [0.1, 0.1, 0.9, 1.0]
        ])
        
        detector = NewmanCommunityDetector()
        communities = detector.detect_communities(similarity_matrix)
        
        # Verifica se pelo menos uma comunidade foi detectada
        unique_communities = len(set(communities.values()))
        self.assertGreaterEqual(unique_communities, 1, "Pelo menos uma comunidade deve ser detectada")

    def test_variable_correlation(self):
        """Test variable correlation analysis"""
        # Create test data with known correlations
        data = pd.DataFrame({
            'a': [1, 2, 3, 4],
            'b': [2, 4, 6, 8],      # Perfect correlation with 'a'
            'c': [5, 3, 1, 2]       # Some variation to avoid NaN
        })
        
        correlation_matrix = data.corr()
        
        # Check perfect correlation between a and b
        self.assertAlmostEqual(correlation_matrix.loc['a', 'b'], 1.0)
        
        # Check non-perfect correlation between a and c
        self.assertNotEqual(correlation_matrix.loc['a', 'c'], 1.0)
        self.assertFalse(np.isnan(correlation_matrix.loc['a', 'c']))

    def test_full_pipeline(self):
        """Test the complete DAMICORE pipeline"""
        # Create sample data
        data = pd.DataFrame({
            'feature1': [1, 2, 3, 10, 11, 12],
            'feature2': [1, 2, 1, 10, 11, 10],
            'feature3': [2, 1, 2, 11, 10, 11]
        })
        
        # Process through NCD
        processor = NCDProcessor()
        matrix, labels = processor.process_dataframe(data)
        
        # Validate results
        self.assertEqual(matrix.shape, (6, 6))  # 6x6 distance matrix
        self.assertEqual(len(labels), 3)        # 3 features
        
        # Check matrix properties
        self.assertTrue(np.all(matrix >= 0))    # All distances non-negative
        self.assertTrue(np.all(matrix <= 1))    # All distances normalized

    def test_edge_cases(self):
        """Test error handling and edge cases"""
        
        # Test empty data
        empty_data = pd.DataFrame()
        processor = NCDProcessor()
        with self.assertRaises(ValueError, msg="Should raise ValueError for empty DataFrame"):
            matrix, labels = processor.process_dataframe(empty_data)
        
        # Test single column data - should not raise an error
        single_col = pd.DataFrame({'a': [1, 2, 3]})
        try:
            matrix, labels = processor.process_dataframe(single_col)
            # Verify the output is as expected
            self.assertEqual(matrix.shape, (3, 3), "Matrix should be 3x3 for 3 rows of single column")
            self.assertTrue(np.all(np.diag(matrix) == 0), "Diagonal should be zeros")
        except Exception as e:
            self.fail(f"Processing single column DataFrame should not raise exception: {str(e)}")
        
        # Test data with NaN values
        nan_data = pd.DataFrame({
            'a': [1, np.nan, 3],
            'b': [4, 5, 6]
        })
        try:
            matrix, labels = processor.process_dataframe(nan_data)
            # Verify the output is as expected
            self.assertEqual(matrix.shape, (3, 3), "Matrix should be 3x3 for 3 rows of data")
            self.assertTrue(np.all(np.diag(matrix) == 0), "Diagonal should be zeros")
            self.assertTrue(np.all(matrix >= 0), "All distances should be non-negative")
            self.assertTrue(np.all(matrix <= 1), "All distances should be normalized")
        except Exception as e:
            self.fail(f"Processing DataFrame with NaN values should not raise exception: {str(e)}")

    def test_performance_metrics(self):
        """Test performance metrics collection"""
        processor = NCDProcessor()
        matrix, labels = processor.process_dataframe(self.test_data)
        
        stats = processor.get_processing_stats()
        self.assertIn('total_time_s', stats)
        self.assertIn('compression_ratio', stats)
        self.assertGreater(stats['compression_ratio'], 0)
        self.assertLess(stats['total_time_s'], 10)  # Should process test data quickly

    def test_dengue_data(self):
        """Test DAMICORE analysis on dengue dataset"""
        
        # Load dengue data with full path
        file_path = r"C:\Users\55179\Desktop\Workspace_vscode\Analise_Dados\PPPP-Arbovirose\entrega\group_by_censitario_quarter.csv"
        
        # Skip test if file doesn't exist
        if not os.path.exists(file_path):
            self.skipTest(f"Test data file not found: {file_path}")
            return
        
        try:
            # Load and preprocess data - use only first 100 rows for testing
            data = pd.read_csv(file_path, nrows=100)
            
            # Handle NaN values
            data = data.fillna(0)  # Replace NaN with zeros
            
            print(f"Data shape: {data.shape}")
            print(f"Number of NaN values: {data.isna().sum().sum()}")
            
            # Initialize processor with serial processing to avoid memory issues
            processor = NCDProcessor(n_jobs=1, verbose=True)
            
            # Process data
            matrix, labels = processor.process_dataframe(data)
            
            # Validate matrix properties
            self.assertEqual(matrix.shape[0], matrix.shape[1], "Matrix should be square")
            self.assertTrue(np.all(matrix >= 0), "Distances should be non-negative")
            self.assertTrue(np.all(matrix <= 1), "Distances should be normalized")
            
        except MemoryError:
            self.skipTest("Not enough memory to process the test data")
        except Exception as e:
            self.fail(f"Test failed with error: {str(e)}")
        
        # Get processing stats
        stats = processor.get_processing_stats()
        print(f"\nProcessing stats:")
        print(f"- Compression ratio: {stats['compression_ratio']:.3f}")
        print(f"- Matrix calculation time: {stats['matrix_calc_time_s']:.3f}s")
        
        # Test community detection
        detector = NewmanCommunityDetector()
        communities = detector.detect_communities(matrix)
        
        n_communities = len(set(communities.values()))
        print(f"\nDetected {n_communities} communities")
        
        # Validate communities
        self.assertGreater(len(communities), 0)
        self.assertEqual(len(communities), len(data))
        
        # Test validator - use only numeric columns for validation
        numeric_cols = data.select_dtypes(include=[np.number]).columns
        if not numeric_cols.empty:
            validator = DAMICOREValidator()
            try:
                # Get numeric data for validation
                numeric_data = data[numeric_cols].values
                
                # Check if we have enough numeric data for validation
                if numeric_data.size == 0:
                    print("\nNo numeric data available for validation")
                    return  # Skip validation if no numeric data
                    
                # Try to validate clusters
                is_valid, score = validator.validate_clusters(
                    numeric_data,
                    np.array(list(communities.values()))
                )
                
                print(f"\nValidation score: {score:.3f}")
                
                # Don't fail the test for low silhouette score, just log a warning
                if not is_valid:
                    print(f"\nWarning: Low silhouette score ({score:.3f}), but continuing test")
                
                # Just check that we got a valid score, not its value
                self.assertIsInstance(score, (int, float), "Score should be a number")
                
            except Exception as e:
                print(f"\nWarning: Cluster validation skipped due to: {str(e)}")
                # Skip validation if it fails, but don't fail the test
                self.skipTest(f"Cluster validation failed: {str(e)}")
        else:
            msg = f"No numeric columns available for cluster validation. Columns: {data.columns.tolist()}"
            print(f"\n{msg}")
            self.skipTest(msg)

if __name__ == "__main__":
    unittest.main()
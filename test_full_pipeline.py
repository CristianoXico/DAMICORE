import pandas as pd
from pathlib import Path
from src.preprocessing.data_processor import DataProcessor
from src.analysis.ncd_calculator import NCDCalculator
from src.analysis.tree_builder import TreeBuilder
from src.visualization.tree_visualizer import TreeVisualizer

def test_pipeline():
    """Test full DAMICORE pipeline with sample dengue data"""
    
    # Setup paths
    data_path = Path("data/sample_dengue.csv")
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    
    print("\n=== Running DAMICORE Pipeline ===")
    
    # 1. Load and preprocess data
    print("\nLoading data...")
    data = pd.read_csv(data_path)
    processor = DataProcessor()
    processed_data = processor.preprocess(data)
    print(f"Processed {len(processed_data)} samples")
    
    # 2. Calculate NCD matrix
    print("\nCalculating NCD matrix...")
    calculator = NCDCalculator()
    distance_matrix = calculator.calculate_matrix(processed_data)
    print(f"Generated {distance_matrix.shape[0]}x{distance_matrix.shape[1]} distance matrix")
    
    # 3. Build phylogenetic trees
    print("\nBuilding phylogenetic trees...")
    builder = TreeBuilder()
    trees = builder.build_trees(distance_matrix)
    print(f"Generated {len(trees)} trees")
    
    # 4. Visualize results
    print("\nGenerating visualizations...")
    visualizer = TreeVisualizer()
    visualizer.load_newick_trees(trees)
    
    # Create and save cloud tree
    cloud_tree = visualizer.draw_cloud_tree()
    visualizer.save_visualization(cloud_tree, output_dir / "cloud_tree.svg")
    
    # Create and save consensus tree
    visualizer.create_consensus_tree()
    consensus_tree = visualizer.draw_consensus_tree()
    visualizer.save_visualization(consensus_tree, output_dir / "consensus_tree.svg")
    
    print("\nPipeline completed successfully!")
    print(f"Output files saved to: {output_dir.absolute()}")

if __name__ == "__main__":
    test_pipeline()
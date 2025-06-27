# Contents of `README.md`

# DAMICORE Project

## Overview
DAMICORE is a data processing pipeline designed for handling large datasets efficiently. It utilizes advanced algorithms for data analysis and community detection, and includes a visualization module for tree structures.

## Features
- **Data Processing**: Efficiently processes large CSV files using the Normalized Compression Distance (NCD) method.
- **Community Detection**: Identifies communities within the data using the Newman method.
- **Tree Visualizations**: Provides functionalities for visualizing tree structures, including:
  - Cloud tree visualizations
  - Consensus trees
  - Tree plots with colored labels
  - Rooting and modifying trees

## Installation
To install the required libraries, run:

```
pip install -r requirements.txt
```

## Usage
To run the DAMICORE pipeline, use the following command:

```
python main.py <input_file.csv> [--chunk-size <size>] [--output-dir <directory>]
```

Replace `<input_file.csv>` with the path to your input CSV file. You can also specify optional parameters for chunk size and output directory.

## Visualization Module
The visualization module includes the following files:
- `tree_visualizer.py`: Functions and classes for visualizing trees.
- `cloud_tree.py`: Functions for creating cloud tree visualizations.
- `consensus_tree.py`: Methods for creating consensus trees from multiple inputs.
- `tree_utils.py`: Utility functions for rooting and modifying trees.

## Contributing
Contributions are welcome! Please submit a pull request or open an issue for any enhancements or bug fixes.

## License
This project is licensed under the MIT License. See the LICENSE file for details.
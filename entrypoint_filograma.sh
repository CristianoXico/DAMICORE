#!/bin/bash
set -e

# Set PATH to include user's local binaries
export PATH="/home/damicore/.local/bin:${PATH}"

# Check if pandas is installed
if ! python -c "import pandas" &> /dev/null; then
    echo "Pandas not found. Installing dependencies..."
    pip install --user --no-cache-dir -r /app/requirements.txt
fi

# Create results directory if it doesn't exist
mkdir -p /app/results

# Create data directory if it doesn't exist
mkdir -p /app/data

# Find all CSV files in the data directory and process them
find /app/data -maxdepth 1 -name "*.csv" -type f | while read -r csv_file; do
    filename=$(basename -- "$csv_file")
    base_filename="${filename%.*}"
    output_dir="/app/results/${base_filename}_results"
    
    echo "Processing file: $filename"
    echo "Output will be saved to: $output_dir"
    
    # Create output directory
    mkdir -p "$output_dir"
    
    # Run DAMICORE_Filograma_script.py with the CSV file
    python /app/src/scripts/DAMICORE_Filograma_script.py \
        --input "$csv_file" \
        --output "$output_dir" \
        || echo "Warning: Failed to process $filename"
    
    echo "Completed processing: $filename"
    echo "----------------------------------------"
done

echo "All CSV files have been processed. Results are available in the /app/results directory."

# Keep the container running if needed
# tail -f /dev/null

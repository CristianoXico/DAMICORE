"""
Enhanced CheckpointManager for DAMICORE Pipeline

Provides robust checkpointing and recovery for all pipeline stages with:
- Atomic operations with backup system
- Detailed progress tracking
- Automatic recovery from failures
- Resource usage monitoring
- Validation of checkpoints
"""

import os
import json
import time
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
import psutil
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('damicore_checkpoint.log'),
        logging.StreamHandler()
    ]
)

class CheckpointManager:
    """
    Enhanced checkpoint manager for DAMICORE pipeline with atomic operations and validation.
    """
    
    def __init__(self, output_dir: str):
        """
        Initialize CheckpointManager with output directory.
        
        Args:
            output_dir: Base directory for storing checkpoints and results
        """
        self.output_dir = Path(output_dir)
        self.checkpoint_file = self.output_dir / "damicore_checkpoint.json"
        self.backup_file = self.checkpoint_file.with_suffix('.json.bak')
        self.progress = self._load_or_initialize_checkpoint()
        
        # Ensure output directory exists
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize resource tracking
        self._start_time = time.time()
        self._peak_memory = psutil.Process().memory_info().rss / (1024 * 1024)  # MB
    
    def _load_or_initialize_checkpoint(self) -> Dict[str, Any]:
        """Load existing checkpoint or initialize a new one."""
        # Try to load from primary file
        if self.checkpoint_file.exists():
            try:
                with open(self.checkpoint_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                logging.info(f"✅ Loaded checkpoint from {self.checkpoint_file}")
                return self._upgrade_checkpoint_format(data)
            except Exception as e:
                logging.warning(f"⚠️  Failed to load checkpoint: {e}")
                # Try backup file
                if self.backup_file.exists():
                    try:
                        shutil.copy2(self.backup_file, self.checkpoint_file)
                        with open(self.checkpoint_file, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                        logging.info(f"✅ Loaded checkpoint from backup {self.backup_file}")
                        return self._upgrade_checkpoint_format(data)
                    except Exception as e2:
                        logging.error(f"⚠️  Failed to load backup checkpoint: {e2}")
        
        # Initialize new checkpoint
        return self._initialize_new_checkpoint()
    
    def _initialize_new_checkpoint(self) -> Dict[str, Any]:
        """Initialize a new checkpoint with default values."""
        return {
            "metadata": {
                "version": "1.2.0",
                "created_at": datetime.now().isoformat(),
                "pipeline_version": "DAMICORE-2.0",
            },
            "execution": {
                "start_time": datetime.now().isoformat(),
                "last_updated": None,
                "status": "initialized",
                "current_stage": None,
                "total_stages": 6,  # Will be updated based on actual pipeline
            },
            "stages": {
                "data_loading": {
                    "status": "pending",
                    "start_time": None,
                    "end_time": None,
                    "metrics": {}
                },
                "preprocessing": {
                    "status": "pending",
                    "start_time": None,
                    "end_time": None,
                    "metrics": {}
                },
                "bootstrap_sampling": {
                    "status": "pending",
                    "start_time": None,
                    "end_time": None,
                    "metrics": {
                        "total_samples": 0,
                        "completed_samples": 0,
                        "failed_samples": 0,
                        "samples": {}
                    }
                },
                "damicore_processing": {
                    "status": "pending",
                    "start_time": None,
                    "end_time": None,
                    "metrics": {
                        "total_trees": 0,
                        "completed_trees": 0,
                        "failed_trees": 0,
                        "trees": {}
                    }
                },
                "visualization": {
                    "status": "pending",
                    "start_time": None,
                    "end_time": None,
                    "metrics": {
                        "generated_visualizations": []
                    }
                },
                "post_processing": {
                    "status": "pending",
                    "start_time": None,
                    "end_time": None,
                    "metrics": {}
                }
            },
            "resources": {
                "peak_memory_mb": 0.0,
                "total_runtime_seconds": 0.0,
                "last_checkpoint_time": None,
                "checkpoint_count": 0
            },
            "files": {
                "input": None,
                "output_dir": str(self.output_dir),
                "temporary_files": [],
                "generated_files": []
            },
            "errors": []
        }
    
    def _upgrade_checkpoint_format(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Upgrade checkpoint format if needed."""
        # Add version if missing (pre-1.0.0 checkpoints)
        if "metadata" not in data:
            data = {"metadata": {"version": "0.9.0"}, **data}
        
        # Upgrade from 0.9.0 to 1.0.0
        if data["metadata"].get("version") == "0.9.0":
            # Migrate old format to new format
            data["metadata"]["version"] = "1.0.0"
            data["stages"] = {
                "data_loading": {
                    "status": data.get("completed_steps", {}).get("data_loading", False) and "completed" or "pending",
                    "start_time": data.get("start_time"),
                    "end_time": None,
                    "metrics": {}
                },
                # ... other stages
            }
            
        # Add any new fields in future versions
        if data["metadata"].get("version") == "1.0.0":
            data["metadata"]["version"] = "1.1.0"
            data["resources"] = data.get("resources", {
                "peak_memory_mb": 0.0,
                "total_runtime_seconds": 0.0,
                "last_checkpoint_time": None,
                "checkpoint_count": 0
            })
        
        return data
    
    def _update_resources(self):
        """Update resource usage metrics."""
        # Update memory usage
        current_mem = psutil.Process().memory_info().rss / (1024 * 1024)  # MB
        self._peak_memory = max(self._peak_memory, current_mem)
        self.progress["resources"]["peak_memory_mb"] = self._peak_memory
        
        # Update runtime
        self.progress["resources"]["total_runtime_seconds"] = time.time() - self._start_time
        self.progress["resources"]["last_checkpoint_time"] = datetime.now().isoformat()
        self.progress["resources"]["checkpoint_count"] += 1
    
    def save(self) -> bool:
        """
        Save checkpoint with atomic write and backup.
        
        Returns:
            bool: True if save was successful, False otherwise
        """
        try:
            # Update resource usage before saving
            self._update_resources()
            
            # Create a temporary file
            temp_file = self.checkpoint_file.with_suffix('.tmp')
            
            # Write to temporary file
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(self.progress, f, indent=2, ensure_ascii=False)
            
            # Create backup of existing file if it exists
            if self.checkpoint_file.exists():
                shutil.copy2(self.checkpoint_file, self.backup_file)
            
            # Atomic rename
            temp_file.replace(self.checkpoint_file)
            
            logging.debug(f"Checkpoint saved to {self.checkpoint_file}")
            return True
            
        except Exception as e:
            logging.error(f"Failed to save checkpoint: {e}")
            return False
    
    def start_stage(self, stage_name: str, **stage_metrics) -> bool:
        """
        Mark the start of a pipeline stage.
        
        Args:
            stage_name: Name of the stage being started
            **stage_metrics: Additional metrics to include
            
        Returns:
            bool: True if stage was started, False if already in progress/completed
        """
        if stage_name not in self.progress["stages"]:
            # Auto-add new stages
            self.progress["stages"][stage_name] = {
                "status": "started",
                "start_time": datetime.now().isoformat(),
                "end_time": None,
                "metrics": stage_metrics or {}
            }
        else:
            stage = self.progress["stages"][stage_name]
            if stage["status"] in ["completed", "failed"]:
                return False
                
            stage.update({
                "status": "started",
                "start_time": datetime.now().isoformat(),
                "end_time": None,
                **stage_metrics
            })
        
        self.progress["execution"]["current_stage"] = stage_name
        self.progress["execution"]["status"] = f"running_{stage_name}"
        return self.save()
    
    def complete_stage(self, stage_name: str, **stage_metrics) -> bool:
        """Mark a pipeline stage as completed."""
        if stage_name not in self.progress["stages"]:
            self.start_stage(stage_name, **stage_metrics)
            
        stage = self.progress["stages"][stage_name]
        stage.update({
            "status": "completed",
            "end_time": datetime.now().isoformat(),
            **stage_metrics
        })
        
        # Update execution status
        all_stages = list(self.progress["stages"].keys())
        current_idx = all_stages.index(stage_name)
        
        if current_idx < len(all_stages) - 1:
            self.progress["execution"]["current_stage"] = all_stages[current_idx + 1]
        else:
            self.progress["execution"]["current_stage"] = None
            self.progress["execution"]["status"] = "completed"
        
        return self.save()
    
    def fail_stage(self, stage_name: str, error: Exception, **stage_metrics) -> bool:
        """Mark a pipeline stage as failed."""
        if stage_name not in self.progress["stages"]:
            self.start_stage(stage_name, **stage_metrics)
            
        stage = self.progress["stages"][stage_name]
        stage.update({
            "status": "failed",
            "end_time": datetime.now().isoformat(),
            "error": str(error),
            "error_type": error.__class__.__name__,
            **stage_metrics
        })
        
        # Log error
        self.progress["errors"].append({
            "stage": stage_name,
            "timestamp": datetime.now().isoformat(),
            "error": str(error),
            "type": error.__class__.__name__,
            "traceback": str(getattr(error, "__traceback__", ""))
        })
        
        self.progress["execution"]["status"] = f"failed_{stage_name}"
        return self.save()
    
    def get_stage_status(self, stage_name: str) -> Dict[str, Any]:
        """Get the status of a specific stage."""
        return self.progress["stages"].get(stage_name, {"status": "not_started"})
    
    def is_stage_completed(self, stage_name: str) -> bool:
        """Check if a stage has been completed."""
        return self.get_stage_status(stage_name).get("status") == "completed"
    
    def get_progress(self) -> Dict[str, Any]:
        """Get current progress summary."""
        # Calculate completion percentage
        total_stages = len(self.progress["stages"])
        completed_stages = sum(
            1 for stage in self.progress["stages"].values() 
            if stage.get("status") == "completed"
        )
        
        # Get current stage
        current_stage = self.progress["execution"].get("current_stage")
        
        # Calculate time estimates
        runtime = time.time() - self._start_time
        if completed_stages > 0:
            avg_time_per_stage = runtime / completed_stages
            remaining_stages = total_stages - completed_stages
            eta_seconds = int(avg_time_per_stage * remaining_stages)
        else:
            eta_seconds = None
        
        return {
            "status": self.progress["execution"]["status"],
            "current_stage": current_stage,
            "completed_stages": completed_stages,
            "total_stages": total_stages,
            "progress_percent": int((completed_stages / total_stages) * 100) if total_stages > 0 else 0,
            "runtime_seconds": int(runtime),
            "eta_seconds": eta_seconds,
            "peak_memory_mb": round(self.progress["resources"]["peak_memory_mb"], 2),
            "checkpoint_count": self.progress["resources"]["checkpoint_count"]
        }
    
    def log_metric(self, stage_name: str, metric_name: str, value: Any) -> bool:
        """Log a metric for the current stage."""
        if stage_name not in self.progress["stages"]:
            self.start_stage(stage_name)
            
        stage = self.progress["stages"][stage_name]
        if "metrics" not in stage:
            stage["metrics"] = {}
            
        stage["metrics"][metric_name] = value
        return self.save()
    
    def add_generated_file(self, file_path: str, file_type: str, **metadata) -> bool:
        """Add a generated file to the checkpoint."""
        if not os.path.exists(file_path):
            logging.warning(f"File does not exist: {file_path}")
            return False
            
        file_info = {
            "path": str(file_path),
            "type": file_type,
            "size_bytes": os.path.getsize(file_path),
            "created_at": datetime.now().isoformat(),
            **metadata
        }
        
        self.progress["files"]["generated_files"].append(file_info)
        return self.save()
    
    def add_temporary_file(self, file_path: str) -> bool:
        """Add a temporary file to track for cleanup."""
        self.progress["files"]["temporary_files"].append(str(file_path))
        return self.save()
    
    def cleanup_temporary_files(self) -> int:
        """Clean up all tracked temporary files."""
        removed = 0
        temp_files = self.progress["files"]["temporary_files"]
        
        for file_path in temp_files[:]:  # Create a copy for safe iteration
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    removed += 1
                temp_files.remove(file_path)
            except Exception as e:
                logging.warning(f"Failed to remove temporary file {file_path}: {e}")
        
        if removed > 0:
            self.save()
            
        return removed

# Example usage
if __name__ == "__main__":
    # Initialize checkpoint manager
    checkpoint = CheckpointManager("checkpoints")
    
    # Start a stage
    checkpoint.start_stage("data_loading", input_file="data.csv")
    
    # Update progress
    checkpoint.log_metric("data_loading", "rows_processed", 1000)
    
    # Complete the stage
    checkpoint.complete_stage("data_loading", rows_processed=1500, columns=10)
    
    # Get progress
    print(checkpoint.get_progress())

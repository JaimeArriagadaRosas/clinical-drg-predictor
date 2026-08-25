#!/usr/bin/env python3
"""Training Pipeline Main Script."""

import subprocess
import sys
import os
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
STAGES = [
    ('Load Data', '01_load_data.py'),
    ('Quality Analysis', '02_quality_analysis.py'),
    ('Preprocessing', '03_preprocessing.py'),
    ('Train Models', '04_train_models.py'),
]

def run_stage(name: str, script: str, args: list = None):
    logger.info(f"\n{'='*60}\nSTAGE: {name}\n{'='*60}")
    script_path = os.path.join(SCRIPT_DIR, script)
    cmd = [sys.executable, script_path]
    if args:
        cmd.extend(args)
    result = subprocess.run(cmd, cwd=os.getcwd())
    if result.returncode != 0:
        logger.error(f"Stage {name} failed with return code {result.returncode}")
        sys.exit(1)
    logger.info(f"Stage {name} completed successfully")

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Run GRD prediction training pipeline')
    parser.add_argument('--skip-quality', action='store_true')
    parser.add_argument('--data-path', type=str, default=None)
    args = parser.parse_args()
    common_args = []
    if args.data_path:
        common_args.extend(['--data-path', args.data_path])
    for name, script in STAGES:
        if name == 'Quality Analysis' and args.skip_quality:
            continue
        run_stage(name, script, common_args.copy())

if __name__ == "__main__":
    main()

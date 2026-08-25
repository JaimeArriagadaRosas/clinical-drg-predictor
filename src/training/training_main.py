#!/usr/bin/env python3
"""Orchestrate the historical GRD training stages."""

import argparse
import logging
import os
import subprocess
import sys

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

STAGES = [
    ("Load Data", "01_load_data.py"),
    ("Quality Analysis", "02_quality_analysis.py"),
    ("Preprocessing", "03_preprocessing.py"),
    ("Train Models", "04_train_models.py"),
]


def build_stage_args(name: str, args: argparse.Namespace) -> list[str]:
    """Return only arguments supported by a particular training stage."""
    stage_args: list[str] = []

    if name == "Load Data" and args.data_path:
        stage_args.extend(["--data-path", args.data_path])

    if name == "Train Models":
        stage_args.extend(["--n-estimators", str(args.n_estimators)])
        if args.max_depth is not None:
            stage_args.extend(["--max-depth", str(args.max_depth)])
        if args.skip_lgbm:
            stage_args.append("--skip-lgbm")

    return stage_args


def run_stage(name: str, script: str, args: list[str] | None = None):
    logger.info("\n%s\nSTAGE: %s\n%s", "=" * 60, name, "=" * 60)
    script_path = os.path.join(SCRIPT_DIR, script)
    command = [sys.executable, script_path]
    if args:
        command.extend(args)

    result = subprocess.run(command, cwd=os.getcwd())
    if result.returncode != 0:
        logger.error("Stage %s failed with return code %s", name, result.returncode)
        raise SystemExit(1)
    logger.info("Stage %s completed successfully", name)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run GRD prediction training pipeline")
    parser.add_argument("--skip-quality", action="store_true", help="Skip data quality analysis")
    parser.add_argument("--data-path", type=str, default=None, help="Path to the source CSV dataset")
    parser.add_argument(
        "--n-estimators",
        type=int,
        default=200,
        help="Number of Random Forest estimators",
    )
    parser.add_argument(
        "--max-depth",
        type=int,
        default=None,
        help="Maximum Random Forest tree depth",
    )
    parser.add_argument(
        "--skip-lgbm",
        action="store_true",
        help="Skip optional LightGBM training",
    )
    return parser


def main():
    args = build_parser().parse_args()

    for name, script in STAGES:
        if name == "Quality Analysis" and args.skip_quality:
            logger.info("Skipping %s", name)
            continue
        run_stage(name, script, build_stage_args(name, args))

    logger.info("\n%s\nTRAINING PIPELINE COMPLETE\n%s", "=" * 60, "=" * 60)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Stage 1: Load and Explore Dataset
Celda 5 del notebook Fase 1
"""

import pandas as pd
import numpy as np
import os
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_dataset(data_path: str = None) -> pd.DataFrame:
    """Load the GRD dataset from CSV file."""
    if data_path is None:
        data_path = os.environ.get('DATA_PATH', 'dataset/dataset_elpino.csv')
    logger.info(f"Loading dataset from {data_path}")
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Dataset not found at {data_path}")
    df = pd.read_csv(data_path, delimiter=';', on_bad_lines='skip', encoding='utf-8')
    logger.info(f"Loaded {len(df)} records with {len(df.columns)} columns")
    return df

def explore_dataset(df: pd.DataFrame) -> dict:
    """Explore dataset structure and return column information."""
    logger.info("Exploring dataset structure...")
    diagnosis_cols = [col for col in df.columns if 'Diag' in col]
    procedure_cols = [col for col in df.columns if 'Proced' in col]
    info = {
        'n_records': len(df),
        'n_columns': len(df.columns),
        'diagnosis_columns': diagnosis_cols,
        'procedure_columns': procedure_cols,
        'n_diagnosis_cols': len(diagnosis_cols),
        'n_procedure_cols': len(procedure_cols),
    }
    logger.info(f"Diagnosis columns: {len(diagnosis_cols)}")
    logger.info(f"Procedure columns: {len(procedure_cols)}")
    return info

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Load and explore GRD dataset')
    parser.add_argument('--data-path', type=str, default=None, help='Path to dataset CSV')
    parser.add_argument('--output-dir', type=str, default='dataset/processed', help='Output directory')
    args = parser.parse_args()
    os.makedirs(args.output_dir, exist_ok=True)
    df = load_dataset(args.data_path)
    info = explore_dataset(df)
    df.to_pickle(f'{args.output_dir}/dataset_loaded.pkl')
    logger.info(f"Saved loaded dataset to {args.output_dir}/dataset_loaded.pkl")
    print("\nDataset Summary:")
    print(f"  Records: {info['n_records']}")
    print(f"  Columns: {info['n_columns']}")

if __name__ == "__main__":
    main()

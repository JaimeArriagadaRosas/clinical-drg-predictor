#!/usr/bin/env python3
"""
Stage 3: Preprocessing and Feature Engineering
Celdas 21-25 del notebook Fase 1
"""

import pandas as pd
import numpy as np
import pickle
import os
import logging
import re

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def filter_rare_classes(df: pd.DataFrame, min_samples: int = 2) -> pd.DataFrame:
    """Filter out GRD classes with fewer than min_samples."""
    logger.info(f"Filtering classes with fewer than {min_samples} samples...")
    grd_counts = df['GRD'].value_counts()
    valid_classes = grd_counts[grd_counts >= min_samples].index
    df_filtered = df[df['GRD'].isin(valid_classes)].copy()
    logger.info(f"Removed {len(df) - len(df_filtered)} samples from rare classes")
    logger.info(f"Remaining: {len(df_filtered)} samples with {len(valid_classes)} classes")
    return df_filtered

def extract_icd_code(text: str) -> str:
    """Extract ICD code from text string."""
    if pd.isna(text) or str(text).strip() in {'-', 'nan', '', None}:
        return None
    text = str(text).strip()
    match = re.match(r'^([A-Z]\d{2}(?:\.\d)?)', text)
    if match:
        return match.group(1).upper()
    match = re.match(r'^(\d{2}\.\d{2})', text)
    if match:
        return match.group(1)
    match = re.match(r'^(\d{6})', text)
    if match:
        return match.group(1)
    return None

def create_binary_features(df: pd.DataFrame, max_diag_codes: int = 500, max_proc_codes: int = 300) -> tuple:
    """Create binary features for diagnosis and procedure codes."""
    logger.info("Creating binary features for ICD codes...")
    diagnosis_cols = [col for col in df.columns if 'Diag' in col]
    procedure_cols = [col for col in df.columns if 'Proced' in col]
    all_diag_codes = []
    for col in diagnosis_cols:
        for val in df[col].dropna():
            code = extract_icd_code(val)
            if code:
                all_diag_codes.append(code)
    all_proc_codes = []
    for col in procedure_cols:
        for val in df[col].dropna():
            code = extract_icd_code(val)
            if code:
                all_proc_codes.append(code)
    from collections import Counter
    diag_code_counts = Counter(all_diag_codes)
    proc_code_counts = Counter(all_proc_codes)
    top_diag_codes = [code for code, _ in diag_code_counts.most_common(max_diag_codes)]
    top_proc_codes = [code for code, _ in proc_code_counts.most_common(max_proc_codes)]
    logger.info(f"Using {len(top_diag_codes)} diagnosis codes as features")
    logger.info(f"Using {len(top_proc_codes)} procedure codes as features")
    diag_features = pd.DataFrame(0, index=df.index, columns=[f'DIAG_{code}' for code in top_diag_codes])
    proc_features = pd.DataFrame(0, index=df.index, columns=[f'PROC_{code}' for code in top_proc_codes])
    for col in diagnosis_cols:
        codes = df[col].apply(extract_icd_code)
        for idx, code in codes.items():
            if code in top_diag_codes:
                diag_features.loc[idx, f'DIAG_{code}'] = 1
    for col in procedure_cols:
        codes = df[col].apply(extract_icd_code)
        for idx, code in codes.items():
            if code in top_proc_codes:
                proc_features.loc[idx, f'PROC_{code}'] = 1
    return diag_features, proc_features, top_diag_codes, top_proc_codes

def create_demographic_features(df: pd.DataFrame) -> pd.DataFrame:
    """Create demographic features (age groups, sex)."""
    logger.info("Creating demographic features...")
    age = df['Edad en años'].copy().clip(0, 120)
    age_groups = pd.cut(age, bins=[0, 1, 5, 18, 40, 60, 80, 120], labels=['neonate', 'infant', 'child', 'young_adult', 'middle_adult', 'senior', 'elderly'], include_lowest=True)
    age_dummies = pd.get_dummies(age_groups, prefix='AGE')
    sex = df['Sexo (Desc)'].fillna('Unknown')
    sex_encoded = (sex == 'Hombre').astype(int)
    sex_df = pd.DataFrame({'SEX_MALE': sex_encoded})
    demo_features = pd.concat([age_dummies, sex_df], axis=1)
    logger.info(f"Demographic features: {demo_features.columns.tolist()}")
    return demo_features

def encode_target(df: pd.DataFrame) -> tuple:
    """Encode target variable (GRD)."""
    from sklearn.preprocessing import LabelEncoder
    logger.info("Encoding target variable...")
    grd = df['GRD'].fillna('UNKNOWN')
    le = LabelEncoder()
    grd_encoded = le.fit_transform(grd)
    logger.info(f"Number of GRD classes: {len(le.classes_)}")
    return grd_encoded, le

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Preprocess data and create features')
    parser.add_argument('--input', type=str, default='dataset/processed/dataset_loaded.pkl', help='Input pickle file')
    parser.add_argument('--output-dir', type=str, default='dataset/processed', help='Output directory')
    parser.add_argument('--min-samples', type=int, default=2, help='Minimum samples per class')
    parser.add_argument('--max-diag', type=int, default=500, help='Max diagnosis codes')
    parser.add_argument('--max-proc', type=int, default=300, help='Max procedure codes')
    args = parser.parse_args()
    os.makedirs(args.output_dir, exist_ok=True)
    df = pd.read_pickle(args.input)
    df = filter_rare_classes(df, args.min_samples)
    diag_features, proc_features, diag_codes, proc_codes = create_binary_features(df, args.max_diag, args.max_proc)
    demo_features = create_demographic_features(df)
    y, label_encoder = encode_target(df)
    X = pd.concat([demo_features, diag_features, proc_features], axis=1)
    logger.info(f"Final feature matrix shape: {X.shape}")
    X.to_csv(f'{args.output_dir}/X_features.csv', index=False)
    np.save(f'{args.output_dir}/y_target.npy', y)
    with open(f'{args.output_dir}/label_encoder.pkl', 'wb') as f:
        pickle.dump(label_encoder, f)
    metadata = {'diag_codes': diag_codes, 'proc_codes': proc_codes, 'n_classes': len(label_encoder.classes_), 'feature_names': X.columns.tolist()}
    with open(f'{args.output_dir}/metadata.pkl', 'wb') as f:
        pickle.dump(metadata, f)
    logger.info(f"Saved processed data to {args.output_dir}")
    print("\nPreprocessing Complete:")
    print(f"  Features: {X.shape[1]}")
    print(f"  Samples: {X.shape[0]}")
    print(f"  Classes: {len(label_encoder.classes_)}")

if __name__ == "__main__":
    main()
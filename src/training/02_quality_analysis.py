#!/usr/bin/env python3
"""
Stage 2: Data Quality Analysis
Celdas 9-11 del notebook Fase 1 (Completitud, Correctitud, Outliers)
"""

import pandas as pd
import re
import logging
import os

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
MISSING_SENTINEL = {'-', 'nan', '', None}

def analyze_completeness(df: pd.DataFrame) -> dict:
    diagnosis_cols = [col for col in df.columns if 'Diag' in col]
    procedure_cols = [col for col in df.columns if 'Proced' in col]
    def count_valid(series):
        valid = series.apply(lambda x: pd.notna(x) and str(x).strip() not in MISSING_SENTINEL)
        return valid.sum()
    diag_completeness = {col: count_valid(df[col]) / len(df) * 100 for col in diagnosis_cols}
    proc_completeness = {col: count_valid(df[col]) / len(df) * 100 for col in procedure_cols}
    return {
        'diagnosis_completeness': {k: float(v) for k, v in diag_completeness.items()},
        'procedure_completeness': {k: float(v) for k, v in proc_completeness.items()},
    }

def extract_icd_code(text: str) -> str:
    if pd.isna(text) or str(text).strip() in MISSING_SENTINEL:
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

def validate_icd_codes(df: pd.DataFrame) -> dict:
    diagnosis_cols = [col for col in df.columns if 'Diag' in col]
    procedure_cols = [col for col in df.columns if 'Proced' in col]
    total_diag_codes = valid_diag_codes = total_proc_codes = valid_proc_codes = 0
    for col in diagnosis_cols:
        for val in df[col].dropna():
            code = extract_icd_code(val)
            if code:
                total_diag_codes += 1
                if re.match(r'^[A-Z]\d{2}', code):
                    valid_diag_codes += 1
    for col in procedure_cols:
        for val in df[col].dropna():
            code = extract_icd_code(val)
            if code:
                total_proc_codes += 1
                if re.match(r'^\d{2}\.\d{2}', code):
                    valid_proc_codes += 1
    return {
        'diagnosis_total': int(total_diag_codes),
        'diagnosis_valid': int(valid_diag_codes),
        'diagnosis_validity_pct': float((valid_diag_codes / total_diag_codes * 100) if total_diag_codes else 0),
        'procedure_total': int(total_proc_codes),
        'procedure_valid': int(valid_proc_codes),
        'procedure_validity_pct': float((valid_proc_codes / total_proc_codes * 100) if total_proc_codes else 0),
    }

def analyze_outliers(df: pd.DataFrame) -> dict:
    age = df['Edad en años'].copy()
    q1 = age.quantile(0.25)
    q3 = age.quantile(0.75)
    iqr = q3 - q1
    upper_bound = q3 + 1.5 * iqr
    lower_bound = q1 - 1.5 * iqr
    outliers = age[(age > upper_bound) | (age < lower_bound)]
    return {
        'age_mean': float(age.mean()),
        'age_std': float(age.std()),
        'age_min': int(age.min()),
        'age_max': int(age.max()),
        'age_median': float(age.median()),
        'outliers_count': int(len(outliers)),
        'outliers_values': [int(x) for x in outliers.tolist()[:10]],
    }

def main():
    import argparse, json
    parser = argparse.ArgumentParser(description='Analyze data quality')
    parser.add_argument('--input', type=str, default='dataset/processed/dataset_loaded.pkl')
    parser.add_argument('--output-dir', type=str, default='dataset/processed')
    args = parser.parse_args()
    os.makedirs(args.output_dir, exist_ok=True)
    df = pd.read_pickle(args.input)
    completeness = analyze_completeness(df)
    validity = validate_icd_codes(df)
    outliers = analyze_outliers(df)
    results = {**completeness, **validity, **outliers}
    with open(f'{args.output_dir}/quality_report.json', 'w') as f:
        json.dump(results, f, indent=2)
    logger.info(f"Quality report saved to {args.output_dir}/quality_report.json")

if __name__ == "__main__":
    main()

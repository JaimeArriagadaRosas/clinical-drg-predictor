#!/usr/bin/env python3
"""
Stage 4: Model Training
Celdas 29-30 del notebook Fase 1 (Random Forest + LightGBM)
"""

import pandas as pd
import numpy as np
import pickle
import os
import logging
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, f1_score

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

try:
    import lightgbm as lgb
    HAS_LGB = True
except ImportError:
    HAS_LGB = False
    logger.warning("LightGBM not available")

def load_preprocessed_data(data_dir: str = 'dataset/processed') -> tuple:
    logger.info("Loading preprocessed data...")
    X = pd.read_csv(f'{data_dir}/X_features.csv')
    y = np.load(f'{data_dir}/y_target.npy')
    with open(f'{data_dir}/label_encoder.pkl', 'rb') as f:
        label_encoder = pickle.load(f)
    with open(f'{data_dir}/metadata.pkl', 'rb') as f:
        metadata = pickle.load(f)
    logger.info(f"Loaded {X.shape[0]} samples with {X.shape[1]} features")
    return X, y, label_encoder, metadata

def split_data(X, y, test_size: float = 0.2, random_state: int = 42) -> tuple:
    logger.info(f"Splitting data (test_size={test_size})...")
    X_train, X_test, y_train, y_test = train_test_split(X.values, y, test_size=test_size, random_state=random_state, stratify=y)
    logger.info(f"Training set: {X_train.shape[0]} samples")
    logger.info(f"Test set: {X_test.shape[0]} samples")
    return X_train, X_test, y_train, y_test

def train_random_forest(X_train, y_train, n_estimators: int = 200, max_depth: int = None, random_state: int = 42) -> object:
    logger.info(f"Training Random Forest (n_estimators={n_estimators})...")
    model = RandomForestClassifier(n_estimators=n_estimators, max_depth=max_depth, min_samples_split=2, min_samples_leaf=1, max_features='sqrt', bootstrap=True, n_jobs=-1, random_state=random_state, class_weight='balanced')
    model.fit(X_train, y_train)
    logger.info("Random Forest training complete")
    return model

def train_lightgbm(X_train, y_train, n_estimators: int = 150, learning_rate: float = 0.1, random_state: int = 42) -> object:
    if not HAS_LGB:
        raise ImportError("LightGBM not available")
    model = lgb.LGBMClassifier(n_estimators=n_estimators, max_depth=8, learning_rate=learning_rate, num_leaves=50, subsample=0.8, colsample_bytree=0.8, n_jobs=-1, random_state=random_state, class_weight='balanced', verbose=-1)
    model.fit(X_train, y_train)
    logger.info("LightGBM training complete")
    return model

def evaluate_model(model, X_train, X_test, y_train, y_test, name: str) -> dict:
    y_train_pred = model.predict(X_train)
    y_test_pred = model.predict(X_test)
    metrics = {
        'name': name,
        'train_accuracy': accuracy_score(y_train, y_train_pred),
        'test_accuracy': accuracy_score(y_test, y_test_pred),
        'train_f1_macro': f1_score(y_train, y_train_pred, average='macro', zero_division=0.0),
        'test_f1_macro': f1_score(y_test, y_test_pred, average='macro', zero_division=0.0),
        'train_f1_weighted': f1_score(y_train, y_train_pred, average='weighted', zero_division=0.0),
        'test_f1_weighted': f1_score(y_test, y_test_pred, average='weighted', zero_division=0.0),
    }
    logger.info(f"  Test Accuracy: {metrics['test_accuracy']:.4f}")
    logger.info(f"  Test F1 (weighted): {metrics['test_f1_weighted']:.4f}")
    return metrics

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Train GRD prediction models')
    parser.add_argument('--data-dir', type=str, default='dataset/processed', help='Data directory')
    parser.add_argument('--output-dir', type=str, default='models', help='Output directory')
    parser.add_argument('--n-estimators', type=int, default=200, help='Number of estimators')
    parser.add_argument('--skip-lgbm', action='store_true', help='Skip LightGBM training')
    args = parser.parse_args()
    os.makedirs(args.output_dir, exist_ok=True)
    X, y, label_encoder, metadata = load_preprocessed_data(args.data_dir)
    X_train, X_test, y_train, y_test = split_data(X, y)
    results = {}
    rf_model = train_random_forest(X_train, y_train, args.n_estimators)
    results['RandomForest'] = evaluate_model(rf_model, X_train, X_test, y_train, y_test, 'RandomForest')
    if HAS_LGB and not args.skip_lgbm:
        lgbm_model = train_lightgbm(X_train, y_train)
        results['LightGBM'] = evaluate_model(lgbm_model, X_train, X_test, y_train, y_test, 'LightGBM')
    best_name = max(results.keys(), key=lambda k: results[k]['test_f1_weighted'])
    logger.info(f"Best model: {best_name}")
    best_model = rf_model if best_name == 'RandomForest' else lgbm_model
    with open(f'{args.output_dir}/best_model.pkl', 'wb') as f:
        pickle.dump(best_model, f)
    logger.info(f"Saved best model to {args.output_dir}/best_model.pkl")

if __name__ == "__main__":
    main()
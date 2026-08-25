#!/usr/bin/env python3
"""Stage 4: train and select the GRD prediction model."""

import argparse
import logging
import os
import pickle

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, f1_score
from sklearn.model_selection import train_test_split

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

try:
    import lightgbm as lgb

    HAS_LGB = True
except ImportError:
    HAS_LGB = False
    logger.warning("LightGBM not available")


def load_preprocessed_data(data_dir: str = "dataset/processed") -> tuple:
    logger.info("Loading preprocessed data...")
    features = pd.read_csv(f"{data_dir}/X_features.csv")
    target = np.load(f"{data_dir}/y_target.npy")
    with open(f"{data_dir}/label_encoder.pkl", "rb") as encoder_file:
        label_encoder = pickle.load(encoder_file)
    with open(f"{data_dir}/metadata.pkl", "rb") as metadata_file:
        metadata = pickle.load(metadata_file)
    logger.info("Loaded %s samples with %s features", features.shape[0], features.shape[1])
    return features, target, label_encoder, metadata


def split_data(features, target, test_size: float = 0.2, random_state: int = 42) -> tuple:
    logger.info("Splitting data (test_size=%s)...", test_size)
    result = train_test_split(
        features.values,
        target,
        test_size=test_size,
        random_state=random_state,
        stratify=target,
    )
    x_train, x_test, y_train, y_test = result
    logger.info("Training set: %s samples", x_train.shape[0])
    logger.info("Test set: %s samples", x_test.shape[0])
    return x_train, x_test, y_train, y_test


def train_random_forest(
    x_train,
    y_train,
    n_estimators: int = 200,
    max_depth: int | None = None,
    random_state: int = 42,
) -> object:
    logger.info(
        "Training Random Forest (n_estimators=%s, max_depth=%s)...",
        n_estimators,
        max_depth,
    )
    model = RandomForestClassifier(
        n_estimators=n_estimators,
        max_depth=max_depth,
        min_samples_split=2,
        min_samples_leaf=1,
        max_features="sqrt",
        bootstrap=True,
        n_jobs=-1,
        random_state=random_state,
        class_weight="balanced",
    )
    model.fit(x_train, y_train)
    logger.info("Random Forest training complete")
    return model


def train_lightgbm(
    x_train,
    y_train,
    n_estimators: int = 150,
    learning_rate: float = 0.1,
    random_state: int = 42,
) -> object:
    if not HAS_LGB:
        raise ImportError("LightGBM not available")
    model = lgb.LGBMClassifier(
        n_estimators=n_estimators,
        max_depth=8,
        learning_rate=learning_rate,
        num_leaves=50,
        subsample=0.8,
        colsample_bytree=0.8,
        n_jobs=-1,
        random_state=random_state,
        class_weight="balanced",
        verbose=-1,
    )
    model.fit(x_train, y_train)
    logger.info("LightGBM training complete")
    return model


def evaluate_model(model, x_train, x_test, y_train, y_test, name: str) -> dict:
    y_train_pred = model.predict(x_train)
    y_test_pred = model.predict(x_test)
    metrics = {
        "name": name,
        "train_accuracy": accuracy_score(y_train, y_train_pred),
        "test_accuracy": accuracy_score(y_test, y_test_pred),
        "train_f1_macro": f1_score(y_train, y_train_pred, average="macro", zero_division=0.0),
        "test_f1_macro": f1_score(y_test, y_test_pred, average="macro", zero_division=0.0),
        "train_f1_weighted": f1_score(
            y_train, y_train_pred, average="weighted", zero_division=0.0
        ),
        "test_f1_weighted": f1_score(
            y_test, y_test_pred, average="weighted", zero_division=0.0
        ),
    }
    logger.info("  Test Accuracy: %.4f", metrics["test_accuracy"])
    logger.info("  Test F1 (weighted): %.4f", metrics["test_f1_weighted"])
    return metrics


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Train GRD prediction models")
    parser.add_argument("--data-dir", type=str, default="dataset/processed", help="Data directory")
    parser.add_argument("--output-dir", type=str, default="models", help="Output directory")
    parser.add_argument("--n-estimators", type=int, default=200, help="Number of estimators")
    parser.add_argument("--max-depth", type=int, default=None, help="Maximum tree depth")
    parser.add_argument("--skip-lgbm", action="store_true", help="Skip LightGBM training")
    return parser


def main():
    args = build_parser().parse_args()
    os.makedirs(args.output_dir, exist_ok=True)

    features, target, _label_encoder, _metadata = load_preprocessed_data(args.data_dir)
    x_train, x_test, y_train, y_test = split_data(features, target)

    results = {}
    rf_model = train_random_forest(
        x_train,
        y_train,
        n_estimators=args.n_estimators,
        max_depth=args.max_depth,
    )
    results["RandomForest"] = evaluate_model(
        rf_model, x_train, x_test, y_train, y_test, "RandomForest"
    )

    lgbm_model = None
    if HAS_LGB and not args.skip_lgbm:
        lgbm_model = train_lightgbm(x_train, y_train)
        results["LightGBM"] = evaluate_model(
            lgbm_model, x_train, x_test, y_train, y_test, "LightGBM"
        )

    best_name = max(results, key=lambda key: results[key]["test_f1_weighted"])
    logger.info("Best model: %s", best_name)
    best_model = rf_model if best_name == "RandomForest" else lgbm_model

    with open(f"{args.output_dir}/best_model.pkl", "wb") as model_file:
        pickle.dump(best_model, model_file)
    logger.info("Saved best model to %s/best_model.pkl", args.output_dir)


if __name__ == "__main__":
    main()

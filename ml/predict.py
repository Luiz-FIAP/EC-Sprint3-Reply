#!/usr/bin/env python3
import argparse
import json
import os
from typing import Dict, List

import joblib
import numpy as np
import pandas as pd


def load_artifacts(base_dir: str):
    artifacts_dir = os.path.join(base_dir, "artifacts")
    scaler = joblib.load(os.path.join(artifacts_dir, "scaler.pkl"))
    model = joblib.load(os.path.join(artifacts_dir, "kmeans.pkl"))
    with open(os.path.join(artifacts_dir, "metadata.json"), "r", encoding="utf-8") as f:
        metadata = json.load(f)
    feature_cols: List[str] = metadata["feature_cols"]
    severity_map: Dict[int, str] = {int(k): v for k, v in metadata["severity_map"].items()}
    return scaler, model, feature_cols, severity_map


def run_predict(input_csv: str, output_csv: str, base_dir: str) -> str:
    scaler, model, feature_cols, severity_map = load_artifacts(base_dir)

    df = pd.read_csv(input_csv)
    missing = [c for c in feature_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Colunas ausentes no CSV de entrada: {missing}")

    X = df[feature_cols].to_numpy()
    X_scaled = scaler.transform(X)

    labels = model.predict(X_scaled)
    df_out = df.copy()
    df_out["cluster_id"] = labels
    df_out["severity"] = df_out["cluster_id"].map(severity_map)

    os.makedirs(os.path.dirname(output_csv), exist_ok=True)
    df_out.to_csv(output_csv, index=False)
    return output_csv


def main() -> None:
    base_dir = os.path.dirname(__file__)

    parser = argparse.ArgumentParser(description="Predição de severidade via KMeans treinado")
    parser.add_argument("--input", required=True, help="CSV de entrada para predição")
    parser.add_argument(
        "--output",
        required=False,
        default=os.path.join(base_dir, "outputs", "predictions.csv"),
        help="CSV de saída com predições",
    )
    args = parser.parse_args()

    out = run_predict(args.input, args.output, base_dir)
    print(f"[OK] Predição salva em: {out}")


if __name__ == "__main__":
    main()

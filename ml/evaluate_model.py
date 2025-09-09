#!/usr/bin/env python3
import json
import os
from typing import Dict, List, Tuple

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from scipy.optimize import linear_sum_assignment
from sklearn.metrics import (
    adjusted_mutual_info_score,
    adjusted_rand_score,
    completeness_score,
    confusion_matrix,
    homogeneity_score,
    normalized_mutual_info_score,
    v_measure_score,
)


def ensure_dirs(base_dir: str) -> Dict[str, str]:
    outputs_dir = os.path.join(base_dir, "outputs")
    reports_dir = os.path.join(base_dir, "reports")
    os.makedirs(outputs_dir, exist_ok=True)
    os.makedirs(reports_dir, exist_ok=True)
    return {"outputs": outputs_dir, "reports": reports_dir}


def load_assignments(assignments_path: str) -> pd.DataFrame:
    if not os.path.exists(assignments_path):
        raise FileNotFoundError(
            f"Arquivo não encontrado: {assignments_path}. Rode antes: python cluster_model.py"
        )
    df = pd.read_csv(assignments_path)
    if "label_true" not in df.columns or "cluster_id" not in df.columns:
        raise ValueError(
            "O arquivo de assignments precisa conter as colunas 'label_true' e 'cluster_id'."
        )
    return df


def encode_labels(series: pd.Series) -> Tuple[np.ndarray, Dict[int, str]]:
    categories = series.astype(str).unique().tolist()
    categories.sort()
    mapping = {label: idx for idx, label in enumerate(categories)}
    encoded = series.astype(str).map(mapping).to_numpy()
    inv_mapping = {v: k for k, v in mapping.items()}
    return encoded, inv_mapping


def optimal_label_mapping(y_true: np.ndarray, y_pred: np.ndarray) -> Tuple[np.ndarray, Dict[int, int]]:
    # Constrói matriz de confusão entre rótulos inteiros
    labels_true = np.unique(y_true)
    labels_pred = np.unique(y_pred)
    cm = confusion_matrix(y_true, y_pred, labels=labels_true)

    # Hungarian para maximizar o acerto (minimizando o custo negativo)
    cost = -cm
    row_ind, col_ind = linear_sum_assignment(cost)

    mapping: Dict[int, int] = {}
    for r, c in zip(row_ind, col_ind):
        mapping[labels_pred[c] if c < len(labels_pred) else c] = labels_true[r]

    y_pred_mapped = np.array([mapping.get(p, p) for p in y_pred])
    return y_pred_mapped, mapping


def compute_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
    return {
        "ARI": float(adjusted_rand_score(y_true, y_pred)),
        "AMI": float(adjusted_mutual_info_score(y_true, y_pred)),
        "NMI": float(normalized_mutual_info_score(y_true, y_pred)),
        "Homogeneity": float(homogeneity_score(y_true, y_pred)),
        "Completeness": float(completeness_score(y_true, y_pred)),
        "VMeasure": float(v_measure_score(y_true, y_pred)),
        "Accuracy_opt_map": float((y_true == y_pred).mean()),
    }


def save_confusion(cm: np.ndarray, labels_true: List[str], labels_pred: List[str], outputs_dir: str) -> Tuple[str, str]:
    df_cm = pd.DataFrame(cm, index=labels_true, columns=labels_pred)
    csv_path = os.path.join(outputs_dir, "confusion_matrix.csv")
    df_cm.to_csv(csv_path)

    plt.figure(figsize=(6, 5))
    sns.heatmap(df_cm, annot=True, fmt="d", cmap="Blues")
    plt.ylabel("Verdadeiro")
    plt.xlabel("Predito (mapeado)")
    plt.title("Matriz de Confusão")
    png_path = os.path.join(outputs_dir, "confusion_matrix.png")
    plt.tight_layout()
    plt.savefig(png_path, dpi=140)
    plt.close()

    return csv_path, png_path


def main() -> None:
    base_dir = os.path.dirname(__file__)
    dirs = ensure_dirs(base_dir)

    assignments_path = os.path.join(dirs["outputs"], "cluster_assignments.csv")
    df = load_assignments(assignments_path)

    # Codificar rótulos verdadeiros e preditos
    y_true_enc, inv_true = encode_labels(df["label_true"])  # e.g., bom/alerta/critico
    y_pred_enc = df["cluster_id"].to_numpy().astype(int)

    # Mapeamento ótimo
    y_pred_mapped, mapping = optimal_label_mapping(y_true_enc, y_pred_enc)

    # Métricas
    metrics = compute_metrics(y_true_enc, y_pred_mapped)

    # Matriz de confusão com rótulos legíveis
    labels_true_sorted = [inv_true[i] for i in sorted(inv_true.keys())]
    cm = confusion_matrix(y_true_enc, y_pred_mapped, labels=sorted(inv_true.keys()))
    save_confusion(cm, labels_true_sorted, labels_true_sorted, dirs["outputs"]) 

    # Salvar métricas
    metrics_path = os.path.join(dirs["outputs"], "eval_metrics.json")
    with open(metrics_path, "w", encoding="utf-8") as f:
        json.dump(metrics, f, ensure_ascii=False, indent=2)

    print(f"[OK] Avaliação concluída. Métricas em: {metrics_path}")


if __name__ == "__main__":
    main()

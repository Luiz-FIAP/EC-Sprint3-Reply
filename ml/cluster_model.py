#!/usr/bin/env python3
import os
import json
from dataclasses import dataclass
from typing import Dict, List, Tuple

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import plotly.express as px
import seaborn as sns
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import calinski_harabasz_score, silhouette_score
from sklearn.preprocessing import StandardScaler
import joblib


@dataclass
class ClusterSelectionResult:
    best_k: int
    best_score: float
    method: str  # "silhouette" ou "calinski_harabasz"
    k_grid: List[int]
    silhouette_scores: List[float]
    ch_scores: List[float]


SEVERITY_LEVELS = [
    "bom",
    "alerta",
    "critico",
    "critico+",
    "critico++",
    "critico+++",
]


def ensure_dirs(base_dir: str) -> Dict[str, str]:
    data_dir = os.path.join(base_dir, "data")
    outputs_dir = os.path.join(base_dir, "outputs")
    reports_dir = os.path.join(base_dir, "reports")
    artifacts_dir = os.path.join(base_dir, "artifacts")
    os.makedirs(data_dir, exist_ok=True)
    os.makedirs(outputs_dir, exist_ok=True)
    os.makedirs(reports_dir, exist_ok=True)
    os.makedirs(artifacts_dir, exist_ok=True)
    return {"data": data_dir, "outputs": outputs_dir, "reports": reports_dir, "artifacts": artifacts_dir}


def load_dataset(data_path: str) -> pd.DataFrame:
    if not os.path.exists(data_path):
        raise FileNotFoundError(
            f"Dataset não encontrado em {data_path}. Rode primeiro: python generate_data.py"
        )
    with open(data_path, "r", encoding="utf-8", errors="ignore") as fh:
        first_line = fh.readline()
    if "timestamp" in first_line:
        df = pd.read_csv(data_path, parse_dates=["timestamp"])
    else:
        df = pd.read_csv(data_path)
    return df


def select_feature_columns(df: pd.DataFrame) -> List[str]:
    ignored = {"timestamp", "label_true"}
    feature_cols = [c for c in df.columns if c not in ignored and pd.api.types.is_numeric_dtype(df[c])]
    if not feature_cols:
        raise ValueError("Nenhuma coluna numérica encontrada para clusterização.")
    return feature_cols


def compute_risk_score_matrix(X_scaled: np.ndarray, feature_names: List[str]) -> np.ndarray:
    weights = np.ones(X_scaled.shape[1], dtype=float)
    return (X_scaled * weights).mean(axis=1)


def choose_k_with_silhouette_and_fallback(
    X_scaled: np.ndarray, k_min: int = 2, k_max: int = 8, silhouette_threshold: float = 0.35
) -> ClusterSelectionResult:
    k_grid = list(range(k_min, k_max + 1))
    silhouette_scores: List[float] = []
    ch_scores: List[float] = []

    for k in k_grid:
        km = KMeans(n_clusters=k, n_init=10, random_state=42)
        labels = km.fit_predict(X_scaled)
        sil = silhouette_score(X_scaled, labels)
        ch = calinski_harabasz_score(X_scaled, labels)
        silhouette_scores.append(sil)
        ch_scores.append(ch)

    best_k_sil = int(k_grid[int(np.nanargmax(silhouette_scores))])
    best_sil = float(np.nanmax(silhouette_scores))

    method = "silhouette"
    best_k = best_k_sil

    if best_sil < silhouette_threshold:
        best_k_ch = int(k_grid[int(np.nanargmax(ch_scores))])
        best_k = best_k_ch
        method = "calinski_harabasz"

    return ClusterSelectionResult(
        best_k=best_k,
        best_score=best_sil if method == "silhouette" else float(np.nanmax(ch_scores)),
        method=method,
        k_grid=k_grid,
        silhouette_scores=silhouette_scores,
        ch_scores=ch_scores,
    )


def fit_kmeans(X_scaled: np.ndarray, n_clusters: int) -> KMeans:
    model = KMeans(n_clusters=n_clusters, n_init=20, random_state=42)
    model.fit(X_scaled)
    return model


def map_clusters_to_severity(
    X_scaled: np.ndarray, cluster_labels: np.ndarray, feature_names: List[str]
) -> Dict[int, str]:
    risk = compute_risk_score_matrix(X_scaled, feature_names)
    cluster_ids = np.unique(cluster_labels)
    cluster_risk = {
        cid: float(risk[cluster_labels == cid].mean()) for cid in cluster_ids
    }
    ranked = sorted(cluster_risk.items(), key=lambda kv: kv[1])
    levels = SEVERITY_LEVELS.copy()
    if len(levels) < len(ranked):
        while len(levels) < len(ranked):
            levels.append(f"critico+{len(levels) - 2}")
    mapping: Dict[int, str] = {}
    for i, (cid, _risk_value) in enumerate(ranked):
        mapping[cid] = levels[i]
    return mapping


def plot_and_save_scores(
    result: ClusterSelectionResult, outputs_dir: str
) -> Tuple[str, str]:
    sns.set(style="whitegrid")

    plt.figure(figsize=(7, 4))
    plt.plot(result.k_grid, result.silhouette_scores, marker="o")
    plt.title("Silhouette vs k")
    plt.xlabel("k")
    plt.ylabel("Silhouette score")
    sil_path = os.path.join(outputs_dir, "silhouette_scores.png")
    plt.tight_layout()
    plt.savefig(sil_path, dpi=140)
    plt.close()

    plt.figure(figsize=(7, 4))
    plt.plot(result.k_grid, result.ch_scores, marker="o", color="tab:orange")
    plt.title("Calinski-Harabasz vs k")
    plt.xlabel("k")
    plt.ylabel("CH index")
    ch_path = os.path.join(outputs_dir, "ch_scores.png")
    plt.tight_layout()
    plt.savefig(ch_path, dpi=140)
    plt.close()

    return sil_path, ch_path


def plot_pca_scatter(
    X_scaled: np.ndarray, labels: np.ndarray, outputs_dir: str
) -> Tuple[str, str]:
    from sklearn.decomposition import PCA
    pca = PCA(n_components=2, random_state=42)
    X_2d = pca.fit_transform(X_scaled)

    plt.figure(figsize=(6, 5))
    scatter = plt.scatter(X_2d[:, 0], X_2d[:, 1], c=labels, cmap="viridis", s=10, alpha=0.7)
    plt.colorbar(scatter, label="cluster")
    plt.title("PCA (2D) - clusters")
    plt.xlabel("PC1")
    plt.ylabel("PC2")
    png_path = os.path.join(outputs_dir, "pca_scatter.png")
    plt.tight_layout()
    plt.savefig(png_path, dpi=140)
    plt.close()

    df_plot = pd.DataFrame({"pc1": X_2d[:, 0], "pc2": X_2d[:, 1], "cluster": labels})
    fig = px.scatter(df_plot, x="pc1", y="pc2", color=df_plot["cluster"].astype(str), title="PCA (2D) - clusters")
    html_path = os.path.join(outputs_dir, "pca_scatter.html")
    fig.write_html(html_path, include_plotlyjs="cdn")

    return png_path, html_path


def save_report(
    df: pd.DataFrame,
    feature_cols: List[str],
    result: ClusterSelectionResult,
    labels: np.ndarray,
    severity_map: Dict[int, str],
    outputs_dir: str,
    reports_dir: str,
) -> str:
    assignments = df.copy()
    assignments["cluster_id"] = labels
    assignments["severity"] = assignments["cluster_id"].map(severity_map)

    summary = assignments.groupby(["cluster_id", "severity"]).agg(
        count=(assignments.columns[0], "count")
    ).reset_index()

    assignments_path = os.path.join(outputs_dir, "cluster_assignments.csv")
    summary_path = os.path.join(outputs_dir, "cluster_summary.csv")
    assignments.to_csv(assignments_path, index=False)
    summary.to_csv(summary_path, index=False)

    summary_html = summary.to_html(index=False)

    sil_path = os.path.join(outputs_dir, "silhouette_scores.png")
    ch_path = os.path.join(outputs_dir, "ch_scores.png")
    pca_png_path = os.path.join(outputs_dir, "pca_scatter.png")
    pca_html_path = os.path.join(outputs_dir, "pca_scatter.html")

    report_path = os.path.join(reports_dir, "report.html")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(
            f"""
<!DOCTYPE html>
<html lang=\"pt-br\">
<head>
  <meta charset=\"UTF-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\" />
  <title>Relatório de Clusterização</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 24px; }}
    h1, h2, h3 {{ margin: 8px 0; }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 16px; }}
    img {{ width: 100%; height: auto; border: 1px solid #ddd; }}
    .meta {{ margin-bottom: 16px; }}
  </style>
</head>
<body>
  <h1>Clusterização por KMeans</h1>
  <div class=\"meta\">
    <p><b>Método de escolha de k:</b> {result.method}</p>
    <p><b>k escolhido:</b> {result.best_k}</p>
    <p><b>Score (método):</b> {result.best_score:.4f}</p>
    <p><b>Amostras:</b> {len(df)}</p>
    <p><b>Features:</b> {', '.join(feature_cols)}</p>
  </div>

  <h2>Gráficos de seleção de k</h2>
  <div class=\"grid\">
    <div>
      <img src=\"{os.path.relpath(sil_path, reports_dir)}\" alt=\"Silhouette vs k\" />
    </div>
    <div>
      <img src=\"{os.path.relpath(ch_path, reports_dir)}\" alt=\"Calinski-Harabasz vs k\" />
    </div>
  </div>

  <h2>Projeção PCA (2D)</h2>
  <div class=\"grid\">
    <div>
      <img src=\"{os.path.relpath(pca_png_path, reports_dir)}\" alt=\"PCA clusters\" />
    </div>
    <div>
      <a href=\"{os.path.relpath(pca_html_path, reports_dir)}\">Versão interativa (HTML)</a>
    </div>
  </div>

  <h2>Resumo por cluster</h2>
  {summary_html}

</body>
</html>
            """
        )

    return report_path


def save_artifacts(
    scaler: StandardScaler,
    model: KMeans,
    feature_cols: List[str],
    severity_map: Dict[int, str],
    result: ClusterSelectionResult,
    artifacts_dir: str,
) -> None:
    joblib.dump(scaler, os.path.join(artifacts_dir, "scaler.pkl"))
    joblib.dump(model, os.path.join(artifacts_dir, "kmeans.pkl"))
    metadata = {
        "feature_cols": feature_cols,
        "severity_map": {int(k): v for k, v in severity_map.items()},
        "model_selection": {
            "method": result.method,
            "best_k": result.best_k,
            "best_score": result.best_score,
        },
    }
    with open(os.path.join(artifacts_dir, "metadata.json"), "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)


def main() -> None:
    base_dir = os.path.dirname(__file__)
    dirs = ensure_dirs(base_dir)
    data_path = os.path.join(dirs["data"], "sensors.csv")

    df = load_dataset(data_path)
    feature_cols = select_feature_columns(df)

    X = df[feature_cols].to_numpy()
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    result = choose_k_with_silhouette_and_fallback(X_scaled)

    plot_and_save_scores(result, dirs["outputs"])

    model = fit_kmeans(X_scaled, n_clusters=result.best_k)
    labels = model.labels_

    severity_map = map_clusters_to_severity(X_scaled, labels, feature_cols)

    plot_pca_scatter(X_scaled, labels, dirs["outputs"])

    report_path = save_report(
        df=df,
        feature_cols=feature_cols,
        result=result,
        labels=labels,
        severity_map=severity_map,
        outputs_dir=dirs["outputs"],
        reports_dir=dirs["reports"],
    )

    save_artifacts(
        scaler=scaler,
        model=model,
        feature_cols=feature_cols,
        severity_map=severity_map,
        result=result,
        artifacts_dir=dirs["artifacts"],
    )

    print(
        f"[OK] k={result.best_k} via {result.method}. Relatório: {report_path}"
    )


if __name__ == "__main__":
    main()

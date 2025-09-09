#!/usr/bin/env python3
import argparse
import os
from datetime import datetime, timedelta
from typing import Tuple

import numpy as np
import pandas as pd


def build_synthetic_dataset(n_samples: int, random_state: int) -> pd.DataFrame:
    rng = np.random.default_rng(random_state)

    # Proporções alvo por severidade (bom/alerta/crítico)
    proportions = np.array([0.6, 0.25, 0.15])
    counts = (proportions * n_samples).astype(int)
    counts[0] += n_samples - counts.sum()  # ajustar total

    # Parâmetros por severidade alinhados ao domínio do projeto
    # Temperatura (°C): ideal 18-25, alerta 10-30, crítico fora disso
    temp_params = {
        "bom": (22.0, 1.5),
        "alerta": (27.0, 2.5),
        "critico": (35.0, 3.5),
    }
    # Umidade (%): ideal 30-70, alerta 20-80, crítico fora disso
    hum_params = {
        "bom": (55.0, 7.0),
        "alerta": (75.0, 6.0),
        "critico": (15.0, 8.0),
    }
    # Vibração digital (0/1): baixa incidência em bom, maior em alerta/crítico
    vib_p = {
        "bom": 0.03,
        "alerta": 0.15,
        "critico": 0.45,
    }
    # Luminosidade analógica (0-4095): ideal 300-3500; alerta nas bordas; crítico fora
    lum_params = {
        "bom": (1800.0, 500.0),
        "alerta": (3800.0, 300.0),
        "critico": (4200.0, 250.0),
    }

    labels_order = ["bom", "alerta", "critico"]
    parts = []

    for label, k in zip(labels_order, counts):
        temp = rng.normal(*temp_params[label], size=k)
        hum = rng.normal(*hum_params[label], size=k)
        vib = rng.binomial(n=1, p=vib_p[label], size=k).astype(int)
        lum = np.clip(rng.normal(*lum_params[label], size=k), 0, 4095).astype(int)

        part = pd.DataFrame(
            {
                "temperatura_c": temp,
                "umidade_pct": hum,
                "vibracao_digital": vib,
                "luminosidade_analogica": lum,
                "label_true": label,
            }
        )
        parts.append(part)

    df = pd.concat(parts, axis=0, ignore_index=True)

    # Embaralhar
    df = df.sample(frac=1.0, random_state=random_state).reset_index(drop=True)

    # Timestamp incremental (minutos)
    start_time = datetime(2024, 1, 1, 0, 0, 0)
    df.insert(
        0,
        "timestamp",
        [start_time + timedelta(minutes=i) for i in range(len(df))],
    )

    # Recortes de domínio
    df["temperatura_c"] = df["temperatura_c"].clip(-20, 80)
    df["umidade_pct"] = df["umidade_pct"].clip(0, 100)

    return df


def main() -> None:
    parser = argparse.ArgumentParser(description="Gerar dataset sintético alinhado ao ESP32")
    parser.add_argument("--n-samples", type=int, default=3000, help="Número de amostras a gerar")
    parser.add_argument("--random-state", type=int, default=42, help="Semente aleatória")
    parser.add_argument(
        "--output",
        type=str,
        default=os.path.join(os.path.dirname(__file__), "data", "sensors.csv"),
        help="Caminho do CSV de saída",
    )
    args = parser.parse_args()

    os.makedirs(os.path.dirname(args.output), exist_ok=True)

    df = build_synthetic_dataset(n_samples=args.n_samples, random_state=args.random_state)
    df.to_csv(args.output, index=False)

    print(f"[OK] Gerado: {args.output} — {len(df)} linhas")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
import argparse
import csv
import json
import os
import sys
import time
from typing import Dict, List

import joblib
import numpy as np
import pandas as pd
import serial


def load_artifacts(base_dir: str):
    artifacts_dir = os.path.join(base_dir, "artifacts")
    scaler = joblib.load(os.path.join(artifacts_dir, "scaler.pkl"))
    model = joblib.load(os.path.join(artifacts_dir, "kmeans.pkl"))
    with open(os.path.join(artifacts_dir, "metadata.json"), "r", encoding="utf-8") as f:
        metadata = json.load(f)
    feature_cols: List[str] = metadata["feature_cols"]
    severity_map: Dict[int, str] = {int(k): v for k, v in metadata["severity_map"].items()}
    return scaler, model, feature_cols, severity_map


def open_serial(port: str, baud: int, timeout: float) -> serial.Serial:
    return serial.Serial(port=port, baudrate=baud, timeout=timeout)


def parse_line_to_features(line: str, feature_cols: List[str]) -> pd.DataFrame:
    # Espera linha CSV com cabeçalho previamente enviado pelo firmware ou com as colunas na mesma ordem de feature_cols
    # Se houver cabeçalho explícito na stream, detectar e usar DictReader; senão, confiar na ordem
    parts = [p.strip() for p in line.strip().split(",")]
    if len(parts) != len(feature_cols):
        raise ValueError(f"Número de colunas incompatível. Esperado {len(feature_cols)}, recebido {len(parts)}. Linha: {line!r}")
    data = {c: [float(v)] for c, v in zip(feature_cols, parts)}
    return pd.DataFrame(data)


def main() -> None:
    base_dir = os.path.dirname(__file__)

    parser = argparse.ArgumentParser(description="Predição em tempo real via Serial")
    parser.add_argument("--port", required=True, help="Porta serial (ex.: /dev/ttyUSB0, /dev/ttyACM0)")
    parser.add_argument("--baud", type=int, default=115200, help="Baud rate")
    parser.add_argument("--timeout", type=float, default=1.0, help="Timeout de leitura (s)")
    parser.add_argument("--log", default=os.path.join(base_dir, "outputs", "serial_predictions.csv"), help="Arquivo CSV para log das predições")
    args = parser.parse_args()

    scaler, model, feature_cols, severity_map = load_artifacts(base_dir)

    os.makedirs(os.path.dirname(args.log), exist_ok=True)
    if not os.path.exists(args.log):
        with open(args.log, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([*feature_cols, "cluster_id", "severity", "ts"])

    print(f"[INFO] Abrindo {args.port} @ {args.baud}...")
    ser = open_serial(args.port, args.baud, args.timeout)
    print("[INFO] Lendo linhas. Ctrl+C para sair.")

    try:
        while True:
            raw = ser.readline().decode("utf-8", errors="ignore")
            if not raw:
                continue
            line = raw.strip()
            if not line:
                continue

            try:
                df = parse_line_to_features(line, feature_cols)
                X = df[feature_cols].to_numpy()
                X_scaled = scaler.transform(X)
                label = int(model.predict(X_scaled)[0])
                severity = severity_map.get(label, str(label))

                ts = int(time.time() * 1000)
                with open(args.log, "a", newline="", encoding="utf-8") as f:
                    writer = csv.writer(f)
                    writer.writerow([*(df.iloc[0][feature_cols].tolist()), label, severity, ts])

                print(f"{severity}\t(label={label})\t{line}")
            except Exception as e:
                print(f"[WARN] Linha inválida: {line!r} — {e}", file=sys.stderr)
    except KeyboardInterrupt:
        print("\n[INFO] Encerrado pelo usuário.")
    finally:
        try:
            ser.close()
        except Exception:
            pass


if __name__ == "__main__":
    main()

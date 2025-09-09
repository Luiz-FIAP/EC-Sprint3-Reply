#!/usr/bin/env python3
import argparse
import os
import time
import pandas as pd


def main() -> None:
    base_dir = os.path.dirname(__file__)
    parser = argparse.ArgumentParser(description="Simular streaming para o live_dashboard")
    parser.add_argument("--source", default=os.path.join(base_dir, "outputs", "predictions.csv"), help="CSV de origem (com severity)")
    parser.add_argument("--target", default=os.path.join(base_dir, "outputs", "serial_predictions.csv"), help="CSV de destino (lido pelo dashboard)")
    parser.add_argument("--delay", type=float, default=0.5, help="Intervalo entre linhas (s)")
    args = parser.parse_args()

    df = pd.read_csv(args.source)
    cols = list(df.columns) + ["ts"]

    os.makedirs(os.path.dirname(args.target), exist_ok=True)
    with open(args.target, "w", encoding="utf-8") as f:
        f.write(",".join(cols) + "\n")

    for _, row in df.iterrows():
        ts = int(time.time() * 1000)
        values = [str(row[c]) for c in df.columns] + [str(ts)]
        with open(args.target, "a", encoding="utf-8") as f:
            f.write(",".join(values) + "\n")
        time.sleep(args.delay)

    print(f"[OK] Simulação concluída. Arquivo: {args.target}")


if __name__ == "__main__":
    main()

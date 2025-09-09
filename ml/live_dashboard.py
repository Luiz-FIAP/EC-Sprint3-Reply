#!/usr/bin/env python3
import os
import time
from datetime import datetime

import pandas as pd
import plotly.express as px
import streamlit as st

BASE_DIR = os.path.dirname(__file__)
LOG_PATH = os.path.join(BASE_DIR, "outputs", "serial_predictions.csv")

# Colunas originais (sem ML)
SENSOR_COLS = [
    "timestamp",
    "temperatura_c",
    "umidade_pct",
    "vibracao_digital",
    "luminosidade_analogica",
]
# Colunas de predição
PRED_COLS = ["severity", "cluster_id"]

st.set_page_config(page_title="Predições em Tempo Real", layout="wide")
st.title("Predições em Tempo Real - Clusterização (KMeans)")

placeholder_meta = st.empty()
col1_area = st.empty()
col2_area = st.empty()
plot_area = st.empty()

def load_data(path: str) -> pd.DataFrame:
    if not os.path.exists(path):
        return pd.DataFrame()
    try:
        df = pd.read_csv(path)
    except Exception:
        return pd.DataFrame()
    # Tipagem e ordenação
    if "ts" in df.columns:
        df["ts_dt"] = pd.to_datetime(df["ts"], unit="ms", errors="coerce")
    else:
        df["ts_dt"] = pd.to_datetime("now")
    return df

refresh_sec = st.sidebar.slider("Refresh (s)", 0.5, 5.0, 1.0)
max_points = st.sidebar.number_input("Máx. pontos no gráfico", min_value=50, max_value=5000, value=1000, step=50)

last_size = 0

while True:
    df = load_data(LOG_PATH)

    if df.empty:
        placeholder_meta.info("Aguardando dados... Rode o stream_serial_predict.py para gerar serial_predictions.csv")
        time.sleep(refresh_sec)
        continue

    # Limitar pontos
    if len(df) > max_points:
        df_view = df.tail(int(max_points)).copy()
    else:
        df_view = df.copy()

    # Apenas colunas originais dos sensores para exibição principal + predições
    sensor_cols_present = [c for c in SENSOR_COLS if c in df_view.columns]
    pred_cols_present = [c for c in PRED_COLS if c in df_view.columns]
    display_cols = sensor_cols_present + pred_cols_present
    df_display = df_view[display_cols].copy()

    # Métricas
    total = len(df)
    last_row = df.iloc[-1]
    severity_counts = df["severity"].value_counts().to_dict() if "severity" in df.columns else {}

    with placeholder_meta.container():
        st.markdown(f"**Total de leituras**: {total}")
        last_sev = last_row.get("severity", "n/a")
        last_cluster = last_row.get("cluster_id", "n/a")
        st.markdown(f"**Última severidade**: {last_sev} | **Cluster**: {last_cluster} | **Horário**: {last_row.get('ts_dt')}")
        if severity_counts:
            st.write({k: int(v) for k, v in severity_counts.items()})

    # Gráfico temporal da severidade
    if "severity" in df_view.columns and "ts_dt" in df_view.columns:
        df_view["count"] = 1
        fig = px.scatter(df_view, x="ts_dt", y="severity", color="severity", title="Severidade ao longo do tempo", height=420)
        plot_area.plotly_chart(fig, use_container_width=True, key=f"plot-{int(time.time()*1000)}")

    # Duas colunas: tabela sensores+predições + resumo último com predição
    with col1_area.container():
        st.subheader("Janela recente (sensores + predição)")
        st.dataframe(df_display.tail(50))
    with col2_area.container():
        st.subheader("Último registro")
        last_summary = {c: last_row.get(c, None) for c in display_cols}
        st.json(last_summary)

    time.sleep(refresh_sec)

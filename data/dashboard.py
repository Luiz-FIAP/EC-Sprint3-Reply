import streamlit as st
import pandas as pd
import requests
import plotly.express as px

st.title("Dashboard de Sensores IoT (Oracle)")

# URL do endpoint Flask
API_URL = "http://localhost:8000/sensors?limit=100"

# Buscar dados
@st.cache_data(ttl=10)
def get_sensor_data():
    try:
        resp = requests.get(API_URL)
        resp.raise_for_status()
        data = resp.json()["data"]
        df = pd.DataFrame(data)
        # Converter datas
        for col in ["timestamp_read", "created_at"]:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col])
        return df
    except Exception as e:
        st.error(f"Erro ao buscar dados: {e}")
        return pd.DataFrame()

df = get_sensor_data()

if not df.empty:
    tipo = st.selectbox("Tipo de sensor", df["sensor_type"].unique())
    df_tipo = df[df["sensor_type"] == tipo]

    st.write(f"Últimos {len(df_tipo)} registros de {tipo}:")
    st.dataframe(df_tipo[["timestamp_read", "sensor_value"]].sort_values("timestamp_read", ascending=False))

    fig = px.line(df_tipo, x="timestamp_read", y="sensor_value", title=f"Evolução de {tipo}")
    st.plotly_chart(fig, use_container_width=True)
else:
    st.warning("Nenhum dado encontrado.") 
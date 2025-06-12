import streamlit as st
import pandas as pd
import requests
import plotly.express as px
from datetime import datetime, timedelta

st.set_page_config(page_title="Dashboard IoT - Sensores", layout="wide")

st.title("Dashboard de Sensores IoT (Oracle)")
st.markdown("""
Bem-vindo ao painel de monitoramento IoT!
Aqui você acompanha em tempo real as medições de **temperatura**, **umidade**, **vibração** e **luminosidade** coletadas pelo seu dispositivo ESP32.
""")

API_URL = "http://localhost:8000/sensors?limit=1000"

@st.cache_data(ttl=10)
def get_sensor_data():
    try:
        resp = requests.get(API_URL)
        resp.raise_for_status()
        data = resp.json()["data"]
        df = pd.DataFrame(data)
        for col in ["timestamp_read", "created_at"]:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors="coerce")
        return df
    except Exception as e:
        st.error(f"Erro ao buscar dados: {e}")
        return pd.DataFrame()

df = get_sensor_data()

# ====== Análises e Alertas de Não Conformidade ======
st.subheader("Análises e Alertas de Não Conformidade")
if not df.empty:
    # Umidade fora da faixa ideal (30-70%)
    df_hum = df[df["sensor_type"] == "humidity"]
    if not df_hum.empty:
        hum_out = df_hum[(df_hum["sensor_value"] < 30) | (df_hum["sensor_value"] > 70)]
        if not hum_out.empty:
            st.error(f"⚠️ {len(hum_out)} registros de umidade fora da faixa ideal (30-70%)!")
        else:
            st.success("Todos os valores de umidade estão dentro da faixa ideal.")
    # Luminosidade fora da faixa recomendada (300-3500)
    df_lux = df[df["sensor_type"] == "luminosity"]
    if not df_lux.empty:
        lux_out = df_lux[(df_lux["sensor_value"] < 300) | (df_lux["sensor_value"] > 3500)]
        if not lux_out.empty:
            st.warning(f"⚠️ {len(lux_out)} registros de luminosidade fora da faixa recomendada (300-3500)!")
        else:
            st.info("Luminosidade dentro da faixa recomendada.")
    # Vibração detectada
    df_vib = df[(df["sensor_type"] == "vibration") & (df["sensor_value"] == 1)]
    if not df_vib.empty:
        st.error(f"⚠️ {len(df_vib)} eventos de vibração detectados!")
    else:
        st.success("Nenhum evento de vibração detectado.")

# Filtro de período
periodo = st.selectbox("Período", ["Última hora", "Últimas 24h", "Tudo"])
if not df.empty:
    agora = datetime.now()
    if periodo == "Última hora":
        df = df[df["timestamp_read"] >= agora - timedelta(hours=1)]
    elif periodo == "Últimas 24h":
        df = df[df["timestamp_read"] >= agora - timedelta(hours=24)]

    # Cards de métricas rápidas
    def get_last(sensor):
        d = df[df["sensor_type"] == sensor]
        return d.sort_values("timestamp_read").iloc[-1]["sensor_value"] if not d.empty else "-"
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Última Temperatura (°C)", f"{get_last('temperature')}")
    col2.metric("Última Umidade (%)", f"{get_last('humidity')}")
    col3.metric("Última Luminosidade", f"{get_last('luminosity')}")
    vib = get_last('vibration')
    col4.metric("Última Vibração", "Sim" if vib == 1 else "Não" if vib == 0 else "-")

    st.divider()

    tab1, tab2, tab3, tab4 = st.tabs([
        "Linha: Temperatura/Umidade",
        "Barra: Média Luminosidade por Hora",
        "Dispersão: Temp vs Umidade",
        "Barra: Eventos de Vibração"
    ])

    with tab1:
        st.subheader("Temperatura e Umidade ao longo do tempo")
        df_temp = df[df["sensor_type"] == "temperature"]
        df_hum = df[df["sensor_type"] == "humidity"]
        fig = px.line()
        if not df_temp.empty:
            fig.add_scatter(x=df_temp["timestamp_read"], y=df_temp["sensor_value"], mode="lines+markers", name="Temperatura", line=dict(color="red"))
        if not df_hum.empty:
            fig.add_scatter(x=df_hum["timestamp_read"], y=df_hum["sensor_value"], mode="lines+markers", name="Umidade", line=dict(color="blue"))
        fig.update_layout(xaxis_title="Data/Hora", yaxis_title="Valor", legend_title="Grandeza")
        st.plotly_chart(fig, use_container_width=True)

    with tab2:
        st.subheader("Média de Luminosidade por Hora")
        df_lux = df[df["sensor_type"] == "luminosity"].copy()
        if not df_lux.empty:
            df_lux["hora"] = df_lux["timestamp_read"].dt.floor("H")
            df_lux_group = df_lux.groupby("hora")["sensor_value"].mean().reset_index()
            fig2 = px.bar(df_lux_group, x="hora", y="sensor_value", labels={"hora": "Hora", "sensor_value": "Luminosidade Média"}, title="Luminosidade Média por Hora", color="sensor_value", color_continuous_scale="YlOrBr")
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("Nenhum dado de luminosidade disponível.")

    with tab3:
        st.subheader("Dispersão: Temperatura vs. Umidade")
        df_temp = df[df["sensor_type"] == "temperature"]["sensor_value"].reset_index(drop=True).rename("temperature")
        df_hum = df[df["sensor_type"] == "humidity"]["sensor_value"].reset_index(drop=True).rename("humidity")
        if not df_temp.empty and not df_hum.empty and len(df_temp) == len(df_hum):
            df_disp = pd.concat([df_temp, df_hum], axis=1)
            fig3 = px.scatter(df_disp, x="temperature", y="humidity", title="Dispersão: Temperatura vs. Umidade", labels={"temperature": "Temperatura (°C)", "humidity": "Umidade (%)"}, color="temperature", color_continuous_scale="RdBu")
            st.plotly_chart(fig3, use_container_width=True)
        else:
            st.info("Dados insuficientes para dispersão.")

    with tab4:
        st.subheader("Eventos de Vibração por Hora")
        df_vib = df[(df["sensor_type"] == "vibration") & (df["sensor_value"] == 1)].copy()
        if not df_vib.empty:
            df_vib["hora"] = df_vib["timestamp_read"].dt.floor("H")
            df_vib_group = df_vib.groupby("hora").size().reset_index(name="eventos_vibracao")
            fig4 = px.bar(df_vib_group, x="hora", y="eventos_vibracao", labels={"hora": "Hora", "eventos_vibracao": "Eventos de Vibração"}, title="Contagem de Eventos de Vibração por Hora", color="eventos_vibracao", color_continuous_scale="Blues")
            st.plotly_chart(fig4, use_container_width=True)
        else:
            st.info("Nenhum evento de vibração detectado.")

    st.divider()
    st.subheader("Dados Recentes")
    st.dataframe(df.sort_values("timestamp_read", ascending=False).head(20), use_container_width=True)

    # ====== Relatório e Exportação ======
    st.divider()
    st.subheader("Relatório e Exportação")
    # Download dos dados em CSV
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="Baixar dados em CSV",
        data=csv,
        file_name='dados_sensores.csv',
        mime='text/csv',
    )
    # Resumo estatístico
    st.write("Resumo estatístico por tipo de sensor:")
    st.dataframe(df.groupby("sensor_type")["sensor_value"].describe(), use_container_width=True)
else:
    st.warning("Nenhum dado encontrado.") 
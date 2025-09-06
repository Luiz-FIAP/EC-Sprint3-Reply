import streamlit as st
import pandas as pd
import requests
import plotly.express as px
from datetime import datetime, timedelta

st.set_page_config(page_title="Dashboard IoT - Sensores", layout="wide")

st.title("Dashboard IoT")
st.markdown("""
**Sistema Integrado de Monitoramento IoT**

Acompanhe em tempo real as medições dos sensores conectados ao seu **ESP32**:
- **Temperatura** - DHT22
- **Umidade** - DHT22  
- **Vibração** - SW-420
- **Luminosidade** - LDR

**Dados armazenados automaticamente no Oracle Database com triggers automáticos!**
""")

API_URL = "http://localhost:8000/sensors?limit=1000"

@st.cache_data(ttl=10)
def get_sensor_data():
    try:
        resp = requests.get(API_URL)
        resp.raise_for_status()
        data = resp.json()["data"]
        df = pd.DataFrame(data)
        for col in ["timestamp", "created_at"]:
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
    # Verificar qualidade dos dados
    quality_counts = df['quality'].value_counts()
    if 'error' in quality_counts:
        st.error(f"🚨 {quality_counts['error']} registros com qualidade 'error'!")
    if 'warning' in quality_counts:
        st.warning(f"⚠️ {quality_counts['warning']} registros com qualidade 'warning'!")
    
    # Umidade fora da faixa ideal (30-70%)
    df_hum = df[df["sensor_type"] == "humidity"]
    if not df_hum.empty:
        hum_out = df_hum[(df_hum["sensor_value"] < 30) | (df_hum["sensor_value"] > 70)]
        if not hum_out.empty:
            st.error(f"⚠️ {len(hum_out)} registros de umidade fora da faixa ideal (30-70%)!")
        else:
            st.success("✅ Todos os valores de umidade estão dentro da faixa ideal.")
            
    # Temperatura fora da faixa ideal (18-25°C)
    df_temp = df[df["sensor_type"] == "temperature"]
    if not df_temp.empty:
        temp_out = df_temp[(df_temp["sensor_value"] < 18) | (df_temp["sensor_value"] > 25)]
        if not temp_out.empty:
            st.warning(f"⚠️ {len(temp_out)} registros de temperatura fora da faixa ideal (18-25°C)!")
        else:
            st.success("✅ Todos os valores de temperatura estão dentro da faixa ideal.")
            
    # Luminosidade fora da faixa recomendada (300-3500)
    df_lux = df[df["sensor_type"] == "luminosity"]
    if not df_lux.empty:
        lux_out = df_lux[(df_lux["sensor_value"] < 300) | (df_lux["sensor_value"] > 3500)]
        if not lux_out.empty:
            st.warning(f"⚠️ {len(lux_out)} registros de luminosidade fora da faixa recomendada (300-3500)!")
        else:
            st.info("ℹ️ Luminosidade dentro da faixa recomendada.")
            
    # Vibração detectada
    df_vib = df[(df["sensor_type"] == "vibration") & (df["sensor_value"] == 1)]
    if not df_vib.empty:
        st.error(f"🚨 {len(df_vib)} eventos de vibração detectados!")
    else:
        st.success("✅ Nenhum evento de vibração detectado.")

# Filtros expandidos
col1, col2 = st.columns(2)
with col1:
    periodo = st.selectbox("Período", ["Última hora", "Últimas 24h", "Tudo"])
with col2:
    if not df.empty and "device_name" in df.columns:
        devices = ["Todos"] + sorted(df["device_name"].unique().tolist())
        device_filter = st.selectbox("Dispositivo", devices)
    else:
        device_filter = "Todos"

if not df.empty:
    agora = datetime.now()
    if periodo == "Última hora":
        df = df[df["timestamp"] >= agora - timedelta(hours=1)]
    elif periodo == "Últimas 24h":
        df = df[df["timestamp"] >= agora - timedelta(hours=24)]
    
    # Aplicar filtro de dispositivo
    if device_filter != "Todos":
        df = df[df["device_name"] == device_filter]

    # Cards de métricas rápidas
    def get_last_value(sensor_type):
        d = df[df["sensor_type"] == sensor_type]
        if not d.empty:
            last_row = d.sort_values("timestamp").iloc[-1]
            return last_row["sensor_value"], last_row.get("quality", "unknown")
        return "-", "unknown"

    def get_device_info():
        if not df.empty and "device_name" in df.columns:
            devices = df["device_name"].unique()
            return f"{len(devices)} dispositivo(s): {', '.join(devices[:3])}{'...' if len(devices) > 3 else ''}"
        return "Dispositivo não identificado"

    col1, col2 = st.columns(2)
    with col1:
        st.metric("Dispositivo", get_device_info())
    with col2:
        total_readings = len(df) if not df.empty else 0
        st.metric("Total de Leituras", f"{total_readings}")

    col1, col2, col3, col4 = st.columns(4)
    temp_val, temp_qual = get_last_value('temperature')
    hum_val, hum_qual = get_last_value('humidity')
    lux_val, lux_qual = get_last_value('luminosity')
    vib_val, vib_qual = get_last_value('vibration')

    col1.metric("Última Temperatura (°C)", f"{temp_val}", delta=f"Q: {temp_qual}")
    col2.metric("Última Umidade (%)", f"{hum_val}", delta=f"Q: {hum_qual}")
    col3.metric("Última Luminosidade", f"{lux_val}", delta=f"Q: {lux_qual}")
    col4.metric("Última Vibração", "Sim" if vib_val == 1 else "Não" if vib_val == 0 else "-", delta=f"Q: {vib_qual}")

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
        
        # Adicionar cores baseadas na qualidade
        quality_colors = {"good": "green", "warning": "orange", "error": "red"}
        
        if not df_temp.empty:
            # Criar coluna de cor baseada na qualidade
            df_temp["color"] = df_temp["quality"].map(quality_colors).fillna("blue")
            fig.add_scatter(x=df_temp["timestamp"], y=df_temp["sensor_value"], 
                           mode="lines+markers", name="Temperatura", 
                           marker=dict(color=df_temp["color"]),
                           hovertemplate="%{x}<br>Temperatura: %{y}°C<br>Qualidade: %{customdata}<extra></extra>",
                           customdata=df_temp["quality"])
                           
        if not df_hum.empty:
            df_hum["color"] = df_hum["quality"].map(quality_colors).fillna("blue")
            fig.add_scatter(x=df_hum["timestamp"], y=df_hum["sensor_value"], 
                           mode="lines+markers", name="Umidade",
                           marker=dict(color=df_hum["color"]),
                           hovertemplate="%{x}<br>Umidade: %{y}%<br>Qualidade: %{customdata}<extra></extra>",
                           customdata=df_hum["quality"])
                           
        fig.update_layout(xaxis_title="Data/Hora", yaxis_title="Valor", legend_title="Sensor")
        st.plotly_chart(fig, use_container_width=True)

    with tab2:
        st.subheader("Luminosidade por Hora")
        df_lux = df[df["sensor_type"] == "luminosity"].copy()
        if not df_lux.empty:
            df_lux["hora"] = df_lux["timestamp"].dt.floor("H")
            df_lux_group = df_lux.groupby("hora")["sensor_value"].mean().reset_index()
            fig2 = px.bar(df_lux_group, x="hora", y="sensor_value", 
                     labels={"hora": "Hora", "sensor_value": "Luminosidade Média"}, 
                     title="Luminosidade Média por Hora", 
                     color="sensor_value", color_continuous_scale="YlOrBr")
            fig2.update_traces(hovertemplate="Hora: %{x}<br>Luminosidade: %{y:.0f}<extra></extra>")
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("Nenhum dado de luminosidade disponível.")

    with tab3:
        st.subheader("Dispersão: Temperatura vs. Umidade")
        df_temp = df[df["sensor_type"] == "temperature"]
        df_hum = df[df["sensor_type"] == "humidity"]
        
        if not df_temp.empty and not df_hum.empty:
            # Pegar timestamps comuns para alinhar os dados
            temp_times = set(df_temp["timestamp"])
            hum_times = set(df_hum["timestamp"])
            common_times = temp_times & hum_times
            
            if common_times:
                df_temp_common = df_temp[df_temp["timestamp"].isin(common_times)].copy()
                df_hum_common = df_hum[df_hum["timestamp"].isin(common_times)].copy()
                
                # Merge dos dados
                df_disp = pd.merge(df_temp_common[["timestamp", "sensor_value"]], 
                                 df_hum_common[["timestamp", "sensor_value"]], 
                                 on="timestamp", suffixes=("_temp", "_hum"))
                
                fig3 = px.scatter(df_disp, x="sensor_value_temp", y="sensor_value_hum", 
                                title="Dispersão: Temperatura vs. Umidade", 
                                labels={"sensor_value_temp": "Temperatura (°C)", "sensor_value_hum": "Umidade (%)"}, 
                                color="sensor_value_temp", color_continuous_scale="RdBu")
                fig3.update_traces(hovertemplate="Temperatura: %{x}°C<br>Umidade: %{y}%<extra></extra>")
                st.plotly_chart(fig3, use_container_width=True)
            else:
                st.info("Nenhum timestamp comum encontrado para dispersão.")
        else:
            st.info("Dados insuficientes para dispersão.")

    with tab4:
        st.subheader("Eventos de Vibração por Hora")
        df_vib = df[(df["sensor_type"] == "vibration") & (df["sensor_value"] == 1)].copy()
        if not df_vib.empty:
            df_vib["hora"] = df_vib["timestamp"].dt.floor("H")
            df_vib_group = df_vib.groupby("hora").size().reset_index(name="eventos_vibracao")
            fig4 = px.bar(df_vib_group, x="hora", y="eventos_vibracao", 
                         labels={"hora": "Hora", "eventos_vibracao": "Eventos de Vibração"}, 
                         title="Contagem de Eventos de Vibração por Hora", 
                         color="eventos_vibracao", color_continuous_scale="Blues")
            fig4.update_traces(hovertemplate="Hora: %{x}<br>Eventos: %{y}<extra></extra>")
            st.plotly_chart(fig4, use_container_width=True)
        else:
            st.info("Nenhum evento de vibração detectado.")

    st.divider()
    st.subheader("Dados Recentes")
    # Selecionar colunas mais relevantes para exibição
    display_cols = ["timestamp", "device_name", "sensor_name", "sensor_type", "sensor_value", "quality"]
    available_cols = [col for col in display_cols if col in df.columns]
    st.dataframe(df[available_cols].sort_values("timestamp", ascending=False).head(20), use_container_width=True)

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
    stats_df = df.groupby("sensor_type")["sensor_value"].describe()
    st.dataframe(stats_df, use_container_width=True)

    # Adicionar estatísticas de qualidade
    if "quality" in df.columns:
        st.write("Distribuição de Qualidade por Sensor:")
        quality_stats = df.groupby(["sensor_type", "quality"]).size().reset_index(name="count")
        st.dataframe(quality_stats.pivot(index="sensor_type", columns="quality", values="count").fillna(0), use_container_width=True)
else:
    st.warning("Nenhum dado encontrado.") 
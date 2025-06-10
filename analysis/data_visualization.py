#!/usr/bin/env python3
"""
Script de Visualização de Dados do Sistema de Monitoramento IoT

Este script lê os dados CSV gerados pelo ESP32 e cria gráficos
para análise dos padrões dos sensores.

Dependências:
- matplotlib
- pandas
- numpy

Uso:
    python data_visualization.py
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os
from datetime import datetime, timedelta

def load_data():
    """Carrega dados do arquivo CSV ou gera dados de exemplo"""
    csv_path = '../data/sensor_data.csv'
    
    if os.path.exists(csv_path):
        print(f"Carregando dados de {csv_path}")
        df = pd.read_csv(csv_path)
    else:
        print("Arquivo CSV não encontrado. Gerando dados de exemplo...")
        df = generate_sample_data()
        # Salva os dados de exemplo
        os.makedirs('../data', exist_ok=True)
        df.to_csv(csv_path, index=False)
        print(f"Dados de exemplo salvos em {csv_path}")
    
    return df

def generate_sample_data():
    """Gera dados de exemplo simulando o comportamento real dos sensores"""
    n_samples = 50
    timestamps = np.arange(0, n_samples * 2000, 2000)  # A cada 2 segundos
    
    data = []
    for i, ts in enumerate(timestamps):
        # Simula padrões realísticos
        time_hours = ts / 3600000.0
        
        # Temperatura: variação senoidal + ruído
        temp = 25.0 + 7.0 * np.sin(time_hours * 0.5) + np.random.normal(0, 1.5)
        temp = np.clip(temp, 15.0, 35.0)
        
        # Umidade: inversamente relacionada à temperatura
        humidity = 70.0 - (temp - 20.0) * 1.5 + np.random.normal(0, 3)
        humidity = np.clip(humidity, 30.0, 90.0)
        
        # Vibração: eventos esporádicos (15% de chance)
        vibration = 1 if np.random.random() < 0.15 else 0
        
        # Luminosidade: padrão dia/noite
        luminosity = 2000 + 1500 * np.sin(time_hours * 0.3) + np.random.normal(0, 150)
        luminosity = np.clip(luminosity, 0, 4095)
        
        data.append({
            'timestamp': int(ts),
            'temperatura_c': round(temp, 2),
            'umidade_pct': round(humidity, 1),
            'vibração_digital': vibration,
            'luminosidade_analogica': int(luminosity)
        })
    
    return pd.DataFrame(data)

def create_visualizations(df):
    """Cria gráficos de análise dos dados dos sensores"""
    
    # Configura o estilo dos gráficos
    plt.style.use('seaborn-v0_8')
    plt.rcParams['font.size'] = 10
    plt.rcParams['axes.grid'] = True
    
    # Converte timestamp para tempo relativo em segundos
    df['tempo_s'] = df['timestamp'] / 1000.0
    
    # Cria figura com subplots
    fig, axes = plt.subplots(2, 2, figsize=(15, 10))
    fig.suptitle('Sistema de Monitoramento IoT - Análise de Sensores', fontsize=16, fontweight='bold')
    
    # Subplot 1: Temperatura ao longo do tempo
    axes[0, 0].plot(df['tempo_s'], df['temperatura_c'], 'r-', linewidth=2, marker='o', markersize=4)
    axes[0, 0].set_title('Temperatura ao Longo do Tempo')
    axes[0, 0].set_xlabel('Tempo (s)')
    axes[0, 0].set_ylabel('Temperatura (°C)')
    axes[0, 0].grid(True, alpha=0.3)
    
    # Adiciona linha de média
    temp_mean = df['temperatura_c'].mean()
    axes[0, 0].axhline(y=temp_mean, color='red', linestyle='--', alpha=0.7, 
                      label=f'Média: {temp_mean:.1f}°C')
    axes[0, 0].legend()
    
    # Subplot 2: Umidade ao longo do tempo
    axes[0, 1].plot(df['tempo_s'], df['umidade_pct'], 'b-', linewidth=2, marker='s', markersize=4)
    axes[0, 1].set_title('Umidade ao Longo do Tempo')
    axes[0, 1].set_xlabel('Tempo (s)')
    axes[0, 1].set_ylabel('Umidade (%)')
    axes[0, 1].grid(True, alpha=0.3)
    
    # Adiciona linha de média
    hum_mean = df['umidade_pct'].mean()
    axes[0, 1].axhline(y=hum_mean, color='blue', linestyle='--', alpha=0.7,
                      label=f'Média: {hum_mean:.1f}%')
    axes[0, 1].legend()
    
    # Subplot 3: Luminosidade ao longo do tempo
    axes[1, 0].plot(df['tempo_s'], df['luminosidade_analogica'], 'y-', linewidth=2, marker='^', markersize=4)
    axes[1, 0].set_title('Luminosidade ao Longo do Tempo')
    axes[1, 0].set_xlabel('Tempo (s)')
    axes[1, 0].set_ylabel('Luminosidade (0-4095)')
    axes[1, 0].grid(True, alpha=0.3)
    
    # Adiciona linha de média
    lum_mean = df['luminosidade_analogica'].mean()
    axes[1, 0].axhline(y=lum_mean, color='orange', linestyle='--', alpha=0.7,
                      label=f'Média: {lum_mean:.0f}')
    axes[1, 0].legend()
    
    # Subplot 4: Eventos de vibração
    vibration_times = df[df['vibração_digital'] == 1]['tempo_s']
    axes[1, 1].scatter(vibration_times, [1] * len(vibration_times), 
                      c='red', s=100, marker='X', label='Vibração Detectada')
    axes[1, 1].set_title('Eventos de Vibração')
    axes[1, 1].set_xlabel('Tempo (s)')
    axes[1, 1].set_ylabel('Estado')
    axes[1, 1].set_ylim(-0.5, 1.5)
    axes[1, 1].set_yticks([0, 1])
    axes[1, 1].set_yticklabels(['Normal', 'Vibração'])
    axes[1, 1].grid(True, alpha=0.3)
    axes[1, 1].legend()
    
    # Adiciona informações estatísticas
    vibration_count = df['vibração_digital'].sum()
    total_count = len(df)
    vibration_percent = (vibration_count / total_count) * 100
    axes[1, 1].text(0.02, 0.98, f'Eventos: {vibration_count}/{total_count} ({vibration_percent:.1f}%)',
                   transform=axes[1, 1].transAxes, verticalalignment='top',
                   bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    
    plt.tight_layout()
    
    # Salva o gráfico
    os.makedirs('../docs/images', exist_ok=True)
    plt.savefig('../docs/images/sensor_analysis.png', dpi=300, bbox_inches='tight')
    print("Gráfico salvo em '../docs/images/sensor_analysis.png'")
    
    return fig

def print_statistics(df):
    """Imprime estatísticas descritivas dos dados"""
    print("\n" + "="*50)
    print("ESTATÍSTICAS DOS SENSORES")
    print("="*50)
    
    print(f"\n📊 RESUMO GERAL:")
    print(f"   • Total de medições: {len(df)}")
    print(f"   • Duração total: {df['timestamp'].max()/1000:.1f} segundos")
    print(f"   • Intervalo de coleta: {(df['timestamp'].iloc[1] - df['timestamp'].iloc[0])/1000:.1f}s")
    
    print(f"\n🌡️  TEMPERATURA:")
    print(f"   • Média: {df['temperatura_c'].mean():.2f}°C")
    print(f"   • Mínima: {df['temperatura_c'].min():.2f}°C")
    print(f"   • Máxima: {df['temperatura_c'].max():.2f}°C")
    print(f"   • Desvio padrão: {df['temperatura_c'].std():.2f}°C")
    
    print(f"\n💧 UMIDADE:")
    print(f"   • Média: {df['umidade_pct'].mean():.1f}%")
    print(f"   • Mínima: {df['umidade_pct'].min():.1f}%")
    print(f"   • Máxima: {df['umidade_pct'].max():.1f}%")
    print(f"   • Desvio padrão: {df['umidade_pct'].std():.2f}%")
    
    print(f"\n🔆 LUMINOSIDADE:")
    print(f"   • Média: {df['luminosidade_analogica'].mean():.0f}")
    print(f"   • Mínima: {df['luminosidade_analogica'].min()}")
    print(f"   • Máxima: {df['luminosidade_analogica'].max()}")
    print(f"   • Desvio padrão: {df['luminosidade_analogica'].std():.2f}")
    
    print(f"\n🔊 VIBRAÇÃO:")
    vibration_count = df['vibração_digital'].sum()
    total_count = len(df)
    vibration_percent = (vibration_count / total_count) * 100
    print(f"   • Eventos detectados: {vibration_count}/{total_count}")
    print(f"   • Percentual: {vibration_percent:.1f}%")
    
    print("="*50)

def main():
    """Função principal do script"""
    print("🚀 Sistema de Análise de Dados IoT")
    print("📈 Gerando visualizações dos sensores...\n")
    
    try:
        # Carrega os dados
        df = load_data()
        
        # Imprime estatísticas
        print_statistics(df)
        
        # Cria visualizações
        fig = create_visualizations(df)
        
        print("\n✅ Análise concluída com sucesso!")
        print("📋 Verifique o arquivo '../docs/images/sensor_analysis.png'")
        
        # Mostra o gráfico
        plt.show()
        
    except Exception as e:
        print(f"❌ Erro durante a análise: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main()) 
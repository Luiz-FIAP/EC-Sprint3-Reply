#!/usr/bin/env python3
"""
Script para simular leituras dos sensores IoT
Testa o sistema completo: ESP32 → Servidor → Oracle → Dashboard
"""

import requests
import time
import random
from datetime import datetime, timedelta
import json

# Configurações do servidor
SERVER_URL = "http://localhost:8000/data"

# IDs dos dispositivos e sensores (iguais aos do ESP32)
DEVICE_ID = "ESP32_001"
SENSOR_IDS = {
    "temperature": "ESP32_001_TEMP",
    "humidity": "ESP32_001_HUM", 
    "vibration": "ESP32_001_VIB",
    "luminosity": "ESP32_001_LUM"
}

def calculate_quality(sensor_type, value):
    """
    Calcula a qualidade baseada no valor do sensor (simulando ESP32)
    """
    if sensor_type == "temperature":
        if 18.0 <= value <= 25.0:
            return "good"
        elif 10.0 <= value <= 30.0:
            return "warning"
        else:
            return "error"
            
    elif sensor_type == "humidity":
        if 30.0 <= value <= 70.0:
            return "good"
        elif 20.0 <= value <= 80.0:
            return "warning"
        else:
            return "error"
            
    elif sensor_type == "vibration":
        return "critical" if value == 1 else "good"
        
    elif sensor_type == "luminosity":
        if 300 <= value <= 3500:
            return "good"
        elif 100 <= value <= 4000:
            return "warning"
        else:
            return "error"
    
    return "unknown"

def generate_sensor_reading(sensor_type, scenario="normal"):
    """
    Gera uma leitura simulada baseada no tipo de sensor e cenário
    """
    base_timestamp = int(time.time() * 1000)  # Timestamp em ms
    
    if sensor_type == "temperature":
        if scenario == "good":
            value = round(random.uniform(18.0, 25.0), 1)  # Faixa ideal
        elif scenario == "warning":
            value = round(random.uniform(10.0, 17.9), 1)  # Faixa warning baixa
        elif scenario == "error":
            value = round(random.uniform(-10.0, 9.9), 1)  # Faixa error
        else:  # normal (mistura)
            value = round(random.uniform(15.0, 35.0), 1)
            
    elif sensor_type == "humidity":
        if scenario == "good":
            value = round(random.uniform(30.0, 70.0), 1)  # Faixa ideal
        elif scenario == "warning":
            value = round(random.uniform(20.0, 29.9), 1)  # Faixa warning baixa
        elif scenario == "error":
            value = round(random.uniform(85.0, 95.0), 1)  # Faixa error alta
        else:  # normal (mistura)
            value = round(random.uniform(25.0, 85.0), 1)
            
    elif sensor_type == "vibration":
        if scenario == "critical":
            value = 1  # Vibração detectada
        else:
            value = 0  # Sem vibração
            
    elif sensor_type == "luminosity":
        if scenario == "good":
            value = random.randint(300, 3500)  # Faixa ideal
        elif scenario == "warning":
            value = random.randint(100, 299)  # Faixa warning baixa
        elif scenario == "error":
            value = random.randint(4000, 4095)  # Faixa error alta
        else:  # normal (mistura)
            value = random.randint(200, 3800)
    
    # Calcular qualidade baseada no valor gerado
    quality = calculate_quality(sensor_type, value)
    
    return {
        "sensor_id": SENSOR_IDS[sensor_type],
        "device_id": DEVICE_ID,
        "sensor_type": sensor_type,
        "sensor_value": value,
        "timestamp": base_timestamp,
        "quality": quality
    }

def send_reading(reading):
    """
    Envia uma leitura para o servidor
    """
    try:
        response = requests.post(SERVER_URL, json=reading, timeout=5)
        if response.status_code == 200:
            data = response.json()
            quality = data.get("data", {}).get("quality", "unknown")
            print(f"✅ {reading['sensor_type']}: {reading['sensor_value']} (Q: {quality})")
            return True
        else:
            print(f"❌ {reading['sensor_type']}: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ {reading['sensor_type']}: Erro - {e}")
        return False

def simulate_scenario(scenario_name, readings_count=10, delay=1.0):
    """
    Simula um cenário específico com múltiplas leituras
    """
    print(f"\n{'='*50}")
    print(f"🎯 CENÁRIO: {scenario_name.upper()}")
    print(f"📊 {readings_count} leituras por sensor")
    print(f"⏱️  Delay: {delay}s entre leituras")
    print(f"{'='*50}")
    
    sensors = ["temperature", "humidity", "vibration", "luminosity"]
    
    for i in range(readings_count):
        print(f"\n🔄 Leitura #{i+1}/{readings_count}")
        
        for sensor in sensors:
            reading = generate_sensor_reading(sensor, scenario_name.lower())
            send_reading(reading)
            
        if i < readings_count - 1:  # Não espera na última leitura
            time.sleep(delay)
    
    print(f"\n✅ Cenário '{scenario_name}' concluído!")

def simulate_time_series(hours=2, interval_minutes=5):
    """
    Simula uma série temporal realista
    """
    print(f"\n{'='*50}")
    print(f"🎯 SIMULAÇÃO TEMPORAL: {hours} horas")
    print(f"📊 Intervalo: {interval_minutes} minutos")
    print(f"{'='*50}")
    
    # Calcular número de leituras
    total_readings = int((hours * 60) / interval_minutes)
    
    for i in range(total_readings):
        print(f"\n🔄 Leitura temporal #{i+1}/{total_readings}")
        
        # Simular variação natural dos valores
        hour_of_day = (i * interval_minutes) % 24
        
        # Temperatura varia com o horário
        temp_scenario = "good" if 6 <= hour_of_day <= 22 else "warning"
        
        # Umidade varia aleatoriamente
        hum_scenario = random.choice(["good", "warning", "normal"])
        
        # Vibração rara (5% de chance)
        vib_scenario = "critical" if random.random() < 0.05 else "good"
        
        # Luminosidade baseada no horário
        if 6 <= hour_of_day <= 18:
            lux_scenario = "good"  # Dia
        elif hour_of_day in [5, 19]:
            lux_scenario = "warning"  # Amanhecer/Anoitecer
        else:
            lux_scenario = "error"  # Noite
        
        # Gerar leituras
        sensors_scenarios = {
            "temperature": temp_scenario,
            "humidity": hum_scenario,
            "vibration": vib_scenario,
            "luminosity": lux_scenario
        }
        
        for sensor, scenario in sensors_scenarios.items():
            reading = generate_sensor_reading(sensor, scenario)
            send_reading(reading)
            
        time.sleep(0.5)  # Pequena pausa entre leituras
    
    print(f"\n✅ Simulação temporal concluída!")

def main():
    """
    Menu principal para escolher tipo de simulação
    """
    print("🚀 SIMULADOR DE LEITURAS IoT")
    print("=" * 40)
    
    while True:
        print("\nEscolha o tipo de simulação:")
        print("1. Cenário GOOD (valores ideais)")
        print("2. Cenário WARNING (valores aceitáveis)")
        print("3. Cenário ERROR (valores críticos)")
        print("4. Cenário CRITICAL (vibração)")
        print("5. Cenário NORMAL (mistura realista)")
        print("6. Série Temporal (2 horas)")
        print("7. Teste Completo (todos os cenários)")
        print("0. Sair")
        
        try:
            choice = input("\nOpção: ").strip()
            
            if choice == "0":
                print("👋 Até logo!")
                break
                
            elif choice == "1":
                simulate_scenario("good", readings_count=5)
                
            elif choice == "2":
                simulate_scenario("warning", readings_count=5)
                
            elif choice == "3":
                simulate_scenario("error", readings_count=5)
                
            elif choice == "4":
                simulate_scenario("critical", readings_count=5)
                
            elif choice == "5":
                simulate_scenario("normal", readings_count=10)
                
            elif choice == "6":
                simulate_time_series(hours=1, interval_minutes=10)  # 1 hora para teste rápido
                
            elif choice == "7":
                print("\n🔄 EXECUTANDO TESTE COMPLETO...")
                simulate_scenario("good", readings_count=3)
                simulate_scenario("warning", readings_count=3)
                simulate_scenario("error", readings_count=3)
                simulate_scenario("critical", readings_count=3)
                print("\n✅ Teste completo finalizado!")
                
            else:
                print("❌ Opção inválida!")
                
        except KeyboardInterrupt:
            print("\n👋 Simulação interrompida pelo usuário!")
            break
        except Exception as e:
            print(f"❌ Erro: {e}")

if __name__ == "__main__":
    main()

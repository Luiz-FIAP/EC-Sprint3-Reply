#!/usr/bin/env python3
"""
Script para testar a API do servidor Flask
Testa requisições POST com dados JSON dos sensores
"""

import requests
import json
import time
import random

# Configurações
SERVER_URL = "http://localhost:8000"
DATA_ENDPOINT = f"{SERVER_URL}/data"
HEALTH_ENDPOINT = f"{SERVER_URL}/health"

def test_health():
    """Testa endpoint de saúde"""
    print("🏥 Testando endpoint de saúde...")
    try:
        response = requests.get(HEALTH_ENDPOINT)
        print(f"Status: {response.status_code}")
        print(f"Resposta: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Erro: {e}")
        return False

def send_sensor_data(sensor_type, sensor_value, timestamp=None):
    """Envia dados de sensor via POST"""
    if timestamp is None:
        timestamp = int(time.time() * 1000)  # milissegundos
    
    data = {
        "timestamp": timestamp,
        "sensor_type": sensor_type,
        "sensor_value": sensor_value
    }
    
    try:
        response = requests.post(
            DATA_ENDPOINT,
            json=data,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"📡 {sensor_type}: {sensor_value} | Status: {response.status_code}")
        
        if response.status_code == 200:
            print(f"✅ Resposta: {response.json()}")
            return True
        else:
            print(f"❌ Erro: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Erro na requisição: {e}")
        return False

def simulate_esp32_data():
    """Simula dados vindos do ESP32"""
    print("\n🤖 Simulando dados do ESP32...")
    
    # Dados simulados realísticos
    sensors_data = [
        ("temperature", round(random.uniform(18.0, 35.0), 2)),
        ("humidity", round(random.uniform(30.0, 90.0), 1)),
        ("vibration", random.choice([0, 1])),
        ("luminosity", random.randint(0, 4095))
    ]
    
    success_count = 0
    for sensor_type, value in sensors_data:
        if send_sensor_data(sensor_type, value):
            success_count += 1
        time.sleep(0.5)  # Pequena pausa entre envios
    
    print(f"\n📊 Resumo: {success_count}/{len(sensors_data)} dados enviados com sucesso")
    return success_count == len(sensors_data)

def test_invalid_requests():
    """Testa requisições inválidas para verificar validação"""
    print("\n🧪 Testando validações...")
    
    # Teste 1: Sem Content-Type correto
    print("1. Testando sem Content-Type JSON...")
    try:
        response = requests.post(DATA_ENDPOINT, data="invalid")
        print(f"   Status: {response.status_code} ✅" if response.status_code == 400 else f"   Status: {response.status_code} ❌")
    except:
        print("   ❌ Erro na requisição")
    
    # Teste 2: JSON inválido
    print("2. Testando dados incompletos...")
    try:
        response = requests.post(
            DATA_ENDPOINT,
            json={"sensor_type": "temperature"},  # Falta sensor_value
            headers={"Content-Type": "application/json"}
        )
        print(f"   Status: {response.status_code} ✅" if response.status_code == 400 else f"   Status: {response.status_code} ❌")
    except:
        print("   ❌ Erro na requisição")
    
    # Teste 3: Tipo de sensor inválido
    print("3. Testando tipo de sensor inválido...")
    try:
        response = requests.post(
            DATA_ENDPOINT,
            json={"sensor_type": "invalid_sensor", "sensor_value": 25.0},
            headers={"Content-Type": "application/json"}
        )
        print(f"   Status: {response.status_code} ✅" if response.status_code == 400 else f"   Status: {response.status_code} ❌")
    except:
        print("   ❌ Erro na requisição")

def main():
    print("🚀 Teste da API do Sistema de Monitoramento IoT")
    print("=" * 50)
    
    # 1. Testar saúde do servidor
    if not test_health():
        print("❌ Servidor não está funcionando. Verifique se está rodando.")
        return
    
    print("\n" + "=" * 50)
    
    # 2. Simular dados do ESP32
    simulate_esp32_data()
    
    print("\n" + "=" * 50)
    
    # 3. Testar validações
    test_invalid_requests()
    
    print("\n" + "=" * 50)
    print("✅ Testes concluídos!")
    print("💡 Para ver os dados no banco, use: curl http://localhost:8000/sensors")

if __name__ == "__main__":
    main() 
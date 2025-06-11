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
    """Testa requisições inválidas para verificar validação ANTES do banco"""
    print("\n🧪 Testando validações robustas...")
    
    test_cases = [
        {
            "name": "Sem Content-Type JSON",
            "request": lambda: requests.post(DATA_ENDPOINT, data="invalid"),
            "expected_status": 400
        },
        {
            "name": "JSON vazio",
            "request": lambda: requests.post(
                DATA_ENDPOINT,
                json={},
                headers={"Content-Type": "application/json"}
            ),
            "expected_status": 400
        },
        {
            "name": "Dados incompletos (sem sensor_value)",
            "request": lambda: requests.post(
                DATA_ENDPOINT,
                json={"sensor_type": "temperature"},
                headers={"Content-Type": "application/json"}
            ),
            "expected_status": 400
        },
        {
            "name": "Tipo de sensor inválido",
            "request": lambda: requests.post(
                DATA_ENDPOINT,
                json={"sensor_type": "invalid_sensor", "sensor_value": 25.0},
                headers={"Content-Type": "application/json"}
            ),
            "expected_status": 400
        },
        {
            "name": "Temperatura fora da faixa (-100°C)",
            "request": lambda: requests.post(
                DATA_ENDPOINT,
                json={"sensor_type": "temperature", "sensor_value": -100.0},
                headers={"Content-Type": "application/json"}
            ),
            "expected_status": 400
        },
        {
            "name": "Temperatura fora da faixa (150°C)",
            "request": lambda: requests.post(
                DATA_ENDPOINT,
                json={"sensor_type": "temperature", "sensor_value": 150.0},
                headers={"Content-Type": "application/json"}
            ),
            "expected_status": 400
        },
        {
            "name": "Umidade inválida (110%)",
            "request": lambda: requests.post(
                DATA_ENDPOINT,
                json={"sensor_type": "humidity", "sensor_value": 110.0},
                headers={"Content-Type": "application/json"}
            ),
            "expected_status": 400
        },
        {
            "name": "Vibração inválida (valor 5)",
            "request": lambda: requests.post(
                DATA_ENDPOINT,
                json={"sensor_type": "vibration", "sensor_value": 5},
                headers={"Content-Type": "application/json"}
            ),
            "expected_status": 400
        },
        {
            "name": "Luminosidade negativa",
            "request": lambda: requests.post(
                DATA_ENDPOINT,
                json={"sensor_type": "luminosity", "sensor_value": -100},
                headers={"Content-Type": "application/json"}
            ),
            "expected_status": 400
        },
        {
            "name": "Luminosidade acima do ADC (5000)",
            "request": lambda: requests.post(
                DATA_ENDPOINT,
                json={"sensor_type": "luminosity", "sensor_value": 5000},
                headers={"Content-Type": "application/json"}
            ),
            "expected_status": 400
        },
        {
            "name": "sensor_type não string",
            "request": lambda: requests.post(
                DATA_ENDPOINT,
                json={"sensor_type": 123, "sensor_value": 25.0},
                headers={"Content-Type": "application/json"}
            ),
            "expected_status": 400
        },
        {
            "name": "sensor_value não numérico",
            "request": lambda: requests.post(
                DATA_ENDPOINT,
                json={"sensor_type": "temperature", "sensor_value": "texto"},
                headers={"Content-Type": "application/json"}
            ),
            "expected_status": 400
        }
    ]
    
    passed = 0
    for i, test in enumerate(test_cases, 1):
        print(f"{i:2d}. {test['name']}...")
        try:
            response = test["request"]()
            if response.status_code == test["expected_status"]:
                print(f"    ✅ Status: {response.status_code}")
                passed += 1
            else:
                print(f"    ❌ Status: {response.status_code} (esperado: {test['expected_status']})")
                if response.status_code < 500:
                    try:
                        error_details = response.json()
                        print(f"    📄 Erro: {error_details.get('error', 'N/A')}")
                    except:
                        pass
        except Exception as e:
            print(f"    ❌ Erro na requisição: {e}")
    
    print(f"\n📊 Validações: {passed}/{len(test_cases)} passaram ({'✅' if passed == len(test_cases) else '⚠️'})")

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
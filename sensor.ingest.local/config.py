# Configurações do Sistema de Monitoramento IoT
# Centralizando configurações para facilitar manutenção

# === CONFIGURAÇÕES DO BANCO DE DADOS ORACLE ===
DB_CONFIG = {
    "user": "fiap",
    "password": "123456", 
    "dsn": "localhost:1521/FREEPDB1",
    "table_name": "sensor_readings"
}


# === CONFIGURAÇÕES DO SERVIDOR FLASK ===
SERVER_CONFIG = {
    "host": "0.0.0.0",
    "port": 8000,
    "debug": True
}

# === CONFIGURAÇÕES DOS SENSORES ===
SENSOR_CONFIG = {
    "valid_types": ["temperature", "humidity", "vibration", "luminosity"],
    "data_precision": 6,  # Casas decimais para valores (aumentado para maior precisão)
    "max_value_range": {
        "temperature": (-50.0, 100.0),
        "humidity": (0.0, 100.0), 
        "vibration": (0, 1),
        "luminosity": (0, 4095)
    }
}

# === CONFIGURAÇÕES DE QUERY ===
QUERY_CONFIG = {
    "default_limit": 100,
    "max_limit": 1000
} 
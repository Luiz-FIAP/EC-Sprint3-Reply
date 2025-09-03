

### **Modelo Conceitual - Visão Geral**

```
┌──────────────────────────────────────────────────────────────────────────┐
│                           SISTEMA IoT MONITOR                            │
│                          (Entidades Principais)                          │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌──────────────┐           ┌──────────────┐           ┌───────────────┐ │
│  │   DEVICES    │◄──────────┤   SENSORS    │◄──────────┤SENSOR_READINGS│ │
│  │              │ 1      N  │              │ 1      N  │               │ │
│  │ • device_id  │           │ • sensor_id  │           │ • reading_id  │ │
│  │ • device_name│           │ • device_id  │           │ • sensor_id   │ │
│  │ • device_type│           │ • sensor_type│           │ • timestamp   │ │
│  │ • location   │           │ • pin_number │           │ • sensor_value│ │
│  │ • status     │           │ • status     │           │ • quality     │ │
│  │ • created_at │           │ • created_at │           │ • created_at  │ │
│  └──────────────┘           └──────────────┘           └───────────────┘ │
│         │                               │                                │
│         │ 1                             │ 1                              │
│         ▼                               ▼                                │
│  ┌──────────────┐           ┌─────────────┐           ┌───────────────┐  │
│  │DEVICE_CONFIGS│           │SENSOR_TYPES │           │    ALERTS     │  │
│  │              │           │             │           │               │  │
│  │ • config_id  │           │ • type_id   │           │ • alert_id    │  │
│  │ • device_id  │           │ • type_name │           │ • sensor_id   │  │
│  │ • config_key │           │ • unit      │           │ • alert_type  │  │
│  │ • config_val │           │ • min_value │           │ • threshold   │  │
│  │ • updated_at │           │ • max_value │           │ • triggered_at│  │
│  └──────────────┘           └─────────────┘           └──────────────┘   │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

### **Legenda das Cardinalidades:**
- **1:1** = Um para um (obrigatório)
- **1:N** = Um para muitos
- **0:1** = Zero ou um (opcional)
- **0:N** = Zero ou muitos

## 📋 Definição Detalhada das Entidades

### **1. DEVICES** (Dispositivos IoT)
**Propósito**: Gerenciar dispositivos físicos ESP32 conectados ao sistema.

| Campo | Tipo | Restrições | Descrição |
|-------|------|------------|-----------|
| `device_id` | `VARCHAR2(50)` | **PK**, NOT NULL | Identificador único do dispositivo (ex: "ESP32_001") |
| `device_name` | `VARCHAR2(100)` | NOT NULL | Nome descritivo (ex: "Sensor Sala Servidores") |
| `device_type` | `VARCHAR2(50)` | NOT NULL, CHECK | Tipo: 'esp32', 'esp32-s2', 'esp32-s3', 'esp8266' |
| `location` | `VARCHAR2(200)` | NULL | Localização física (ex: "Data Center - Rack 5") |
| `ip_address` | `VARCHAR2(15)` | NULL | Endereço IP atual do dispositivo |
| `status` | `VARCHAR2(20)` | NOT NULL, DEFAULT 'active' | Status: 'active', 'inactive', 'maintenance' |
| `firmware_version` | `VARCHAR2(20)` | NULL | Versão do firmware instalado |
| `last_seen` | `TIMESTAMP` | NULL | Última comunicação registrada |
| `created_at` | `TIMESTAMP` | DEFAULT CURRENT_TIMESTAMP | Data de cadastro |
| `updated_at` | `TIMESTAMP` | DEFAULT CURRENT_TIMESTAMP | Última atualização |

### **2. SENSORS** (Sensores Individuais)
**Propósito**: Instâncias específicas de sensores em cada dispositivo.

| Campo | Tipo | Restrições | Descrição |
|-------|------|------------|-----------|
| `sensor_id` | `VARCHAR2(50)` | **PK**, NOT NULL | ID único do sensor (ex: "ESP32_001_TEMP") |
| `device_id` | `VARCHAR2(50)` | **FK**, NOT NULL | Referência ao dispositivo |
| `sensor_type` | `VARCHAR2(50)` | NOT NULL | Tipo: temperature, humidity, vibration, luminosity |
| `pin_number` | `NUMBER(3)` | NOT NULL | Pino GPIO do ESP32 (ex: 4, 2, 34) |
| `sensor_name` | `VARCHAR2(100)` | NOT NULL | Nome descritivo (ex: "DHT22 Temperatura") |
| `status` | `VARCHAR2(20)` | NOT NULL, DEFAULT 'active' | Status: 'active', 'inactive', 'error' |
| `calibration_offset` | `NUMBER(8,4)` | DEFAULT 0 | Offset de calibração |
| `sampling_interval` | `NUMBER(5)` | DEFAULT 3000 | Intervalo em ms (padrão 3s) |
| `created_at` | `TIMESTAMP` | DEFAULT CURRENT_TIMESTAMP | Data de criação |

### **3. SENSOR_TYPES** (Catálogo de Tipos)
**Propósito**: Metadados dos tipos de sensores suportados.

| Campo | Tipo | Restrições | Descrição |
|-------|------|------------|-----------|
| `type_id` | `VARCHAR2(50)` | **PK**, NOT NULL | Código do tipo (ex: "temperature") |
| `type_name` | `VARCHAR2(100)` | NOT NULL | Nome descritivo (ex: "Temperatura Ambiente") |
| `unit` | `VARCHAR2(20)` | NOT NULL | Unidade de medida (ex: "°C", "%", "digital") |
| `min_value` | `NUMBER(15,6)` | NULL | Valor mínimo válido |
| `max_value` | `NUMBER(15,6)` | NULL | Valor máximo válido |
| `precision_digits` | `NUMBER(2)` | DEFAULT 2 | Casas decimais para exibição |
| `description` | `VARCHAR2(500)` | NULL | Descrição técnica do sensor |
| `is_active` | `CHAR(1)` | DEFAULT 'Y' | Flag de tipo ativo |

### **4. SENSOR_READINGS** (Leituras dos Sensores)
**Propósito**: Armazenamento das medições coletadas.

| Campo | Tipo | Restrições | Descrição |
|-------|------|------------|-----------|
| `reading_id` | `NUMBER` | **PK**, AUTO_INCREMENT | ID sequencial da leitura |
| `sensor_id` | `VARCHAR2(50)` | **FK**, NOT NULL | Referência ao sensor |
| `timestamp` | `TIMESTAMP` | DEFAULT CURRENT_TIMESTAMP | Momento da leitura |
| `sensor_value` | `NUMBER(15,6)` | NOT NULL | Valor medido |
| `quality` | `VARCHAR2(20)` | DEFAULT 'good' | Qualidade: 'good', 'warning', 'error' |
| `raw_value` | `NUMBER(15,6)` | NULL | Valor bruto (antes calibração) |
| `created_at` | `TIMESTAMP` | DEFAULT CURRENT_TIMESTAMP | Timestamp de inserção |

### **5. ALERTS** (Sistema de Alertas)
**Propósito**: Gerenciamento de alertas e notificações.

| Campo | Tipo | Restrições | Descrição |
|-------|------|------------|-----------|
| `alert_id` | `NUMBER` | **PK**, AUTO_INCREMENT | ID único do alerta |
| `sensor_id` | `VARCHAR2(50)` | **FK**, NOT NULL | Sensor que gerou o alerta |
| `alert_type` | `VARCHAR2(50)` | NOT NULL | Tipo: 'threshold_high', 'threshold_low', 'error' |
| `threshold_value` | `NUMBER(15,6)` | NOT NULL | Valor limite que ativou o alerta |
| `actual_value` | `NUMBER(15,6)` | NOT NULL | Valor real medido |
| `severity` | `VARCHAR2(20)` | NOT NULL | Severidade: 'low', 'medium', 'high', 'critical' |
| `message` | `VARCHAR2(500)` | NOT NULL | Mensagem descritiva do alerta |
| `triggered_at` | `TIMESTAMP` | DEFAULT CURRENT_TIMESTAMP | Quando foi acionado |
| `acknowledged` | `CHAR(1)` | DEFAULT 'N' | Se foi reconhecido |
| `resolved_at` | `TIMESTAMP` | NULL | Quando foi resolvido |

### **6. DEVICE_CONFIGS** (Configurações por Dispositivo)
**Propósito**: Configurações específicas de cada dispositivo.

| Campo | Tipo | Restrições | Descrição |
|-------|------|------------|-----------|
| `config_id` | `NUMBER` | **PK**, AUTO_INCREMENT | ID único da configuração |
| `device_id` | `VARCHAR2(50)` | **FK**, NOT NULL | Dispositivo associado |
| `config_key` | `VARCHAR2(100)` | NOT NULL | Chave da configuração |
| `config_value` | `VARCHAR2(500)` | NOT NULL | Valor da configuração |
| `config_type` | `VARCHAR2(20)` | DEFAULT 'string' | Tipo: 'string', 'number', 'boolean' |
| `description` | `VARCHAR2(200)` | NULL | Descrição da configuração |
| `updated_at` | `TIMESTAMP` | DEFAULT CURRENT_TIMESTAMP | Última atualização |

## 🔒 Restrições de Integridade

### **Primary Keys (Chaves Primárias)**
```sql
-- Cada entidade tem sua chave primária única
ALTER TABLE devices ADD CONSTRAINT pk_devices PRIMARY KEY (device_id);
ALTER TABLE sensors ADD CONSTRAINT pk_sensors PRIMARY KEY (sensor_id);
ALTER TABLE sensor_types ADD CONSTRAINT pk_sensor_types PRIMARY KEY (type_id);
ALTER TABLE sensor_readings ADD CONSTRAINT pk_sensor_readings PRIMARY KEY (reading_id);
ALTER TABLE alerts ADD CONSTRAINT pk_alerts PRIMARY KEY (alert_id);
ALTER TABLE device_configs ADD CONSTRAINT pk_device_configs PRIMARY KEY (config_id);
```

### **Foreign Keys (Chaves Estrangeiras)**
```sql
-- Relacionamentos obrigatórios
ALTER TABLE sensors ADD CONSTRAINT fk_sensors_device 
    FOREIGN KEY (device_id) REFERENCES devices(device_id) ON DELETE CASCADE;

ALTER TABLE sensor_readings ADD CONSTRAINT fk_readings_sensor 
    FOREIGN KEY (sensor_id) REFERENCES sensors(sensor_id) ON DELETE CASCADE;

ALTER TABLE alerts ADD CONSTRAINT fk_alerts_sensor 
    FOREIGN KEY (sensor_id) REFERENCES sensors(sensor_id) ON DELETE CASCADE;

ALTER TABLE device_configs ADD CONSTRAINT fk_configs_device 
    FOREIGN KEY (device_id) REFERENCES devices(device_id) ON DELETE CASCADE;
```

### **Check Constraints (Validações)**
```sql
-- Validações de domínio
ALTER TABLE devices ADD CONSTRAINT chk_device_type 
    CHECK (device_type IN ('esp32', 'esp32-s2', 'esp32-s3', 'esp8266'));

ALTER TABLE devices ADD CONSTRAINT chk_device_status 
    CHECK (status IN ('active', 'inactive', 'maintenance'));

ALTER TABLE sensors ADD CONSTRAINT chk_sensor_type 
    CHECK (sensor_type IN ('temperature', 'humidity', 'vibration', 'luminosity'));

ALTER TABLE sensors ADD CONSTRAINT chk_sensor_status 
    CHECK (status IN ('active', 'inactive', 'error'));

ALTER TABLE sensor_readings ADD CONSTRAINT chk_reading_quality 
    CHECK (quality IN ('good', 'warning', 'error'));

ALTER TABLE alerts ADD CONSTRAINT chk_alert_type 
    CHECK (alert_type IN ('threshold_high', 'threshold_low', 'sensor_error', 'device_offline'));

ALTER TABLE alerts ADD CONSTRAINT chk_alert_severity 
    CHECK (severity IN ('low', 'medium', 'high', 'critical'));
```

## 🛠️ Script SQL Completo de Criação

```sql
-- ================================================================================
-- SISTEMA DE MONITORAMENTO IoT - BANCO DE DADOS ORACLE
-- Script completo de criação v2.0 - Modelo ER Expandido
-- ================================================================================

-- =====================================================
-- 1. TABELA: SENSOR_TYPES (Catálogo de tipos)
-- =====================================================
CREATE TABLE sensor_types (
    type_id VARCHAR2(50) PRIMARY KEY,
    type_name VARCHAR2(100) NOT NULL,
    unit VARCHAR2(20) NOT NULL,
    min_value NUMBER(15,6),
    max_value NUMBER(15,6),
    precision_digits NUMBER(2) DEFAULT 2,
    description VARCHAR2(500),
    is_active CHAR(1) DEFAULT 'Y' CHECK (is_active IN ('Y', 'N')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- 2. TABELA: DEVICES (Dispositivos IoT)
-- =====================================================
CREATE TABLE devices (
    device_id VARCHAR2(50) PRIMARY KEY,
    device_name VARCHAR2(100) NOT NULL,
    device_type VARCHAR2(50) NOT NULL 
        CHECK (device_type IN ('esp32', 'esp32-s2', 'esp32-s3', 'esp8266')),
    location VARCHAR2(200),
    ip_address VARCHAR2(15),
    status VARCHAR2(20) DEFAULT 'active' 
        CHECK (status IN ('active', 'inactive', 'maintenance')),
    firmware_version VARCHAR2(20),
    last_seen TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- 3. TABELA: SENSORS (Sensores individuais)
-- =====================================================
CREATE TABLE sensors (
    sensor_id VARCHAR2(50) PRIMARY KEY,
    device_id VARCHAR2(50) NOT NULL,
    sensor_type VARCHAR2(50) NOT NULL 
        CHECK (sensor_type IN ('temperature', 'humidity', 'vibration', 'luminosity')),
    pin_number NUMBER(3) NOT NULL,
    sensor_name VARCHAR2(100) NOT NULL,
    status VARCHAR2(20) DEFAULT 'active' 
        CHECK (status IN ('active', 'inactive', 'error')),
    calibration_offset NUMBER(8,4) DEFAULT 0,
    sampling_interval NUMBER(5) DEFAULT 3000,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Foreign Key
    CONSTRAINT fk_sensors_device FOREIGN KEY (device_id) 
        REFERENCES devices(device_id) ON DELETE CASCADE
);

-- =====================================================
-- 4. TABELA: SENSOR_READINGS (Leituras)
-- =====================================================
CREATE TABLE sensor_readings (
    reading_id NUMBER GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
    sensor_id VARCHAR2(50) NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    sensor_value NUMBER(15,6) NOT NULL,
    quality VARCHAR2(20) DEFAULT 'good' 
        CHECK (quality IN ('good', 'warning', 'error')),
    raw_value NUMBER(15,6),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Foreign Key
    CONSTRAINT fk_readings_sensor FOREIGN KEY (sensor_id) 
        REFERENCES sensors(sensor_id) ON DELETE CASCADE
);

-- =====================================================
-- 5. TABELA: ALERTS (Sistema de alertas)
-- =====================================================
CREATE TABLE alerts (
    alert_id NUMBER GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
    sensor_id VARCHAR2(50) NOT NULL,
    alert_type VARCHAR2(50) NOT NULL 
        CHECK (alert_type IN ('threshold_high', 'threshold_low', 'sensor_error', 'device_offline')),
    threshold_value NUMBER(15,6) NOT NULL,
    actual_value NUMBER(15,6) NOT NULL,
    severity VARCHAR2(20) NOT NULL 
        CHECK (severity IN ('low', 'medium', 'high', 'critical')),
    message VARCHAR2(500) NOT NULL,
    triggered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    acknowledged CHAR(1) DEFAULT 'N' CHECK (acknowledged IN ('Y', 'N')),
    resolved_at TIMESTAMP,
    
    -- Foreign Key
    CONSTRAINT fk_alerts_sensor FOREIGN KEY (sensor_id) 
        REFERENCES sensors(sensor_id) ON DELETE CASCADE
);

-- =====================================================
-- 6. TABELA: DEVICE_CONFIGS (Configurações)
-- =====================================================
CREATE TABLE device_configs (
    config_id NUMBER GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
    device_id VARCHAR2(50) NOT NULL,
    config_key VARCHAR2(100) NOT NULL,
    config_value VARCHAR2(500) NOT NULL,
    config_type VARCHAR2(20) DEFAULT 'string' 
        CHECK (config_type IN ('string', 'number', 'boolean')),
    description VARCHAR2(200),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Foreign Key
    CONSTRAINT fk_configs_device FOREIGN KEY (device_id) 
        REFERENCES devices(device_id) ON DELETE CASCADE,
    
    -- Unique constraint para chave por dispositivo
    CONSTRAINT uk_device_config UNIQUE (device_id, config_key)
);

-- =====================================================
-- 7. ÍNDICES PARA PERFORMANCE
-- =====================================================

-- Índices para DEVICES
CREATE INDEX idx_devices_status ON devices(status);
CREATE INDEX idx_devices_last_seen ON devices(last_seen DESC);

-- Índices para SENSORS
CREATE INDEX idx_sensors_device ON sensors(device_id);
CREATE INDEX idx_sensors_type ON sensors(sensor_type);
CREATE INDEX idx_sensors_status ON sensors(status);

-- Índices para SENSOR_READINGS (principais consultas)
CREATE INDEX idx_readings_sensor_timestamp ON sensor_readings(sensor_id, timestamp DESC);
CREATE INDEX idx_readings_timestamp ON sensor_readings(timestamp DESC);
CREATE INDEX idx_readings_quality ON sensor_readings(quality);

-- Índices para ALERTS
CREATE INDEX idx_alerts_sensor_triggered ON alerts(sensor_id, triggered_at DESC);
CREATE INDEX idx_alerts_severity ON alerts(severity);
CREATE INDEX idx_alerts_acknowledged ON alerts(acknowledged, triggered_at DESC);

-- =====================================================
-- 8. DADOS INICIAIS
-- =====================================================

-- Tipos de sensores suportados
INSERT INTO sensor_types (type_id, type_name, unit, min_value, max_value, precision_digits, description) VALUES
    ('temperature', 'Temperatura Ambiente', '°C', -50.0, 100.0, 2, 'Sensor DHT22 para temperatura ambiente'),
    ('humidity', 'Umidade Relativa', '%', 0.0, 100.0, 1, 'Sensor DHT22 para umidade relativa do ar'),
    ('vibration', 'Detector de Vibração', 'digital', 0, 1, 0, 'Sensor SW-420 para detecção de vibração'),
    ('luminosity', 'Sensor de Luminosidade', 'ADC', 0, 4095, 0, 'Sensor LDR com leitura analógica ESP32');

-- Dispositivo exemplo
INSERT INTO devices (device_id, device_name, device_type, location, status) VALUES
    ('ESP32_001', 'Sensor Sala Servidores', 'esp32', 'Data Center - Rack 5', 'active');

-- Sensores do dispositivo
INSERT INTO sensors (sensor_id, device_id, sensor_type, pin_number, sensor_name) VALUES
    ('ESP32_001_TEMP', 'ESP32_001', 'temperature', 4, 'DHT22 Temperatura'),
    ('ESP32_001_HUM', 'ESP32_001', 'humidity', 4, 'DHT22 Umidade'),
    ('ESP32_001_VIB', 'ESP32_001', 'vibration', 2, 'SW-420 Vibração'),
    ('ESP32_001_LUM', 'ESP32_001', 'luminosity', 34, 'LDR Luminosidade');

-- Configurações do dispositivo
INSERT INTO device_configs (device_id, config_key, config_value, config_type, description) VALUES
    ('ESP32_001', 'sampling_interval', '3000', 'number', 'Intervalo entre leituras em ms'),
    ('ESP32_001', 'wifi_ssid', 'Wokwi-GUEST', 'string', 'Rede WiFi para conexão'),
    ('ESP32_001', 'server_port', '8000', 'number', 'Porta do servidor de dados'),
    ('ESP32_001', 'ntp_enabled', 'true', 'boolean', 'Sincronização NTP ativa');

-- =====================================================
-- 9. VIEWS PARA CONSULTAS FREQUENTES
-- =====================================================

-- View completa dos dispositivos com seus sensores
CREATE OR REPLACE VIEW device_sensor_inventory AS
SELECT 
    d.device_id,
    d.device_name,
    d.device_type,
    d.location,
    d.status as device_status,
    d.last_seen,
    s.sensor_id,
    s.sensor_name,
    s.sensor_type,
    st.type_name,
    st.unit,
    s.status as sensor_status,
    s.pin_number,
    s.sampling_interval
FROM devices d
LEFT JOIN sensors s ON d.device_id = s.device_id
LEFT JOIN sensor_types st ON s.sensor_type = st.type_id
ORDER BY d.device_id, s.sensor_type;

-- View das últimas leituras por sensor
CREATE OR REPLACE VIEW latest_sensor_readings AS
SELECT sr.*
FROM sensor_readings sr
WHERE sr.timestamp = (
    SELECT MAX(sr2.timestamp)
    FROM sensor_readings sr2
    WHERE sr2.sensor_id = sr.sensor_id
);

-- View de estatísticas por sensor
CREATE OR REPLACE VIEW sensor_statistics AS
SELECT 
    s.sensor_id,
    s.sensor_name,
    s.sensor_type,
    st.type_name,
    st.unit,
    COUNT(sr.reading_id) as total_readings,
    ROUND(AVG(sr.sensor_value), st.precision_digits) as avg_value,
    ROUND(MIN(sr.sensor_value), st.precision_digits) as min_value,
    ROUND(MAX(sr.sensor_value), st.precision_digits) as max_value,
    ROUND(STDDEV(sr.sensor_value), st.precision_digits) as std_dev,
    MIN(sr.timestamp) as first_reading,
    MAX(sr.timestamp) as last_reading,
    COUNT(CASE WHEN sr.quality != 'good' THEN 1 END) as quality_issues
FROM sensors s
LEFT JOIN sensor_types st ON s.sensor_type = st.type_id
LEFT JOIN sensor_readings sr ON s.sensor_id = sr.sensor_id
GROUP BY s.sensor_id, s.sensor_name, s.sensor_type, st.type_name, st.unit, st.precision_digits;

-- =====================================================
-- 10. TRIGGERS PARA MANUTENÇÃO AUTOMÁTICA
-- =====================================================

-- Trigger para atualizar last_seen quando há nova leitura
CREATE OR REPLACE TRIGGER trg_update_device_last_seen
AFTER INSERT ON sensor_readings
FOR EACH ROW
DECLARE
    v_device_id VARCHAR2(50);
BEGIN
    -- Encontra o device_id através do sensor_id
    SELECT device_id INTO v_device_id
    FROM sensors 
    WHERE sensor_id = :NEW.sensor_id;
    
    -- Atualiza o last_seen do dispositivo
    UPDATE devices 
    SET last_seen = :NEW.timestamp, 
        updated_at = CURRENT_TIMESTAMP
    WHERE device_id = v_device_id;
END;
/

-- Trigger para alertas automáticos baseados em thresholds
CREATE OR REPLACE TRIGGER trg_auto_alerts
AFTER INSERT ON sensor_readings
FOR EACH ROW
DECLARE
    v_min_val NUMBER;
    v_max_val NUMBER;
    v_alert_type VARCHAR2(50);
BEGIN
    -- Busca os limites do tipo de sensor
    SELECT min_value, max_value 
    INTO v_min_val, v_max_val
    FROM sensor_types st
    JOIN sensors s ON st.type_id = s.sensor_type
    WHERE s.sensor_id = :NEW.sensor_id;
    
    -- Verifica se valor está fora dos limites
    IF :NEW.sensor_value < v_min_val THEN
        v_alert_type := 'threshold_low';
    ELSIF :NEW.sensor_value > v_max_val THEN
        v_alert_type := 'threshold_high';
    ELSE
        RETURN; -- Sai se estiver dentro dos limites
    END IF;
    
    -- Insere alerta
    INSERT INTO alerts (
        sensor_id, 
        alert_type, 
        threshold_value, 
        actual_value, 
        severity, 
        message
    ) VALUES (
        :NEW.sensor_id,
        v_alert_type,
        CASE WHEN v_alert_type = 'threshold_low' THEN v_min_val ELSE v_max_val END,
        :NEW.sensor_value,
        'high',
        'Valor ' || v_alert_type || ' detectado: ' || :NEW.sensor_value
    );
END;
/

-- =====================================================
-- 11. COMMIT FINAL
-- =====================================================
COMMIT;

-- =====================================================
-- VERIFICAÇÃO DA ESTRUTURA
-- =====================================================

-- Verificar tabelas criadas
SELECT table_name FROM user_tables 
WHERE table_name IN ('DEVICES', 'SENSORS', 'SENSOR_TYPES', 'SENSOR_READINGS', 'ALERTS', 'DEVICE_CONFIGS')
ORDER BY table_name;

-- Verificar estrutura das tabelas
SELECT 'Estrutura criada com sucesso!' as status FROM dual;
```

## 🎯 Benefícios do Modelo ER

### **Escalabilidade**
- Suporte a múltiplos dispositivos ESP32
- Fácil adição de novos tipos de sensores
- Configurações flexíveis por dispositivo

### **Integridade de Dados**
- Constraints rigorosas previnem dados inválidos
- Relacionamentos consistentes
- Triggers automáticos para manutenção

### **Performance**
- Índices otimizados para consultas típicas
- Views para acesso rápido a dados agregados
- Estrutura preparada para alto volume de dados

### **Manutenibilidade**
- Modelo normalizado evita redundância
- Configurações separadas facilitam ajustes
- Sistema de alertas automático

Este DER representa um sistema IoT robusto e profissional, preparado para cenários reais de monitoramento com ESP32 e múltiplos sensores.

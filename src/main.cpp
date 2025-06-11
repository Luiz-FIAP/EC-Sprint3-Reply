/*
 * Sistema de Monitoramento IoT com ESP32
 * 
 * Sensores utilizados:
 * - DHT22: Temperatura e umidade (pino D4)
 * - SW-420: Sensor de vibração (pino D2)
 * - LDR: Sensor de luminosidade (pino A0)
 * 
 * Funcionalidades:
 * - Leitura de sensores a cada 10 segundos
 * - Simulação de valores realistas
 * - Envio via HTTP POST para servidor Flask
 * - Fallback para saída CSV se não conectar WiFi
 */

#include <Arduino.h>
#include <DHT.h>
#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include <math.h>

// *** Configurações WiFi ***
const char* ssid = "Wokwi-GUEST";      // Para simulação Wokwi
const char* password = "";              // Sem senha no Wokwi
// Para uso real, substitua por suas credenciais:
// const char* ssid = "SUA_REDE_WIFI";
// const char* password = "SUA_SENHA_WIFI";

// *** Configurações do Servidor ***
const char* serverURL = "http://localhost:8000/data";  // URL do servidor Flask
// Para teste local, use: "http://192.168.1.100:8000/data" (IP do seu computador)

// Definições de pinos
#define DHT_PIN 4
#define VIBRATION_PIN 2
#define LDR_PIN 34  // GPIO36 para ADC no ESP32

// Configuração do sensor DHT22
#define DHT_TYPE DHT22
DHT dht(DHT_PIN, DHT_TYPE);

// Variáveis para controle de tempo
unsigned long lastReadTime = 0;
const unsigned long READ_INTERVAL = 10000; // 10 segundos (mais adequado para IoT)

// Variáveis para geração de dados realísticos
float baseTemperature = 25.0;
int baseLuminosity = 2000;
unsigned long startTime;
int measurementCount = 0;

// Controle de conexão
bool wifiConnected = false;
bool csvHeaderPrinted = false;

// Declaração da estrutura de dados dos sensores
struct SensorData {
  float temperature;
  float humidity;
  int vibration;
  int luminosity;
  unsigned long timestamp;
};

// Declarações das funções
void setupWiFi();
SensorData readSensors();
bool sendDataToServer(SensorData data);
void printCSVData(SensorData data);
void printDebugData(SensorData data);

void setup() {
  Serial.begin(115200);
  
  // Inicialização dos sensores
  dht.begin();
  pinMode(VIBRATION_PIN, INPUT);
  pinMode(LDR_PIN, INPUT);
  
  startTime = millis();
  
  Serial.println("=== Sistema de Monitoramento IoT ===");
  Serial.println("ESP32 com 3 sensores + conectividade WiFi");
  Serial.println();
  
  // Configurar WiFi
  setupWiFi();
  
  Serial.println("Iniciando coleta e envio de dados...\n");
  delay(2000); // Aguarda estabilização dos sensores
}

void loop() {
  unsigned long currentTime = millis();
  
  if (currentTime - lastReadTime >= READ_INTERVAL) {
    lastReadTime = currentTime;
    measurementCount++;
    
    // Leitura dos sensores
    SensorData data = readSensors();
    
    // Tentar enviar para o servidor se conectado
    bool dataSent = false;
    if (wifiConnected && WiFi.status() == WL_CONNECTED) {
      dataSent = sendDataToServer(data);
      
      if (dataSent) {
        Serial.printf("✅ [%d] Dados enviados com sucesso!\n", measurementCount);
      } else {
        Serial.printf("❌ [%d] Falha ao enviar dados\n", measurementCount);
      }
    } else {
      Serial.printf("📶 [%d] WiFi desconectado - salvando localmente\n", measurementCount);
    }
    
    // Fallback: salvar em formato CSV se não conseguir enviar
    if (!dataSent) {
      if (!csvHeaderPrinted) {
        Serial.println("\n=== DADOS CSV (BACKUP) ===");
        Serial.println("timestamp,temperatura_c,umidade_pct,vibracao_digital,luminosidade_analogica");
        csvHeaderPrinted = true;
      }
      printCSVData(data);
    }
    
    // Debug a cada 5 medições
    if (measurementCount % 5 == 0) {
      printDebugData(data);
    }
    
    // Para simulação infinita, comente as linhas abaixo
    if (measurementCount >= 100) {
      Serial.println("\n=== Simulação finalizada ===");
      Serial.println("100 medições processadas!");
      Serial.println("Sistema entrando em modo de espera...");
      
      // Continua enviando dados em intervalo maior
      delay(30000); // 30 segundos
      measurementCount = 0; // Reinicia contador
    }
  }
  
  // Verificar reconexão WiFi se perdeu conexão
  if (wifiConnected && WiFi.status() != WL_CONNECTED) {
    Serial.println("⚠️  Conexão WiFi perdida, tentando reconectar...");
    setupWiFi();
  }
}

void setupWiFi() {
  Serial.print("🔌 Conectando ao WiFi");
  WiFi.begin(ssid, password);
  
  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 20) {
    delay(500);
    Serial.print(".");
    attempts++;
  }
  
  if (WiFi.status() == WL_CONNECTED) {
    wifiConnected = true;
    Serial.println();
    Serial.println("✅ WiFi conectado com sucesso!");
    Serial.print("📍 IP: ");
    Serial.println(WiFi.localIP());
    Serial.print("📡 Servidor: ");
    Serial.println(serverURL);
  } else {
    wifiConnected = false;
    Serial.println();
    Serial.println("❌ Falha na conexão WiFi");
    Serial.println("📝 Modo offline: dados serão salvos em CSV");
  }
  Serial.println();
}

bool sendDataToServer(SensorData data) {
  HTTPClient http;
  http.begin(serverURL);
  http.addHeader("Content-Type", "application/json");
  
  // Criar JSON com os dados
  DynamicJsonDocument jsonDoc(200);
  jsonDoc["timestamp"] = data.timestamp;
  jsonDoc["sensor_type"] = "temperature";
  jsonDoc["sensor_value"] = data.temperature;
  
  String jsonString;
  serializeJson(jsonDoc, jsonString);
  
  // Enviar temperatura
  int httpResponseCode = http.POST(jsonString);
  bool success = (httpResponseCode == 200);
  
  if (!success) {
    Serial.printf("⚠️  Erro HTTP: %d\n", httpResponseCode);
    if (httpResponseCode > 0) {
      String response = http.getString();
      Serial.println("Resposta: " + response);
    }
  }
  
  http.end();
  
  // Enviar dados adicionais (umidade, vibração, luminosidade)
  if (success) {
    // Umidade
    jsonDoc["sensor_type"] = "humidity";
    jsonDoc["sensor_value"] = data.humidity;
    serializeJson(jsonDoc, jsonString);
    http.begin(serverURL);
    http.addHeader("Content-Type", "application/json");
    http.POST(jsonString);
    http.end();
    
    // Vibração
    jsonDoc["sensor_type"] = "vibration";
    jsonDoc["sensor_value"] = data.vibration;
    serializeJson(jsonDoc, jsonString);
    http.begin(serverURL);
    http.addHeader("Content-Type", "application/json");
    http.POST(jsonString);
    http.end();
    
    // Luminosidade
    jsonDoc["sensor_type"] = "luminosity";
    jsonDoc["sensor_value"] = data.luminosity;
    serializeJson(jsonDoc, jsonString);
    http.begin(serverURL);
    http.addHeader("Content-Type", "application/json");
    http.POST(jsonString);
    http.end();
  }
  
  return success;
}

SensorData readSensors() {
  SensorData data;
  data.timestamp = millis();
  
  // === SENSOR DHT22 (Temperatura e Umidade) ===
  // Simula variação diária realística
  float timeHours = (millis() - startTime) / 3600000.0;
  
  // Temperatura: varia entre 18°C e 32°C com padrão senoidal
  data.temperature = baseTemperature + 
                    7.0 * sin(timeHours * 0.5) + 
                    random(-200, 200) / 100.0; // Ruído
  
  // Umidade: inversamente relacionada à temperatura
  data.humidity = 70.0 - (data.temperature - 20.0) * 1.5 + 
                  random(-300, 300) / 100.0;
  
  // Limita os valores dentro de faixas realísticas
  data.temperature = constrain(data.temperature, 15.0, 35.0);
  data.humidity = constrain(data.humidity, 30.0, 90.0);
  
  // === SENSOR SW-420 (Vibração) ===
  // Simula detecção esporádica de vibração
  int vibrationChance = random(0, 100);
  if (vibrationChance < 15) { // 15% de chance de vibração
    data.vibration = 1; // Vibração detectada
  } else {
    data.vibration = 0; // Sem vibração
  }
  
  // === SENSOR LDR (Luminosidade) ===
  // Simula variação dia/noite
  float dayNightCycle = sin(timeHours * 0.3); // Ciclo mais lento
  data.luminosity = baseLuminosity + 
                   1500 * dayNightCycle + 
                   random(-200, 200); // Ruído
  
  // Limita valores do ADC (0-4095 para ESP32)
  data.luminosity = constrain(data.luminosity, 0, 4095);
  
  return data;
}

void printCSVData(SensorData data) {
  Serial.print(data.timestamp);
  Serial.print(",");
  Serial.print(data.temperature, 2);
  Serial.print(",");
  Serial.print(data.humidity, 1);
  Serial.print(",");
  Serial.print(data.vibration);
  Serial.print(",");
  Serial.println(data.luminosity);
}

void printDebugData(SensorData data) {
  Serial.println("\n--- Status dos Sensores ---");
  Serial.printf("📊 Medição #%d | ⏰ %lus\n", measurementCount, data.timestamp / 1000);
  Serial.printf("🌡️  Temperatura: %.1f°C\n", data.temperature);
  Serial.printf("💧 Umidade: %.1f%%\n", data.humidity);
  Serial.printf("📳 Vibração: %s\n", data.vibration ? "DETECTADA" : "Normal");
  Serial.printf("💡 Luminosidade: %d (0-4095)\n", data.luminosity);
  Serial.printf("📶 WiFi: %s | 📡 RSSI: %ddBm\n", 
                wifiConnected ? "Conectado" : "Desconectado", 
                wifiConnected ? WiFi.RSSI() : 0);
  Serial.println("---------------------------\n");
} 
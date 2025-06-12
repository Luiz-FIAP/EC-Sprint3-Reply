/*
 * Sistema de Monitoramento IoT com ESP32
 * 
 * Sensores utilizados:
 * - DHT22: Temperatura e umidade (pino D4)
 * - SW-420: Sensor de vibração (pino D2)
 * - LDR: Sensor de luminosidade (pino A0)
 * 
 * Funcionalidades:
 * - Leitura e envio automático a cada 3 segundos
 * - Envio via HTTP POST para servidor Flask
 * - Simulação de valores realistas
 * - Fallback para saída CSV se não conectar WiFi
 */

#include <Arduino.h>
#include <DHT.h>
#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include <math.h>
#include <time.h>  // Adicionado para suporte a NTP

// *** Configurações WiFi ***
const char* ssid = "Wokwi-GUEST";      // Para simulação Wokwi
const char* password = "";              // Sem senha no Wokwi
// Para uso real, substitua por suas credenciais:
// const char* ssid = "SUA_REDE_WIFI";
// const char* password = "SUA_SENHA_WIFI";

// *** Configurações do Servidor ***
const char* serverURL = "http://192.168.160.1:8000/data";  // URL do servidor Flask
// IP local detectado automaticamente para conexão do Wokwi
// Para teste local com localhost: "http://localhost:8000/data"

// *** Configurações NTP ***
const char* ntpServer = "pool.ntp.org";
const char* ntpServer2 = "time.google.com";  // Servidor backup
const long  gmtOffset_sec = -3 * 3600;  // GMT-3 para Brasil
const int   daylightOffset_sec = 0;

// Definições de pinos
#define DHT_PIN 4
#define VIBRATION_PIN 2
#define LDR_PIN 34  // GPIO34 para ADC no ESP32

// Configuração do sensor DHT22
#define DHT_TYPE DHT22
DHT dht(DHT_PIN, DHT_TYPE);

// Variáveis para controle de tempo
unsigned long lastSendTime = 0;
const unsigned long SEND_INTERVAL = 3000;    // Envia dados a cada 3 segundos

// Variável para controle de tempo de inicialização
unsigned long startTime;
int measurementCount = 0;

// Controle de conexão e NTP
bool wifiConnected = false;
bool ntpSynced = false;
bool csvHeaderPrinted = false;

// Declaração da estrutura de dados dos sensores
struct SensorData {
  time_t timestamp;  // Alterado para time_t
  float temperature;
  float humidity;
  int vibration;
  int luminosity;
};

// Declarações das funções
void setupWiFi();
void setupNTP();
bool syncNTP();
SensorData readSensors();
bool sendDataToServer(SensorData data);
void printCSVData(SensorData data);
void printDebugData(SensorData data);

void setup() {
  Serial.begin(115200);
  
  // Inicialização dos sensores
  dht.begin();
  pinMode(VIBRATION_PIN, INPUT_PULLUP);  // Pull-up interno para botão
  pinMode(LDR_PIN, INPUT);
  
  startTime = millis();
  
  Serial.println("=== Sistema de Monitoramento IoT Automático ===");
  Serial.println("ESP32 com 3 sensores + envio automático a cada 3s");
  Serial.println("📡 Dados enviados automaticamente para o servidor!");
  Serial.println();
  
  // Configurar WiFi
  setupWiFi();
  
  // Configurar NTP após conectar WiFi
  if (wifiConnected) {
    setupNTP();
  }
  
  // Aguardar sincronização NTP antes de continuar
  int ntpRetries = 0;
  while (!ntpSynced && ntpRetries < 5) {
    Serial.println("🔄 Tentando sincronizar NTP novamente...");
    setupNTP();
    ntpRetries++;
    delay(1000);
  }
  
  if (!ntpSynced) {
    Serial.println("⚠️ AVISO: NTP não sincronizado. Timestamps podem estar incorretos!");
  }
  
  Serial.println("Iniciando coleta e envio automático de dados...");
  Serial.printf("⏰ Intervalo de envio: %d segundos\n", SEND_INTERVAL / 1000);
  Serial.println();
  delay(2000); // Aguarda estabilização dos sensores
}

void loop() {
  unsigned long currentTime = millis();
  
  // Tentar sincronizar NTP periodicamente se não estiver sincronizado
  static unsigned long lastNTPSync = 0;
  if (!ntpSynced && (currentTime - lastNTPSync >= 30000)) {  // Tenta a cada 30 segundos
    lastNTPSync = currentTime;
    setupNTP();
  }
  
  // Envio automático a cada 3 segundos
  if (currentTime - lastSendTime >= SEND_INTERVAL) {
    lastSendTime = currentTime;
    measurementCount++;
    
    // Só envia dados se o NTP estiver sincronizado
    if (ntpSynced) {
      // Leitura dos sensores
      SensorData data = readSensors();
      
      Serial.printf("📊 [Medição #%d] Coletando dados dos sensores...\n", measurementCount);
      
      // Tentar enviar para o servidor se conectado
      bool dataSent = false;
      if (wifiConnected && WiFi.status() == WL_CONNECTED) {
        Serial.println("📡 Enviando dados para servidor...");
        dataSent = sendDataToServer(data);
        
        if (dataSent) {
          Serial.printf("✅ [#%d] Dados enviados com SUCESSO!\n", measurementCount);
          Serial.println("🎉 Todos os sensores enviados ao servidor!");
        } else {
          Serial.printf("❌ [#%d] Falha ao enviar dados para servidor\n", measurementCount);
          Serial.println("💾 Salvando dados localmente...");
        }
      } else {
        Serial.printf("📶 [#%d] WiFi desconectado - salvando localmente\n", measurementCount);
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
      
      // Debug a cada medição
      printDebugData(data);
      
      Serial.println("⏳ Aguardando próximo envio em 3 segundos...\n");
    } else {
      Serial.println("⚠️ Aguardando sincronização NTP antes de enviar dados...");
    }
  }
  
  // Verificar reconexão WiFi se perdeu conexão
  if (wifiConnected && WiFi.status() != WL_CONNECTED) {
    Serial.println("⚠️ Conexão WiFi perdida, tentando reconectar...");
    setupWiFi();
    if (wifiConnected) {
      setupNTP();  // Tenta sincronizar NTP novamente após reconexão
    }
  }
  
  delay(100);
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
  JsonDocument jsonDoc;
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
  
  // Obter timestamp atual
  struct tm timeinfo;
  if (getLocalTime(&timeinfo)) {
    data.timestamp = mktime(&timeinfo);
    // Verificar se o timestamp é válido (posterior a 2024)
    if (data.timestamp < 1704067200) { // 1 Jan 2024 00:00:00
      Serial.println("⚠️ Timestamp inválido detectado, tentando ressincronizar NTP...");
      setupNTP();
      getLocalTime(&timeinfo);
      data.timestamp = mktime(&timeinfo);
    }
  } else {
    Serial.println("❌ Falha ao obter hora atual!");
    data.timestamp = 0;  // Indica erro
  }
  
  // === SENSOR DHT22 (Temperatura e Umidade) ===
  // Leitura REAL do sensor DHT22
  data.temperature = dht.readTemperature();
  data.humidity = dht.readHumidity();
  
  // Verificar se as leituras são válidas
  if (isnan(data.temperature) || isnan(data.humidity)) {
    Serial.println("⚠️ Erro na leitura do DHT22! Usando valores padrão...");
    data.temperature = 25.0; // Valor padrão
    data.humidity = 60.0;    // Valor padrão
  }
  
  // === SENSOR SW-420 (Vibração) ===
  // Leitura REAL do sensor de vibração
  int rawButtonRead = digitalRead(VIBRATION_PIN);
  // Com INPUT_PULLUP: botão pressionado = LOW (0), não pressionado = HIGH (1)
  // Invertemos para: 1 = vibração detectada, 0 = sem vibração
  data.vibration = !rawButtonRead;
  
  // Debug do botão (remover depois de testar)
  Serial.printf("🔧 DEBUG Botão: Raw=%d, Final=%d\n", rawButtonRead, data.vibration);
  
  // === SENSOR LDR (Luminosidade) ===
  // Leitura REAL do sensor de luminosidade
  data.luminosity = analogRead(LDR_PIN);
  
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
  Serial.println("--- Status dos Sensores ---");
  Serial.printf("📊 Medição #%d | ⏰ %lus\n", measurementCount, data.timestamp);
  Serial.printf("🌡️  Temperatura: %.1f°C\n", data.temperature);
  Serial.printf("💧 Umidade: %.1f%%\n", data.humidity);
  Serial.printf("📳 Vibração: %s\n", data.vibration ? "DETECTADA" : "Normal");
  Serial.printf("💡 Luminosidade: %d (0-4095)\n", data.luminosity);
  Serial.printf("📶 WiFi: %s | 📡 RSSI: %ddBm\n", 
                wifiConnected ? "Conectado" : "Desconectado", 
                wifiConnected ? WiFi.RSSI() : 0);
  Serial.println("---------------------------");
}

void setupNTP() {
  Serial.println("\n⏰ Configurando NTP...");
  configTime(gmtOffset_sec, daylightOffset_sec, ntpServer, ntpServer2);
  
  if (syncNTP()) {
    ntpSynced = true;
    Serial.println("✅ NTP sincronizado com sucesso!");
  } else {
    ntpSynced = false;
    Serial.println("❌ Falha na sincronização NTP");
  }
}

bool syncNTP() {
  struct tm timeinfo;
  int attempts = 0;
  const int maxAttempts = 10;
  
  while (!getLocalTime(&timeinfo) && attempts < maxAttempts) {
    Serial.print(".");
    delay(500);
    attempts++;
  }
  
  if (getLocalTime(&timeinfo)) {
    Serial.printf("\n📅 Data/Hora atual: %d-%02d-%02d %02d:%02d:%02d\n",
                 timeinfo.tm_year + 1900, timeinfo.tm_mon + 1, timeinfo.tm_mday,
                 timeinfo.tm_hour, timeinfo.tm_min, timeinfo.tm_sec);
    return true;
  }
  
  return false;
} 
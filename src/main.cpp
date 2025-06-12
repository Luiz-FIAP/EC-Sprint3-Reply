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
// Lista de servidores para envio simultâneo
const char* serverIPs[] = {
  "192.168.2.126",    // Servidor principal
  "192.168.160.1",    // Servidor Wokwi
  "localhost",        // Servidor local
  "192.168.1.100"     // Servidor adicional
};
const int numServers = sizeof(serverIPs) / sizeof(serverIPs[0]);
const int serverPort = 8000;
const char* serverPath = "/data";

// Controle de servidores
bool serverStatus[4] = {false, false, false, false}; // Status de cada servidor (máximo 4)
int activeServers = 0;
String serverURLs[4]; // URLs completas dos servidores
bool multiServerMode = true; // Modo multi-servidor ativo

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
void discoverActiveServers();
bool testServerConnection(const char* ip);
int sendDataToAllServers(SensorData data);
bool sendDataToSingleServer(SensorData data, const char* serverURL);
String getGatewayIP();
void checkSerialCommands();
SensorData readSensors();
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
  
  // Descobrir servidores ativos após conectar WiFi
  if (wifiConnected) {
    discoverActiveServers();
    
    if (activeServers > 0) {
      Serial.printf("🎯 %d servidor(es) ativo(s) encontrado(s)!\n", activeServers);
      Serial.println("📡 Modo multi-servidor ativado - dados serão enviados para todos os servidores ativos");
    } else {
      Serial.println("❌ Nenhum servidor encontrado!");
      Serial.println("💡 Digite 'add:<IP>' para adicionar servidor manualmente");
      Serial.println("   Exemplo: add:192.168.1.100");
      Serial.println("⚠️ Enquanto isso, dados serão salvos apenas localmente.");
    }
    Serial.println();
    
    // Configurar NTP
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
  Serial.println("💡 Comandos disponíveis via Serial:");
  Serial.println("   • Digite 'help' para ver todos os comandos");
  Serial.println("   • Digite 'status' para ver status do sistema");
  Serial.println("   • Digite 'list' para ver lista de servidores");
  Serial.println("   • Digite 'add:<IP>' para adicionar servidor manualmente");
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
      
      // Tentar enviar para todos os servidores ativos
      int successfulSends = 0;
      if (wifiConnected && WiFi.status() == WL_CONNECTED) {
        if (activeServers > 0) {
          Serial.printf("📡 Enviando dados para %d servidor(es)...\n", activeServers);
          successfulSends = sendDataToAllServers(data);
          
          if (successfulSends > 0) {
            Serial.printf("✅ [#%d] Dados enviados com SUCESSO para %d/%d servidor(es)!\n", 
                         measurementCount, successfulSends, activeServers);
            if (successfulSends == activeServers) {
              Serial.println("🎉 Todos os servidores receberam os dados!");
            } else {
              Serial.printf("⚠️ %d servidor(es) não responderam\n", activeServers - successfulSends);
            }
          } else {
            Serial.printf("❌ [#%d] Falha ao enviar para todos os servidores\n", measurementCount);
            Serial.println("🔄 Tentando redescobrir servidores...");
            discoverActiveServers();
            
            if (activeServers > 0) {
              Serial.printf("🎯 %d servidor(es) redescoberto(s)\n", activeServers);
              successfulSends = sendDataToAllServers(data);
            }
            
            if (successfulSends == 0) {
              Serial.println("💾 Salvando dados localmente...");
            }
          }
        } else {
          Serial.println("🔍 Nenhum servidor ativo, tentando descobrir...");
          discoverActiveServers();
          if (activeServers > 0) {
            Serial.printf("🎯 %d servidor(es) descoberto(s)\n", activeServers);
            successfulSends = sendDataToAllServers(data);
          } else {
            Serial.println("💾 Nenhum servidor encontrado - salvando localmente...");
          }
        }
      } else {
        Serial.printf("📶 [#%d] WiFi desconectado - salvando localmente\n", measurementCount);
      }
      
      // Fallback: salvar em formato CSV se não conseguir enviar para nenhum servidor
      if (successfulSends == 0) {
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
  
  // Verificar comandos via Serial
  checkSerialCommands();
  
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
    Serial.print("📍 IP do ESP32: ");
    Serial.println(WiFi.localIP());
    Serial.print("🌐 Gateway: ");
    Serial.println(WiFi.gatewayIP());
    Serial.println("🔍 Servidor será descoberto automaticamente...");
  } else {
    wifiConnected = false;
    Serial.println();
    Serial.println("❌ Falha na conexão WiFi");
    Serial.println("📝 Modo offline: dados serão salvos em CSV");
  }
  Serial.println();
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

void discoverActiveServers() {
  Serial.println("🔍 Descobrindo servidores ativos...");
  activeServers = 0;
  
  for (int i = 0; i < numServers; i++) {
    Serial.printf("   Testando: %s\n", serverIPs[i]);
    if (testServerConnection(serverIPs[i])) {
      serverStatus[i] = true;
      serverURLs[i] = "http://" + String(serverIPs[i]) + ":" + String(serverPort) + serverPath;
      activeServers++;
      Serial.printf("   ✅ Ativo: %s\n", serverURLs[i].c_str());
    } else {
      serverStatus[i] = false;
      Serial.printf("   ❌ Inativo: %s\n", serverIPs[i]);
    }
    delay(300); // Pequena pausa entre testes
  }
  
  Serial.printf("🎯 Total de servidores ativos: %d/%d\n", activeServers, numServers);
}

int sendDataToAllServers(SensorData data) {
  int successCount = 0;
  
  for (int i = 0; i < numServers; i++) {
    if (serverStatus[i]) {
      Serial.printf("📤 Enviando para servidor %d: %s\n", i+1, serverIPs[i]);
      if (sendDataToSingleServer(data, serverURLs[i].c_str())) {
        successCount++;
        Serial.printf("   ✅ Sucesso no servidor %d\n", i+1);
      } else {
        Serial.printf("   ❌ Falha no servidor %d\n", i+1);
        serverStatus[i] = false; // Marca como inativo se falhar
        activeServers--;
      }
    }
  }
  
  return successCount;
}

bool sendDataToSingleServer(SensorData data, const char* serverURL) {
  HTTPClient http;
  http.begin(serverURL);
  http.addHeader("Content-Type", "application/json");
  http.setTimeout(3000); // Timeout de 3 segundos para não travar
  
  JsonDocument jsonDoc;
  
  // Validar timestamp antes de converter
  if (data.timestamp == 0) {
    data.timestamp = time(nullptr);
  }
  
  // Verificar se timestamp está em segundos (não milissegundos)
  uint64_t timestamp_ms;
  if (data.timestamp > 1000000000000ULL) {
    timestamp_ms = data.timestamp;
  } else {
    timestamp_ms = static_cast<uint64_t>(data.timestamp) * 1000ULL;
  }
  
  jsonDoc["timestamp"] = timestamp_ms;
  jsonDoc["sensor_type"] = "temperature";
  jsonDoc["sensor_value"] = data.temperature;
  
  String jsonString;
  serializeJson(jsonDoc, jsonString);
  
  // Enviar temperatura
  int httpResponseCode = http.POST(jsonString);
  bool success = (httpResponseCode == 200);
  
  http.end();
  
  // Enviar dados adicionais se temperatura foi enviada com sucesso
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

bool testServerConnection(const char* ip) {
  HTTPClient http;
  String testURL = "http://" + String(ip) + ":" + String(serverPort) + "/health";
  
  http.begin(testURL);
  http.setTimeout(2000); // Timeout de 2 segundos
  
  int httpResponseCode = http.GET();
  http.end();
  
  // Considera sucesso se receber qualquer resposta HTTP (mesmo 404)
  // Isso indica que há um servidor rodando nesse IP
  return (httpResponseCode > 0);
}

String getGatewayIP() {
  // Obtém o IP do gateway da rede atual
  IPAddress gateway = WiFi.gatewayIP();
  if (gateway == IPAddress(0, 0, 0, 0)) {
    return "";
  }
  return gateway.toString();
}

void checkSerialCommands() {
  if (Serial.available()) {
    String command = Serial.readStringUntil('\n');
    command.trim();
    
    if (command.startsWith("add:")) {
      // Comando para adicionar servidor manualmente
      // Formato: add:192.168.1.100
      String newIP = command.substring(4);
      newIP.trim();
      
      Serial.printf("🔧 Testando novo servidor: %s\n", newIP.c_str());
      
      if (testServerConnection(newIP.c_str())) {
        // Encontrar slot vazio para adicionar o servidor
        bool added = false;
        for (int i = 0; i < numServers; i++) {
          if (!serverStatus[i]) {
            serverStatus[i] = true;
            serverURLs[i] = "http://" + newIP + ":" + String(serverPort) + serverPath;
            activeServers++;
            added = true;
            Serial.printf("✅ Servidor adicionado: %s\n", serverURLs[i].c_str());
            break;
          }
        }
        if (!added) {
          Serial.println("⚠️ Lista de servidores cheia. Use 'clear' primeiro.");
        }
      } else {
        Serial.printf("❌ Servidor não responde em: %s\n", newIP.c_str());
      }
    }
    else if (command == "scan") {
      // Comando para forçar nova descoberta
      Serial.println("🔍 Forçando nova descoberta de servidores...");
      discoverActiveServers();
      if (activeServers > 0) {
        Serial.printf("✅ %d servidor(es) redescoberto(s)\n", activeServers);
      } else {
        Serial.println("❌ Nenhum servidor encontrado");
      }
    }
    else if (command == "clear") {
      // Comando para limpar lista de servidores
      Serial.println("🧹 Limpando lista de servidores...");
      for (int i = 0; i < numServers; i++) {
        serverStatus[i] = false;
      }
      activeServers = 0;
      Serial.println("✅ Lista de servidores limpa");
    }
    else if (command == "list") {
      // Comando para listar servidores
      Serial.println("\n=== LISTA DE SERVIDORES ===");
      for (int i = 0; i < numServers; i++) {
        String status = serverStatus[i] ? "✅ ATIVO" : "❌ INATIVO";
        Serial.printf("%d. %s - %s\n", i+1, serverIPs[i], status.c_str());
      }
      Serial.printf("Total ativos: %d/%d\n", activeServers, numServers);
      Serial.println("===========================\n");
    }
    else if (command == "status") {
      // Comando para mostrar status atual
      Serial.println("\n=== STATUS DO SISTEMA ===");
      Serial.printf("WiFi: %s\n", wifiConnected ? "Conectado" : "Desconectado");
      Serial.printf("IP ESP32: %s\n", WiFi.localIP().toString().c_str());
      Serial.printf("Gateway: %s\n", WiFi.gatewayIP().toString().c_str());
      Serial.printf("Servidores Ativos: %d/%d\n", activeServers, numServers);
      Serial.printf("Modo Multi-Servidor: %s\n", multiServerMode ? "Ativo" : "Inativo");
      Serial.printf("NTP: %s\n", ntpSynced ? "Sincronizado" : "Não sincronizado");
      Serial.printf("Medições: %d\n", measurementCount);
      Serial.println("========================\n");
    }
    else if (command == "help") {
      // Comando de ajuda
      Serial.println("\n=== COMANDOS DISPONÍVEIS ===");
      Serial.println("add:<IP>     - Adiciona servidor manualmente");
      Serial.println("             Exemplo: add:192.168.1.100");
      Serial.println("scan         - Força nova descoberta de servidores");
      Serial.println("list         - Lista todos os servidores e status");
      Serial.println("clear        - Limpa lista de servidores");
      Serial.println("status       - Mostra status do sistema");
      Serial.println("help         - Mostra esta ajuda");
      Serial.println("============================\n");
    }
  }
} 
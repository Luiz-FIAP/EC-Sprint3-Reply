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

// Controle de servidor confiável
bool reliableServerFound = false;        // Flag para servidor confiável encontrado
int reliableServerIndex = -1;            // Índice do servidor confiável
int consecutiveFailures = 0;             // Contador de falhas consecutivas
const int MAX_CONSECUTIVE_FAILURES = 3;  // Máximo de falhas antes de rediscovery
bool forceDiscovery = false;             // Flag para forçar descoberta (comando manual)

// *** Configurações WiFi ***
const char* ssid = "Wokwi-GUEST";      // Para simulação Wokwi
const char* password = "";              // Sem senha no Wokwi
// Para uso real, substitua por suas credenciais:
// const char* ssid = "SUA_REDE_WIFI";
// const char* password = "SUA_SENHA_WIFI";

// *** Configurações do Servidor ***
// Lista de servidores para envio simultâneo
const char* serverIPs[] = {
  "192.168.2.126",    // Servidor principal (ajuste conforme sua rede)
  "192.168.1.100",    // Servidor adicional
  "192.168.100.161",  // Servidor adicional
  "192.168.18.7",      // Servidor adicional
  "localhost",        // Servidor local
  "192.168.160.1",    // Servidor Wokwi
  "127.0.0.1"        // Loopback
// Adicione mais servidores conforme necessário
};
const int numServers = sizeof(serverIPs) / sizeof(serverIPs[0]);
const int serverPort = 8000;
const char* serverPath = "/data";

// Controle de servidores
bool serverStatus[numServers] = {false}; // Status de cada servidor
int activeServers = 0;
String serverURLs[numServers]; // URLs completas dos servidores
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

// *** Configurações do Dispositivo ***
const char* DEVICE_ID = "ESP32_001";  // Deve corresponder ao initial_data.sql
const char* DEVICE_NAME = "Sensor Sala Servidores";

// IDs dos sensores (devem corresponder aos do initial_data.sql)
const char* SENSOR_IDS[] = {
  "ESP32_001_TEMP",  // Temperatura
  "ESP32_001_HUM",   // Umidade  
  "ESP32_001_VIB",   // Vibração
  "ESP32_001_LUM"    // Luminosidade
};

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
      
      // Tentar enviar para servidores
      int successfulSends = 0;
      if (wifiConnected && WiFi.status() == WL_CONNECTED) {
        if (activeServers > 0) {
          if (reliableServerFound) {
            Serial.printf("🎯 Usando modo servidor confiável (%d servidor ativo)\n", activeServers);
          } else {
            Serial.printf("📡 Enviando dados para %d servidor(es)...\n", activeServers);
          }
          successfulSends = sendDataToAllServers(data);
          
          if (successfulSends > 0) {
            Serial.printf("✅ [#%d] Dados enviados com SUCESSO!\n", measurementCount);
          } else {
            Serial.printf("❌ [#%d] Falha ao enviar dados\n", measurementCount);
            Serial.println("💾 Salvando dados localmente...");
          }
        } else {
          // Só faz rediscovery se não tem servidor confiável ou se foi forçado
          if (!reliableServerFound || forceDiscovery) {
            Serial.println("🔍 Nenhum servidor ativo, tentando descobrir...");
            discoverActiveServers();
            if (activeServers > 0) {
              successfulSends = sendDataToAllServers(data);
            } else {
              Serial.println("💾 Nenhum servidor encontrado - salvando localmente...");
            }
          } else {
            Serial.println("🎯 Servidor confiável definido, pulando rediscovery automática");
            Serial.println("💾 Salvando dados localmente...");
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
  
  // Reset do contador de falhas quando faz descoberta
  consecutiveFailures = 0;
  
  for (int i = 0; i < numServers; i++) {
    Serial.printf("   Testando: %s\n", serverIPs[i]);
    if (testServerConnection(serverIPs[i])) {
      serverStatus[i] = true;
      serverURLs[i] = "http://" + String(serverIPs[i]) + ":" + String(serverPort) + serverPath;
      activeServers++;
      Serial.printf("   ✅ Ativo: %s\n", serverURLs[i].c_str());
      
      // Se ainda não encontrou servidor confiável, marca este como confiável
      if (!reliableServerFound && !forceDiscovery) {
        reliableServerFound = true;
        reliableServerIndex = i;
        Serial.printf("   🎯 Servidor confiável definido: %s\n", serverIPs[i]);
      }
    } else {
      serverStatus[i] = false;
      Serial.printf("   ❌ Inativo: %s\n", serverIPs[i]);
    }
    delay(300); // Pequena pausa entre testes
  }
  
  Serial.printf("🎯 Total de servidores ativos: %d/%d\n", activeServers, numServers);
  
  // Se encontrou servidor confiável, mostra mensagem
  if (reliableServerFound && !forceDiscovery) {
    Serial.printf("🔒 Modo servidor confiável ativado - usando: %s\n", serverIPs[reliableServerIndex]);
  }
  
  // Reset da flag de força após descoberta
  forceDiscovery = false;
}

int sendDataToAllServers(SensorData data) {
  int successCount = 0;
  
  // Se tem servidor confiável, tenta apenas ele primeiro
  if (reliableServerFound && reliableServerIndex >= 0 && serverStatus[reliableServerIndex]) {
    Serial.printf("🎯 Usando servidor confiável: %s\n", serverIPs[reliableServerIndex]);
    if (sendDataToSingleServer(data, serverURLs[reliableServerIndex].c_str())) {
      successCount++;
      consecutiveFailures = 0; // Reset contador de falhas
      Serial.printf("   ✅ Sucesso no servidor confiável\n");
      return successCount; // Retorna imediatamente se conseguiu enviar
    } else {
      consecutiveFailures++;
      Serial.printf("   ❌ Falha no servidor confiável (%d/%d)\n", consecutiveFailures, MAX_CONSECUTIVE_FAILURES);
      
      // Se atingiu limite de falhas, marca como inativo e força rediscovery
      if (consecutiveFailures >= MAX_CONSECUTIVE_FAILURES) {
        Serial.println("   🔄 Muitas falhas consecutivas - servidor confiável removido");
        serverStatus[reliableServerIndex] = false;
        reliableServerFound = false;
        reliableServerIndex = -1;
        consecutiveFailures = 0;
        
        // Tenta outros servidores ativos se houver
        Serial.println("   🔄 Tentando outros servidores ativos...");
      }
    }
  }
  
  // Tenta todos os servidores ativos (incluindo o confiável se ainda estiver ativo)
  for (int i = 0; i < numServers; i++) {
    if (serverStatus[i]) {
      Serial.printf("📤 Enviando para servidor %d: %s\n", i+1, serverIPs[i]);
      if (sendDataToSingleServer(data, serverURLs[i].c_str())) {
        successCount++;
        Serial.printf("   ✅ Sucesso no servidor %d\n", i+1);
        
        // Se conseguiu enviar e não tinha servidor confiável, marca este como confiável
        if (!reliableServerFound && successCount == 1) {
          reliableServerFound = true;
          reliableServerIndex = i;
          Serial.printf("   🎯 Novo servidor confiável definido: %s\n", serverIPs[i]);
        }
      } else {
        Serial.printf("   ❌ Falha no servidor %d\n", i+1);
        serverStatus[i] = false; // Marca como inativo se falhar
        activeServers--;
        
        // Se era o servidor confiável que falhou, incrementa contador
        if (reliableServerFound && i == reliableServerIndex) {
          consecutiveFailures++;
        }
      }
    }
  }
  
  return successCount;
}

bool sendDataToSingleServer(SensorData data, const char* serverURL) {
  HTTPClient http;
  bool overallSuccess = false;
  
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
  
  // Estrutura para organizar dados de cada sensor
  struct SensorInfo {
    const char* sensorId;
    const char* sensorType;
    float value;
  };
  
  // Criar array com informações de cada sensor
  SensorInfo sensorData[] = {
    {SENSOR_IDS[0], "temperature", data.temperature},
    {SENSOR_IDS[1], "humidity", data.humidity}, 
    {SENSOR_IDS[2], "vibration", data.vibration},
    {SENSOR_IDS[3], "luminosity", data.luminosity}
  };
  
  // Enviar cada sensor separadamente
  for (int i = 0; i < 4; i++) {
    // Criar novo documento JSON para cada sensor
    JsonDocument jsonDoc;
    
    // Preencher dados do sensor
    jsonDoc["sensor_id"] = sensorData[i].sensorId;
    jsonDoc["device_id"] = DEVICE_ID;
    jsonDoc["timestamp"] = timestamp_ms;
    jsonDoc["sensor_type"] = sensorData[i].sensorType;
    jsonDoc["sensor_value"] = sensorData[i].value;
    jsonDoc["quality"] = "good";
    
    // Serializar JSON
    String jsonString;
    serializeJson(jsonDoc, jsonString);
    
    // Debug: mostrar JSON sendo enviado
    Serial.printf("📤 Enviando %s: %s\n", sensorData[i].sensorType, jsonString.c_str());
    
    // Iniciar conexão HTTP
    http.begin(serverURL);
    http.addHeader("Content-Type", "application/json");
    http.setTimeout(3000); // Timeout de 3 segundos
    
    // Enviar dados
    int httpResponseCode = http.POST(jsonString);
    
    // Verificar resposta
    if (httpResponseCode == 200) {
      Serial.printf("   ✅ %s enviado com sucesso\n", sensorData[i].sensorType);
      overallSuccess = true; // Pelo menos um sensor conseguiu enviar
    } else {
      Serial.printf("   ❌ Falha %s (HTTP %d)\n", sensorData[i].sensorType, httpResponseCode);
    }
    
    // Fechar conexão
    http.end();
    
    // Pequena pausa entre envios
    delay(100);
  }
  
  return overallSuccess;
}

bool testServerConnection(const char* ip) {
  HTTPClient http;
  String testURL = "http://" + String(ip) + ":" + String(serverPort) + "/health";
  
  http.begin(testURL);
  http.setTimeout(2000); // Timeout de 2 segundos
  
  int httpResponseCode = http.GET();
  http.end();
  
  return (httpResponseCode == 200); // Sucesso se retornar 200
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
      forceDiscovery = true;  // Força rediscovery
      discoverActiveServers();
      if (activeServers > 0) {
        Serial.printf("✅ %d servidor(es) encontrado(s)\n", activeServers);
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
    else if (command == "reliable") {
      // Comando para mostrar/verificar servidor confiável
      if (reliableServerFound && reliableServerIndex >= 0) {
        Serial.printf("🎯 Servidor confiável: %s\n", serverIPs[reliableServerIndex]);
        Serial.printf("   Status: %s\n", serverStatus[reliableServerIndex] ? "Ativo" : "Inativo");
        Serial.printf("   Falhas consecutivas: %d/%d\n", consecutiveFailures, MAX_CONSECUTIVE_FAILURES);
      } else {
        Serial.println("❌ Nenhum servidor confiável definido");
      }
    }
    else if (command == "reset") {
      // Comando para resetar servidor confiável
      Serial.println("🔄 Resetando servidor confiável...");
      reliableServerFound = false;
      reliableServerIndex = -1;
      consecutiveFailures = 0;
      Serial.println("✅ Servidor confiável removido");
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
      Serial.println("reliable     - Mostra servidor confiável atual");
      Serial.println("reset        - Remove servidor confiável");
      Serial.println("help         - Mostra esta ajuda");
      Serial.println("============================\n");
    }
  }
} 
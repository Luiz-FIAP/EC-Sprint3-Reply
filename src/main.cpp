/*
 * Sistema de Monitoramento IoT com ESP32
 * 
 * Sensores utilizados:
 * - DHT22: Temperatura e umidade (pino D4)
 * - SW-420: Sensor de vibração (pino D2)
 * - LDR: Sensor de luminosidade (pino A0)
 * 
 * Funcionalidades:
 * - Leitura de sensores a cada 2 segundos
 * - Simulação de valores realistas
 * - Saída formatada para CSV
 * - Monitor Serial para debug
 */

#include <Arduino.h>
#include <DHT.h>
#include <math.h>

// Definições de pinos
#define DHT_PIN 4
#define VIBRATION_PIN 2
#define LDR_PIN 34  // GPIO36 para ADC no ESP32

// Configuração do sensor DHT22
#define DHT_TYPE DHT22
DHT dht(DHT_PIN, DHT_TYPE);

// Variáveis para simulação realística
unsigned long lastReadTime = 0;
const unsigned long READ_INTERVAL = 2000; // 2 segundos

// Variáveis para geração de dados realísticos
float baseTemperature = 25.0;
int baseLuminosity = 2000;
unsigned long startTime;
int measurementCount = 0;

// Header CSV já impresso
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
SensorData readSensors();
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
  Serial.println("ESP32 com 3 sensores virtuais");
  Serial.println("Iniciando coleta de dados...\n");
  
  delay(2000); // Aguarda estabilização dos sensores
}

void loop() {
  unsigned long currentTime = millis();
  
  if (currentTime - lastReadTime >= READ_INTERVAL) {
    lastReadTime = currentTime;
    measurementCount++;
    
    // Imprime header CSV apenas uma vez
    if (!csvHeaderPrinted) {
      Serial.println("\n=== DADOS CSV ===");
      Serial.println("timestamp,temperatura_c,umidade_pct,vibração_digital,luminosidade_analogica");
      csvHeaderPrinted = true;
    }
    
    // Leitura e simulação dos sensores
    SensorData data = readSensors();
    
    // Saída formatada para CSV
    printCSVData(data);
    
    // Saída formatada para debug (opcional)
    if (measurementCount % 10 == 0) { // A cada 10 medições
      printDebugData(data);
    }
    
    // Para simulação, limita a 50 medições
    if (measurementCount >= 50) {
      Serial.println("\n=== Simulação finalizada ===");
      Serial.println("50 medições coletadas com sucesso!");
      Serial.println("Dados prontos para análise.");
      while(true) { delay(1000); } // Para a execução
    }
  }
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
  Serial.println("\n--- Debug Info ---");
  Serial.print("Medição #"); Serial.println(measurementCount);
  Serial.print("Tempo: "); Serial.print(data.timestamp / 1000.0); Serial.println("s");
  Serial.print("Temperatura: "); Serial.print(data.temperature); Serial.println("°C");
  Serial.print("Umidade: "); Serial.print(data.humidity); Serial.println("%");
  Serial.print("Vibração: "); Serial.println(data.vibration ? "DETECTADA" : "Normal");
  Serial.print("Luminosidade: "); Serial.print(data.luminosity); Serial.println(" (0-4095)");
  Serial.println("------------------\n");
} 
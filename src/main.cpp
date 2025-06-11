// --- Bibliotecas ---
#include <Arduino.h>
#include "DHT.h" // Biblioteca para o sensor DHT

// --- Definição de Pinos ---
#define DHT_PIN 4         // Pino de dados do sensor DHT22
#define VIBRATION_PIN 2   // Pino do botão para simular vibração
#define LDR_PIN 34        // Pino do sensor de luminosidade LDR

// --- Configurações dos Sensores ---
#define DHT_TYPE DHT22    // Define o tipo de sensor DHT como DHT22
DHT dht(DHT_PIN, DHT_TYPE);

// --- Função de Inicialização ---
void setup() {
  // Inicia a comunicação serial
  Serial.begin(115200);
  Serial.println("Iniciando sistema de monitoramento...");

  // Configura o pino do botão/vibração como entrada com pull-up interno
  // O pino do LDR (analógico) não precisa de pinMode
  pinMode(VIBRATION_PIN, INPUT_PULLUP);

  // Inicia o sensor DHT
  dht.begin();
}

// --- Loop Principal ---
void loop() {
  // --- Leitura dos Sensores ---

  // Lê a umidade do sensor DHT22
  float humidity = dht.readHumidity();
  // Lê a temperatura em Celsius do sensor DHT22
  float temperature = dht.readTemperature();

  // Lê o valor analógico do LDR (0-4095)
  int ldrValue = analogRead(LDR_PIN);

  // Lê o estado do sensor de vibração (botão)
  // INPUT_PULLUP: LOW significa que o botão foi pressionado (vibração detectada)
  int vibrationStatus = digitalRead(VIBRATION_PIN);

  // --- Exibição dos Dados no Monitor Serial ---

  // Verifica se a leitura do DHT falhou e exibe uma mensagem de erro
  if (isnan(humidity) || isnan(temperature)) {
    Serial.println("Falha ao ler do sensor DHT!");
  } else {
    Serial.print("Umidade: ");
    Serial.print(humidity);
    Serial.print("%\t"); // Tabulação para formatar a saída
    Serial.print("Temperatura: ");
    Serial.print(temperature);
    Serial.println(" *C");
  }

  // Exibe o valor do LDR
  Serial.print("Luminosidade (LDR): ");
  Serial.println(ldrValue);

  // Exibe o status da vibração
  Serial.print("Status de Vibracao: ");
  if (vibrationStatus == LOW) {
    Serial.println("Vibracao Detectada!");
  } else {
    Serial.println("Normal");
  }

  Serial.println("---------------------------------------");

  // Aguarda 2 segundos antes da próxima leitura
  delay(2000);
}
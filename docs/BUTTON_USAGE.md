# 🔘 Sistema de Botão de Envio Manual

## Visão Geral

O sistema foi modificado para incluir um **botão de envio manual** que permite controlar quando os dados dos sensores são enviados para o servidor. Isso oferece maior controle sobre o consumo de dados e permite testes mais precisos.

## 🔧 Configuração Física

### Conexões do Botão
- **Pino do ESP32**: D5 (GPIO 5)
- **Tipo**: Push button (normalmente aberto)
- **Pull-up**: Interno do ESP32 ativado
- **GND**: Conectado ao GND do ESP32

### Componentes Necessários
```
📋 Lista de Materiais:
✅ ESP32 DevKit v1
✅ DHT22 (Temperatura/Umidade) - Pino D4
✅ SW-420 (Vibração) - Pino D2  
✅ LDR (Luminosidade) - Pino D34
✅ Push Button - Pino D5
✅ Resistor 10kΩ (opcional, pull-up interno usado)
✅ Jumpers
```

## 🚀 Como Funciona

### 1. **Monitoramento Contínuo**
- Sistema lê sensores a cada **2 segundos**
- Dados ficam armazenados na variável `currentData`
- Monitor serial exibe status a cada **5 segundos**

### 2. **Envio Manual**
- **Pressione o botão** para enviar dados atuais
- Sistema detecta pressionamento com debounce (50ms)
- Dados são enviados imediatamente para o servidor

### 3. **Feedback Visual**
```
📊 === DADOS ATUAIS DOS SENSORES ===
🌡️  Temperatura: 24.3°C
💧 Umidade: 67.2%
📳 Vibração: Normal ✅
💡 Luminosidade: 2847/4095
📶 WiFi: Conectado ✅ | RSSI: -45dBm
📤 Dados enviados: 3 | 🔘 Pressione botão para enviar!
=====================================
```

## 📡 Fluxo de Dados

### Quando o Botão é Pressionado:

1. **🔘 BOTÃO DETECTADO!**
   ```
   🔘 BOTÃO PRESSIONADO! Enviando dados...
   =======================================
   ```

2. **📋 Dados Exibidos**
   - Mostra todos os valores dos sensores
   - Timestamp atual
   - Status da conexão

3. **📡 Tentativa de Envio**
   - Se WiFi OK → Envia para servidor Flask
   - Se WiFi OFF → Salva em formato CSV

4. **✅ Confirmação**
   ```
   ✅ Dados enviados com SUCESSO! (#4)
   🎉 Servidor recebeu os dados!
   ```

## 🔧 Configuração no Código

### Definições Importantes
```cpp
#define BUTTON_PIN 5              // Pino do botão
#define DEBOUNCE_DELAY 50         // Anti-bounce 50ms
#define READ_INTERVAL 2000        // Lê sensores a cada 2s
#define DISPLAY_INTERVAL 5000     // Exibe dados a cada 5s
```

### Função de Detecção
```cpp
bool isButtonPressed() {
  // Implementa debounce para evitar múltiplas leituras
  // Retorna true apenas quando botão é realmente pressionado
}
```

## 📊 Vantagens do Sistema Manual

### ✅ **Controle Total**
- Você decide quando enviar dados
- Ideal para testes e demonstrações
- Economia de bateria em sistemas portáteis

### ✅ **Debugging Facilitado**
- Vê exatamente quais dados serão enviados
- Feedback imediato de sucesso/erro
- Logs detalhados no monitor serial

### ✅ **Flexibilidade**
- Monitoramento contínuo + envio sob demanda
- Backup automático se WiFi falhar
- Contador de envios bem-sucedidos

## 🔧 Simulação no Wokwi

### Configuração Virtual
O arquivo `wokwi.toml` inclui:
```toml
[[parts]]
type = "wokwi-pushbutton"
id = "button"
attrs = { color = "red", bounce = "true" }

# Conexões
[ "button:1.l", "esp:D5", "" ]
[ "button:2.l", "esp:GND", "" ]
```

### Como Testar
1. Carregue o projeto no Wokwi
2. Inicie a simulação
3. Observe os dados no monitor serial
4. **Clique no botão vermelho** para enviar dados
5. Verifique os logs de confirmação

## 🚨 Troubleshooting

### Botão Não Responde
- ✅ Verifique conexão no pino D5
- ✅ Confirme GND conectado
- ✅ Observe logs de debounce no serial

### Múltiplos Envios
- ✅ Delay de 1s implementado após envio
- ✅ Debounce de 50ms previne bouncing
- ✅ Solte e pressione novamente o botão

### WiFi Desconectado
- ✅ Sistema salva automaticamente em CSV
- ✅ Reconexão automática tentada
- ✅ Dados não são perdidos

## 📈 Próximos Passos

### Melhorias Possíveis
- 🔄 **Botão de Reset**: Limpar contadores
- 📊 **LED de Status**: Indicação visual de envio
- ⏰ **Modo Automático**: Alternância manual/automático
- 💾 **Múltiplos Backups**: Diferentes formatos de saída

---

**💡 Dica**: Use este sistema para demonstrações interativas ou quando precisar de controle preciso sobre quando os dados IoT são transmitidos! 
# Sistema de Monitoramento IoT com ESP32

## Descrição
Este projeto simula um circuito funcional com ESP32 e 3 sensores virtuais (temperatura, vibração e luminosidade) para coleta e análise de dados em tempo real.

## Sensores Utilizados
- **DHT22**: Sensor de temperatura e umidade
- **SW-420**: Sensor de vibração
- **LDR**: Sensor de luminosidade (fotorresistor)

## Estrutura do Projeto
```
├── README.md              # Este arquivo
├── diagram.json           # Configuração do circuito Wokwi
├── wokwi.toml            # Configuração do projeto Wokwi
├── src/
│   └── main.cpp          # Código principal Arduino
├── data/
│   └── sensor_data.csv   # Dados coletados dos sensores
├── analysis/
│   └── data_visualization.py  # Script para gerar gráficos
└── docs/
    └── images/           # Prints do circuito e gráficos
```

## Como Executar

### 1. Simulação no Wokwi
1. Acesse [Wokwi.com](https://wokwi.com)
2. Crie um novo projeto ESP32
3. Copie o conteúdo de `diagram.json` para o diagrama
4. Copie o código de `src/main.cpp` para o editor
5. Execute a simulação

### 2. Análise dos Dados
```bash
# Instalar dependências Python
pip3 install -r requirements.txt

# Executar visualização
cd analysis
python3 data_visualization.py
```

### 3. Resultados Obtidos
O sistema gera automaticamente:
- 📊 **Gráfico de análise**: `docs/images/sensor_analysis.png`
- 📈 **Estatísticas detalhadas** no terminal
- 📄 **Dados CSV** prontos para análise

## Funcionalidades Implementadas
- ✅ **Simulação ESP32**: Circuito virtual com 3 sensores no Wokwi
- ✅ **Sensores Configurados**: DHT22, SW-420, LDR com valores realistas
- ✅ **Código Arduino**: Leitura a cada 2 segundos com simulação de padrões
- ✅ **Saída CSV**: Formato padronizado para análise
- ✅ **Visualização**: Gráficos automáticos com estatísticas
- ✅ **Documentação**: Instruções completas de reprodução

## Cenários Simulados
- **Temperatura**: 15°C a 35°C (ambiente interno)
- **Vibração**: 0-1023 (digital com ruído simulado)
- **Luminosidade**: 0-4095 (variação dia/noite)

## Tecnologias
- **Hardware**: ESP32-DevKitC V4
- **Plataforma**: Wokwi Simulator
- **Linguagem**: C++ (Arduino Framework)
- **Visualização**: Python + Matplotlib
- **Dados**: CSV Export

## Solução de Problemas
Se encontrar erros de compilação ou execução, consulte o [Guia de Troubleshooting](docs/TROUBLESHOOTING.md).

## Arquivos Importantes
- 🔧 `platformio.ini`: Configuração do PlatformIO
- 📋 `docs/TROUBLESHOOTING.md`: Guia de solução de problemas
- 🖼️ `docs/images/sensor_analysis.png`: Gráfico gerado

---
*Projeto desenvolvido para demonstrar conceitos de IoT e análise de dados.* 
# FIAP - Faculdade de Informática e Administração Paulista 

<p align="center">
<a href= "https://www.fiap.com.br/"><img src="imagens/logo-fiap.png" alt="FIAP - Faculdade de Informática e Admnistração Paulista" border="0" width=40% height=40%></a>
</p>

<br>

# Sistema de Monitoramento IoT com ESP32

---

## 🚀 **Contexto do Desafio Hermes Reply**

> **Este projeto faz parte do desafio proposto pela Hermes Reply para a Fase 4 do curso FIAP, cujo objetivo é simular um sistema de monitoramento industrial utilizando ESP32 e sensores virtuais. A iniciativa visa aproximar os alunos das práticas de Indústria 4.0, promovendo a coleta, análise e visualização de dados em ambientes simulados, preparando para desafios reais de automação e inteligência artificial.**

A Hermes Reply atua com soluções digitais aplicadas à indústria, com foco em monitoramento inteligente de equipamentos. A coleta de dados em ambientes industriais modernos é realizada através de sensores conectados a sistemas embarcados, como o ESP32, monitorando variáveis como temperatura, vibração e luminosidade. O projeto simula esse cenário, utilizando plataformas online de simulação de circuitos e sensores (Wokwi, VSCode, PlatformIO), para criar um circuito virtual, coletar dados e realizar análises iniciais.

---

## Grupo 36

## 👨‍🎓 Integrantes: 
- <a href="https://github.com/FelipeSabinoTMRS">Felipe Sabino da Silva</a>
- <a href="https://github.com/juanvoltolini-rm562890">Juan Felipe Voltolini</a>
- <a href="https://github.com/Luiz-FIAP">Luiz Henrique Ribeiro de Oliveira</a> 
- <a href="https://github.com/marcofiap">Marco Aurélio Eberhardt Assimpção</a>
- <a href="https://github.com/PauloSenise">Paulo Henrique Senise</a> 


## 👩‍🏫 Professores:
### Tutor(a) 
- <a href="https://github.com/Leoruiz197">Leonardo Ruiz Orabona</a>
### Coordenador(a)
- <a href="https://github.com/agodoi">André Godoi</a>



**Enterprise Challenge - Sprint 2 - Reply**



## Descrição
Este projeto simula um circuito funcional com ESP32 e 3 sensores virtuais (temperatura, vibração e luminosidade) para coleta e análise de dados em tempo real.

<p align="center">
<a><img src="imagens/esquema.png" alt="Esquema da ESP32 com sensores" border="0" width=70% height=70%></a>
</p>

## Sensores Utilizados
- **DHT22**: Sensor de temperatura e umidade
- **SW-420**: Sensor de vibração (simulado com botão)
- **LDR**: Sensor de luminosidade (fotorresistor)

### 🎯 **Justificativa dos Sensores Utilizados**

- **DHT22 (Temperatura e Umidade):** Essencial para monitorar condições ambientais que podem afetar o funcionamento de máquinas e a qualidade do produto.
- **SW-420 (Vibração):** Importante para detectar anomalias mecânicas e prevenir falhas em equipamentos rotativos.
- **LDR (Luminosidade):** Útil para monitorar iluminação em ambientes industriais, garantindo condições ideais de trabalho e segurança.

### 🎮 **Interação com Sensores Virtuais**

**Como testar no Wokwi:**
- **DHT22**: Clique no sensor e ajuste temperatura/umidade manualmente
- **SW-420**: Use o botão/switch para simular vibração (0/1)
- **LDR**: Ajuste o slider de luminosidade (0-4095)

## Estrutura do Projeto
```
├── README.md                          # Este arquivo
├── plan.md                           # Plano de desenvolvimento do projeto
├── diagram.json                       # Configuração do circuito Wokwi
├── wokwi.toml                        # Configuração do projeto Wokwi
├── platformio.ini                    # Configuração PlatformIO
├── requirements.txt                   # Dependências Python do projeto
├── .gitignore                        # Arquivos ignorados pelo Git
├── src/
│   └── main.cpp                      # Código principal Arduino/ESP32
├── sensor.ingest.local/
│   ├── servidor.py                   # Servidor Flask para ingestão de dados
│   ├── config.py                     # Configurações centralizadas
│   ├── initial_data.sql              # Script SQL para inicialização do banco
│   └── server_logs.txt               # Logs do servidor de ingestão
├── scripts/
│   ├── setup-oracle-docker.sh       # Script para configurar Oracle (Linux/macOS)
│   ├── setup-oracle-docker.bat      # Script para configurar Oracle (Windows Batch)  
│   └── setup-oracle-docker.ps1      # Script para configurar Oracle (Windows PowerShell)
├── data/
│   ├── dashboard.py                  # Script para geração de dashboard
│   ├── dashboard_*.png               # Capturas de tela dos dashboards (1-10)
│   └── README.md                     # Documentação específica dos dados
├── imagens/
│   ├── esquema.png                   # Esquema do circuito ESP32
│   ├── logo-fiap.png                 # Logo da FIAP
│   ├── play.png                      # Imagem do botão play
│   └── servidor.png                  # Screenshot do servidor em execução
├── .vscode/                          # Configurações do VS Code
│   ├── settings.json                 # Configurações do editor
│   └── extensions.json               # Extensões recomendadas
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
```

### 3. Banco de Dados Oracle (Opcional)
Para usar o sistema completo com persistência de dados:

#### **🐳 Subir Oracle Free no Docker**

**Pré-requisitos:**
- Docker instalado ([Docker Desktop](https://www.docker.com/products/docker-desktop/))
- 8GB+ de RAM disponível

**Passo a passo:**

#### **🤖 Opção Automática (Recomendada)**

**🐧 Linux/macOS:**
```bash
# Execute o script automatizado
./scripts/setup-oracle-docker.sh
```

**🪟 Windows:**
```cmd
REM Opção 1: Script Batch (Command Prompt)
scripts\setup-oracle-docker.bat
```
```powershell
# Opção 2: PowerShell (Recomendado)
.\scripts\setup-oracle-docker.ps1

# Com opções avançadas:
.\scripts\setup-oracle-docker.ps1 -Force              # Remove container existente sem perguntar
.\scripts\setup-oracle-docker.ps1 -SkipMemoryCheck    # Pula verificação de memória
```

#### **📋 Opção Manual**
```bash
# 1. Baixar e executar Oracle Database 23c Free
docker run -d \
  --name oracle-free \
  -p 1521:1521 \
  -p 5500:5500 \
  -e ORACLE_PWD=123456 \
  -e ORACLE_CHARACTERSET=AL32UTF8 \
  -v oracle-data:/opt/oracle/oradata \
  container-registry.oracle.com/database/free:latest

# 2. Aguardar inicialização (pode levar 5-10 minutos)
echo "⏳ Aguardando Oracle inicializar..."
docker logs -f oracle-free

# 3. Verificar se está rodando
docker ps | grep oracle-free
```

**Aguarde ver esta mensagem:**
```
DATABASE IS READY TO USE!
```

#### **🔧 Conectar ao Banco**

```bash
# Conectar via SQL*Plus (opcional, para testes)
docker exec -it oracle-free sqlplus sys/123456@FREEPDB1 as sysdba

# Ou conectar como usuário FIAP
docker exec -it oracle-free sqlplus fiap/123456@FREEPDB1
```

#### **📋 Configurações para o Servidor Python**

Edite as configurações conforme seu banco de dados Oracle no `sensor.ingest.local/config.py`:

```python
# Configurações do Banco Oracle
DB_CONFIG = {
  "user": "fiap",
  "password": "123456", 
  "dsn": "localhost:1521/FREEPDB1", # Configurado para porta mapeada do Docker
  "table_name": "sensor_readings"
}  
```

#### **🛑 Comandos Úteis do Docker**

```bash
# Parar o banco
docker stop oracle-free

# Iniciar novamente 
docker start oracle-free

# Ver logs
docker logs oracle-free

# Remover completamente (CUIDADO: perde dados!)
docker rm -f oracle-free
docker volume rm oracle-data
```

### 4. Servidor de Ingestão (Opcional)
Para receber dados em tempo real do ESP32 e armazenar no Oracle:

```bash
# Pré-requisitos
pip3 install flask oracledb

# As configurações estão centralizadas em config.py
# Para conexão com banco de dados Oracle, edite o arquivo sensor.ingest.local/config.py

# Iniciar servidor
cd sensor.ingest.local
python3 servidor.py (mac)
python servidor.py (windows)
```
Terminal do ``servidor.py``:

<p align="center">
<a><img src="imagens/servidor.png" alt="Terminal servidor.py" border="0" width=100%></a>
</p>

Após rodar `servidor.py`, copie o endereço do servidor Flask para esta parte do código na linha 31 do `main.cpp`:

```c
// *** Configurações do Servidor ***
// Lista de servidores para envio simultâneo
const char* serverIPs[] = {
  "192.168.2.126",    // Servidor principal
  "192.168.160.1",    // Servidor Wokwi
  "localhost",        // Servidor local
  "192.168.1.100"     // Servidor adicional
};
```

#### **⚙️ Configurações Personalizadas**

Todas as configurações estão centralizadas em `sensor.ingest.local/config.py`:

```python
# Banco de dados
DB_CONFIG = {
    "user": "fiap",
    "password": "123456", 
    "dsn": "localhost:1521/FREEPDB1",
    "table_name": "sensor_readings"
}

# Servidor
SERVER_CONFIG = {
    "host": "0.0.0.0",
    "port": 8000,
    "debug": True
}

# Sensores válidos
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

# Configurações de query
QUERY_CONFIG = {
    "default_limit": 100,
    "max_limit": 1000
} 
```

#### **Endpoints Disponíveis:**
- `GET /data` - Recebe dados dos sensores
- `GET /get_all_data` - Lista todas as leituras
- `GET /health` - Status do servidor

#### **Como o ESP32 envia dados:**
```cpp
// Exemplo de URL para envio
POST http://servidor:8000/data
Content-Type: application/json
{
  "timestamp": 1234567890,
  "sensor_type": "temperature",
  "sensor_value": 25.5
}
```

#### **O que o Servidor Faz:**
1. **🔍 Verificação Automática**: Cria tabela Oracle se não existir
2. **📥 Ingestão de Dados**: Recebe dados via HTTP POST (JSON)
3. **✅ Validação**: Verifica parâmetros e tipos de dados
4. **🗄️ Persistência**: Armazena no Oracle Database
5. **📋 Consultas**: API para listar dados históricos
6. **🏥 Monitoramento**: Health check do sistema

#### **Características Técnicas:**
- **Porta**: 8000 (configurável)
- **Protocolo**: HTTP REST API
- **Banco**: Oracle Database (com auto-criação de tabelas)
- **Formato**: Dados em JSON/texto plano
- **Log**: Console com timestamps
- **Tratamento**: Rollback automático em caso de erro

### 5. Compilar e simular ESP32
```bash
# Compilar código ESP32
pio run
```
Após compilar, inicie a simulação no arquivo `diagram.json`

<p align="center">
<a><img src="imagens/play.png" alt="Esquema da ESP32 com sensores" border="0" width=100%></a>
</p>

Monitor serial ESP32:

<p align="center">
<a><img src="imagens/monitor_serial_1.png" alt="Imagem monitor serial" border="0" width=100%></a>
</p>
<p align="center">
<a><img src="imagens/monitor_serial_2.png" alt="Imagem monitor serial" border="0" width=100%></a>
</p>

Terminal do ``servidor.py`` ao rodar ESP32:

<p align="center">
<a><img src="imagens/terminal_servidor.png" alt="Imagem terminal do servidor" border="0" width=100%></a>
</p>

### 6. Análise dos Dados

#### Dashboard de Sensores IoT (Oracle)

Este dashboard foi desenvolvido em Streamlit para visualização e análise dos dados coletados por sensores IoT (temperatura, umidade, vibração e luminosidade) e armazenados em um banco de dados Oracle.

---

#### Visão Geral do Dashboard

<p align="center">
<a><img src="imagens/dashboard_1.png" alt="Visão Geral e Alertas" border="0" width=100%></a>
</p>
Visão geral do dashboard com alertas de não conformidade para umidade, luminosidade e vibração.

---

#### Objetivo

Permitir o acompanhamento em tempo real e a análise histórica das medições dos sensores conectados ao seu sistema IoT, facilitando a visualização de tendências, correlações e eventos relevantes.

---

#### Recursos do Dashboard

- **Visualização em tempo real** dos dados coletados
- **Filtro de período** (última hora, últimas 24h, tudo)
- **Cards de métricas rápidas** (últimos valores de cada grandeza)
- **Análises e Alertas de Não Conformidade**:
  - Destaca automaticamente valores fora da faixa ideal para umidade, luminosidade e eventos de vibração
- **Gráficos interativos** organizados em abas:
  - **Linha:** Temperatura e Umidade ao longo do tempo
  - **Barra:** Média de Luminosidade por Hora
  - **Dispersão:** Temperatura vs. Umidade
  - **Barra:** Contagem de Eventos de Vibração por Hora
- **Tabela de dados recentes**
- **Relatório e Exportação**:
  - Botão para baixar todos os dados em CSV
  - Resumo estatístico por tipo de sensor
- **Layout responsivo** e visual moderno

---

#### Análises e Alertas de Não Conformidade

O dashboard realiza automaticamente análises de não conformidade e exibe alertas visuais no topo da página para facilitar a identificação de situações críticas:

- **Umidade fora da faixa ideal:**
  - Alerta se algum valor de umidade estiver abaixo de 30% ou acima de 70%.
- **Luminosidade fora da faixa recomendada:**
  - Alerta se algum valor de luminosidade estiver abaixo de 300 ou acima de 3500.
- **Eventos de vibração detectados:**
  - Alerta se houver qualquer evento de vibração (valor 1).

Esses limites podem ser facilmente ajustados no código conforme a necessidade do seu projeto.

---

#### Relatório e Exportação

- **Download dos dados em CSV:**
  - Permite baixar todos os dados coletados para análise externa ou arquivamento.
- **Resumo estatístico por tipo de sensor:**
  - Exibe média, mínimo, máximo, desvio padrão e outros indicadores para cada grandeza coletada.

---

#### Gráficos Disponíveis

##### Linha: Temperatura e Umidade ao longo do tempo

<p align="center">
<a><img src="imagens/dashboard_2.png" alt="Gráfico de Linha - Temperatura e Umidade" border="0" width=100%></a>
</p>
Evolução da temperatura e umidade ao longo do tempo.

##### Barra: Média de Luminosidade por Hora

<p align="center">
<a><img src="imagens/dashboard_3.png" alt="Gráfico de Barra - Luminosidade" border="0" width=100%></a>
</p>
Média de luminosidade registrada em cada hora.

##### Dispersão: Temperatura vs. Umidade

<p align="center">
<a><img src="imagens/dashboard_4.png" alt="Gráfico de Dispersão - Temperatura vs. Umidade" border="0" width=100%></a>
</p>
Relação entre temperatura e umidade, útil para identificar correlações.

##### Barra: Eventos de Vibração por Hora
<p align="center">
<a><img src="imagens/dashboard_5.png" alt="Gráfico de Barra - Vibração" border="0" width=100%></a>
</p>
Contagem de eventos de vibração detectados em cada hora.

---

#### Tabela de Dados Recentes

<p align="center">
<a><img src="imagens/dashboard_6.png" alt="Tabela de Dados Recentes" border="0" width=100%></a>
</p>
Visualização dos registros mais recentes recebidos pelo sistema.

---

#### Relatório e Exportação

<p align="center">
<a><img src="imagens/dashboard_7.png" alt="Botão de Exportação CSV" border="0" width=100%></a>
</p>
Botão para baixar todos os dados em CSV.

<p align="center">
<a><img src="imagens/dashboard_8.png" alt="Resumo Estatístico" border="0" width=100%></a>
</p>
Resumo estatístico por tipo de sensor: média, mínimo, máximo, desvio padrão, etc.

---

#### Filtro de Período

<p align="center">
<a><img src="imagens/dashboard_9.png" alt="Filtro de Período" border="0" width=100%></a>
</p>
*Selecione o período desejado para análise: última hora, últimas 24h ou tudo.*

---

#### Menu de Configurações

<p align="center">
<a><img src="imagens/dashboard_10.png" alt="Menu de Configurações" border="0" width=100%></a>
</p>
Menu do Streamlit com opções para atualizar, imprimir, gravar screencast, limpar cache, etc.

---

#### Como Rodar o Dashboard

1. **Instale as dependências:**
   ```bash
   pip install streamlit pandas requests plotly
   ```
2. **Certifique-se de que o servidor Flask está rodando na porta 8000.**
3. **No terminal, execute:**
   ```bash
   streamlit run data/dashboard.py
   ```
4. **Acesse o dashboard pelo navegador:**
   - O endereço padrão será: [http://localhost:8501](http://localhost:8501)

---

#### Dicas de Uso

- Use o filtro de período para analisar dados recentes ou históricos.
- Passe o mouse sobre os gráficos para ver detalhes de cada ponto.
- Utilize as abas para alternar entre diferentes tipos de análise.
- Consulte a tabela de dados recentes para ver os últimos registros recebidos.
- Fique atento aos alertas de não conformidade no topo do dashboard.
- Utilize o botão de download para exportar os dados em CSV e o resumo estatístico para análises rápidas.

---

#### Dependências
- [Streamlit](https://streamlit.io/)
- [Pandas](https://pandas.pydata.org/)
- [Requests](https://docs.python-requests.org/)
- [Plotly](https://plotly.com/python/)

---

### 7. Verificação do Sistema Completo

#### **🔍 Testar se tudo está funcionando:**

```bash
# 1. Verificar Oracle
docker ps | grep oracle-free  # Deve mostrar container rodando

# 2. Testar servidor Flask
curl http://localhost:8000/health
# Resposta esperada: {"status": "ok", "database": "ok", ...}

# 3. Simular dados do ESP32
curl -X POST http://localhost:8000/data \
  -H "Content-Type: application/json" \
  -d '{"timestamp": 1234567890, "sensor_type": "temperature", "sensor_value": 25.5}'
# Resposta: "Dados recebidos com sucesso"

# 4. Consultar dados salvos
curl http://localhost:8000/sensors
# Deve retornar JSON com os dados inseridos
```

### 8. Resultados Obtidos
O sistema gera automaticamente:
- 📊 **Gráficoss e Insigths**: `data/dashboard_*.png` (10 visualizações completas)
- 📈 **Estatísticas detalhadas** no terminal
- 📄 **Dados CSV** prontos para análise
- 🗄️ **Dados no Oracle** (se usar servidor)
- 🐳 **Banco Oracle** rodando no Docker ou localmente

## Casos de Uso

### 🎯 **Simulação Simples (Wokwi)**
**Para:** Demonstrações, aprendizado, prototipagem
```
1. Use apenas: Wokwi + Análise Python
2. Dados: CSV estático
3. Tempo: 5-10 minutos para configurar
```

### 🏗️ **Sistema Completo (Produção)**
**Para:** Projetos reais, IoT em escala, monitoramento contínuo
```
1. Use: Docker Oracle + ESP32 + Servidor Flask + Análise
2. Dados: Tempo real no banco
3. Tempo: 30-60 minutos para configurar
4. Passos: Seções 3 → 4 → 5 do README
```

### 📊 **Apenas Análise (Offline)**
**Para:** Análise de dados existentes
```
1. Use apenas: Python + CSV
2. Dados: Arquivo estático
3. Tempo: 2-5 minutos
```

## Funcionalidades Implementadas
- ✅ **Simulação ESP32**: Circuito virtual com 3 sensores no Wokwi
- ✅ **Sensores Configurados**: DHT22, SW-420, LDR com valores realistas
- ✅ **Código Arduino**: Leitura a cada 2 segundos com simulação de padrões
- ✅ **Servidor de Ingestão**: Flask + Oracle para dados em tempo real
- ✅ **Saída CSV**: Formato padronizado para análise
- ✅ **Visualização**: Gráficos automáticos com estatísticas
- ✅ **Documentação**: Instruções completas de reprodução

## Cenários Simulados
- **Temperatura**: 15°C a 35°C (ambiente interno)
- **Vibração**: 0-1023 (digital com ruído simulado)
- **Luminosidade**: 0-4095 (variação dia/noite)

## Componentes do Sistema

### 🔧 **ESP32 + Sensores (IoT)**
- **Hardware**: ESP32-DevKitC V4
- **Plataforma**: Wokwi Simulator
- **Linguagem**: C++ (Arduino Framework)
- **Sensores**: DHT22, SW-420, LDR

### 🖥️ **Servidor de Ingestão (Backend)**
- **Framework**: Flask (Python)
- **Banco de Dados**: Oracle Database
- **API**: REST endpoints para receber dados dos sensores
- **Funcionalidades**:
  - Recebe dados dos sensores ESP32 via HTTP
  - Armazena no Oracle Database
  - Valida e processa dados em tempo real
  - Endpoints para consulta e monitoramento

### 📊 **Análise de Dados (Analytics)**
- **Linguagem**: Python
- **Bibliotecas**: Matplotlib, Pandas, NumPy
- **Saída**: Gráficos e estatísticas detalhadas

## Fluxo de Dados Completo

```
🔧 ESP32 Sensors → 📡 HTTP Request → 🖥️ Flask Server → 🐳 Docker Oracle
                                           ↓              ↓
📊 Python Analysis ← 📄 CSV Export ← 🔍 Data Query ← 🗄️ Oracle DB
```

## Arquivos Importantes
- 🔧 `platformio.ini`: Configuração do PlatformIO
- 🖥️ `sensor.ingest.local/servidor.py`: Servidor de ingestão de dados
- 🐳 `scripts/setup-oracle-docker.sh`: Setup automático do Oracle (Linux/macOS)
- 🪟 `scripts/setup-oracle-docker.bat`: Setup automático do Oracle (Windows Batch) 
- ⚡ `scripts/setup-oracle-docker.ps1`: Setup automático do Oracle (Windows PowerShell)
- ⚙️ `INSTRUÇÕES_IMPORTANTES.md`: Como evitar erros de debug

---
*Projeto desenvolvido para demonstrar conceitos de IoT e análise de dados.* 

### 🧑‍💻 **Trecho Representativo do Código**

```cpp
// Leitura do sensor de temperatura e umidade
float temperature = dht.readTemperature();
float humidity = dht.readHumidity();
Serial.print("Temperature: ");
Serial.println(temperature);
Serial.print("Humidity: ");
Serial.println(humidity);

// Leitura do sensor de vibração
int vibration = digitalRead(SW420_PIN);
Serial.print("Vibration: ");
Serial.println(vibration);

// Leitura do sensor de luminosidade
int luminosity = analogRead(LDR_PIN);
Serial.print("Luminosity: ");
Serial.println(luminosity);
```

> *O código acima exemplifica a leitura dos sensores e o envio dos dados para o Monitor Serial, simulando o comportamento de um sistema embarcado real.*

---

### 🔄 **Fluxo de Dados do Sistema**

```mermaid
graph TD;
  A["Sensores Virtuais (DHT22, SW-420, LDR)"] --> B["ESP32 (Simulação)"];
  B --> C["Monitor Serial / Exportação CSV"];
  C --> D["Análise Python (Pandas/Matplotlib)"];
  D --> E["Geração de Gráficos e Insights"];
```

---
### 📈 **Insights Iniciais da Análise**
> 5 registros de umidade fora da faixa ideal (30-70%)!
> 1 registros de luminosidade fora da faixa recomendada (300-3500)!
> Nenhum evento de vibração detectado.
---

### ✅ **Checklist dos Entregáveis**

- [x] Imagens da simulação do circuito (print Wokwi ou similar)
- [x] Lista e justificativa dos sensores virtuais
- [x] Código-fonte comentado da leitura e visualização de dados simulados
- [x] Prints do comportamento da simulação (Monitor Serial ou simulação de dados)
- [x] Gráficos e insights iniciais da análise exploratória
- [x] README estruturado e explicativo

---

### 📚 **Referências e Agradecimentos**

- [Wokwi - Simulador de Circuitos](https://wokwi.com/)
- [PlatformIO](https://platformio.org/)
- [FIAP](https://www.fiap.com.br/)
- [Hermes Reply](https://www.reply.com/hermes-reply/)
- Datasheets dos sensores: [DHT22](https://cdn.sparkfun.com/datasheets/Sensors/Temperature/DHT22.pdf), [SW-420](https://components101.com/sensors/vibration-sensor-module-sw-420), [LDR](https://www.electronics-tutorials.ws/io/photoresistor.html)

> **Agradecimentos à Hermes Reply e à FIAP pela proposta do desafio e apoio ao desenvolvimento do projeto.**

---
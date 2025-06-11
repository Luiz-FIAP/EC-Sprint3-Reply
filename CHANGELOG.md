# Changelog - Sistema de Monitoramento IoT

## [v3.0] - 2024-06-10

### ⚠️ **BREAKING CHANGES**
- **Protocolo de comunicação**: GET → POST com JSON
- **Endpoint `/data`**: Agora aceita apenas POST com `Content-Type: application/json`
- **Formato de dados**: Query parameters → JSON body

### 🔄 **Principais Alterações**

#### **Protocolo HTTP Correto para IoT:**
- ✅ **Servidor Flask**: Rota `/data` agora usa POST
- ✅ **Validação JSON**: Verificação de Content-Type obrigatória
- ✅ **Dados no corpo**: JSON em vez de query parameters
- ✅ **Segurança**: Dados não expostos na URL

#### **ESP32 com Conectividade WiFi:**
- ✅ **WiFi integrado**: Conexão automática com fallback
- ✅ **HTTP POST**: Envio correto via requisições POST
- ✅ **Formato JSON**: Dados estruturados corretamente
- ✅ **Múltiplos sensores**: Envio de todos os tipos de sensor
- ✅ **Reconexão automática**: Recuperação de falhas de rede
- ✅ **Backup CSV**: Dados salvos localmente se offline

#### **Melhorias Técnicas:**
- ✅ **ArduinoJson**: Biblioteca para manipulação JSON no ESP32
- ✅ **Validações robustas**: Verificação de dados no servidor
- ✅ **Script de teste**: `test_api.py` para validar API
- ✅ **Documentação atualizada**: Exemplos com POST e JSON

#### **Arquivos Modificados:**
- `sensor.ingest.local/servidor.py` - Rota POST com JSON
- `src/main.cpp` - WiFi + HTTP POST completo
- `platformio.ini` - ArduinoJson adicionado
- `README.md` - Documentação atualizada
- `test_api.py` - Novo script de teste

#### **Exemplo de Uso:**
```bash
# Antes (GET - INCORRETO):
curl "http://localhost:8000/data?sensor_type=temperature&sensor_value=25.5"

# Agora (POST - CORRETO):
curl -X POST http://localhost:8000/data \
  -H "Content-Type: application/json" \
  -d '{"sensor_type": "temperature", "sensor_value": 25.5}'
```

---

## [v2.0] - 2024-06-10

### 🔄 Mudanças nas Configurações do Banco de Dados

#### **Alterações Principais:**
- **Usuário**: `system` → `fiap`
- **Senha**: `MinhaSenha123` → `123456`
- **Tabela**: `sensor_ingest_local` → `sensor_readings`
- **DSN**: `localhost/FREEPDB1` → `localhost:1521/FREEPDB1`

#### **Arquivos Modificados:**
- ✅ `scripts/setup-oracle-docker.sh`
  - Senha do Oracle alterada
  - Criação automática do usuário FIAP
  - Permissões configuradas automaticamente

- ✅ `sensor.ingest.local/servidor.py`
  - Configurações atualizadas para usar usuário FIAP
  - Refatorado para usar arquivo de configuração

- ✅ `sensor.ingest.local/config.py` (NOVO)
  - Configurações centralizadas
  - Facilita manutenção e personalização
  - Separação de responsabilidades

- ✅ `README.md`
  - Documentação atualizada
  - Novos exemplos de conexão
  - Seção de configurações personalizadas

#### **Melhorias Técnicas:**
1. **Configurações Centralizadas**: Todas as configurações em um arquivo
2. **Usuário Dedicado**: Criação automática do usuário FIAP no Oracle
3. **Segurança**: Permissões específicas para o usuário da aplicação
4. **Manutenibilidade**: Mais fácil de configurar e manter

#### **Migração:**
Para migrar de versões anteriores:
```bash
# 1. Recrie o container Oracle com nova senha
./scripts/setup-oracle-docker.sh

# 2. O usuário FIAP será criado automaticamente
# 3. A tabela sensor_readings será criada automaticamente
# 4. Nenhuma configuração manual necessária
```

---

## [v1.0] - 2024-06-10

### 🚀 Versão Inicial
- Sistema de simulação ESP32 com sensores
- Servidor Flask para ingestão de dados
- Banco Oracle no Docker
- Análise Python com gráficos
- Documentação completa 
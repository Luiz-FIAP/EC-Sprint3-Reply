# Changelog - Sistema de Monitoramento IoT

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
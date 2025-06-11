#!/bin/bash

# Script para configurar Oracle Database Free no Docker
# Sistema de Monitoramento IoT com ESP32

set -e  # Para o script se houver erro

echo "🚀 Configurando Oracle Database Free no Docker..."
echo "=================================================="

# Verificar se Docker está instalado
if ! command -v docker &> /dev/null; then
    echo "❌ Docker não está instalado!"
    echo "📥 Baixe em: https://www.docker.com/products/docker-desktop/"
    exit 1
fi

echo "✅ Docker encontrado: $(docker --version)"

# Verificar se container já existe
if docker ps -a | grep -q oracle-free; then
    echo "⚠️  Container 'oracle-free' já existe"
    read -p "Deseja removê-lo e criar novo? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "🗑️  Removendo container existente..."
        docker rm -f oracle-free || true
        docker volume rm oracle-data || true
    else
        echo "🔄 Usando container existente..."
        docker start oracle-free
        
        # Verificar se usuário FIAP já existe
        echo "🔍 Verificando usuário FIAP..."
        if docker exec oracle-free sqlplus -s fiap/123456@FREEPDB1 <<< "SELECT 'FIAP_USER_EXISTS' FROM DUAL; EXIT;" 2>/dev/null | grep -q "FIAP_USER_EXISTS"; then
            echo "✅ Usuário FIAP já configurado!"
            echo "📊 Sistema pronto para uso!"
            exit 0
        else
            echo "🔧 Usuário FIAP não encontrado, criando..."
        fi
    fi
fi

# Verificar memória disponível
echo "🔍 Verificando recursos do sistema..."
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    MEM_GB=$(( $(sysctl -n hw.memsize) / 1024 / 1024 / 1024 ))
else
    # Linux
    MEM_GB=$(free -g | awk '/^Mem:/{print $2}')
fi

echo "💾 Memória disponível: ${MEM_GB}GB"
if [ $MEM_GB -lt 8 ]; then
    echo "⚠️  Recomendado: 8GB+ de RAM para Oracle"
    read -p "Continuar mesmo assim? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Criar e executar container Oracle se não existir
if ! docker ps -a | grep -q oracle-free; then
    echo "📦 Criando container Oracle Database Free..."
    docker run -d \
      --name oracle-free \
      -p 1521:1521 \
      -p 5500:5500 \
      -e ORACLE_PWD=123456 \
      -e ORACLE_CHARACTERSET=AL32UTF8 \
      -v oracle-data:/opt/oracle/oradata \
      container-registry.oracle.com/database/free:latest
fi

echo "⏳ Aguardando inicialização do Oracle..."
echo "   (Isso pode levar 5-10 minutos na primeira vez)"
echo "   Pressione Ctrl+C para parar de acompanhar os logs"

# Acompanhar logs até ver a mensagem de pronto
timeout 600 docker logs -f oracle-free &
LOG_PID=$!

# Verificar se ficou pronto
READY=false
for i in {1..60}; do
    if docker logs oracle-free 2>&1 | grep -q "DATABASE IS READY TO USE"; then
        READY=true
        break
    fi
    sleep 10
    echo "⏳ Ainda inicializando... (${i}0s)"
done

kill $LOG_PID 2>/dev/null || true

if [ "$READY" = true ]; then
    echo ""
    echo "✅ Oracle Database está pronto!"
    echo "🔧 Criando usuário FIAP..."
    
    # Aguardar mais um pouco para garantir que o serviço esteja completamente pronto
    sleep 5
    
    # Criar usuário FIAP no Oracle
    USER_CREATION_RESULT=$(docker exec oracle-free sqlplus -s sys/123456@FREEPDB1 as sysdba <<EOF
SET PAGESIZE 0
SET FEEDBACK OFF
SET HEADING OFF
WHENEVER SQLERROR EXIT SQL.SQLCODE

-- Tentar remover usuário se já existir (ignora erro se não existir)
BEGIN
    EXECUTE IMMEDIATE 'DROP USER fiap CASCADE';
EXCEPTION
    WHEN OTHERS THEN
        IF SQLCODE != -1918 THEN -- -1918 = usuário não existe
            RAISE;
        END IF;
END;
/

-- Criar usuário FIAP
CREATE USER fiap IDENTIFIED BY 123456;

-- Conceder privilégios necessários
GRANT CONNECT, RESOURCE, CREATE SESSION, CREATE TABLE, CREATE SEQUENCE TO fiap;
GRANT UNLIMITED TABLESPACE TO fiap;

-- Confirmar criação
SELECT 'USER_CREATED_SUCCESS' FROM DUAL;

EXIT;
EOF
)
    
    # Verificar se a criação foi bem-sucedida
    if echo "$USER_CREATION_RESULT" | grep -q "USER_CREATED_SUCCESS"; then
        echo "✅ Usuário FIAP criado com sucesso!"
        
        # Testar conexão com o usuário FIAP
        echo "🧪 Testando conexão do usuário FIAP..."
        TEST_RESULT=$(docker exec oracle-free sqlplus -s fiap/123456@FREEPDB1 <<< "SELECT 'CONNECTION_OK' FROM DUAL; EXIT;" 2>/dev/null)
        
        if echo "$TEST_RESULT" | grep -q "CONNECTION_OK"; then
            echo "✅ Conexão do usuário FIAP testada com sucesso!"
        else
            echo "⚠️  Aviso: Usuário criado mas teste de conexão falhou"
        fi
    else
        echo "❌ Erro ao criar usuário FIAP"
        echo "🔍 Detalhes do erro:"
        echo "$USER_CREATION_RESULT"
        echo "⚠️  Você pode tentar criar manualmente:"
        echo "   docker exec -it oracle-free sqlplus sys/123456@FREEPDB1 as sysdba"
    fi
    
    echo "=================================================="
    echo "📊 Informações de Conexão:"
    echo "   Host: localhost"
    echo "   Porta: 1521"
    echo "   Service Name: FREEPDB1"
    echo "   Usuário: fiap"
    echo "   Senha: 123456"
    echo ""
    echo "🔗 String de Conexão Python:"
    echo "   DB_DSN = 'localhost:1521/FREEPDB1'"
    echo ""
    echo "🔗 Para cliente de banco (ex: DBeaver):"
    echo "   Tipo: Oracle"
    echo "   Host: localhost"
    echo "   Porta: 1521"
    echo "   Database: FREEPDB1 (Service Name, não SID)"
    echo "   Usuário: fiap"
    echo "   Senha: 123456"
    echo ""
    echo "🌐 Enterprise Manager:"
    echo "   https://localhost:5500/em"
    echo "   Usuário: sys"
    echo "   Senha: 123456"
    echo "   Container: FREEPDB1"
    echo ""
    echo "💡 Próximos passos:"
    echo "   1. cd sensor.ingest.local"
    echo "   2. python3 servidor.py"
    echo "   3. Testar: curl http://localhost:8000/health"
else
    echo ""
    echo "❌ Oracle não ficou pronto no tempo esperado"
    echo "🔍 Verifique os logs: docker logs oracle-free"
    echo "⏭️  Pode ser que ainda esteja inicializando..."
    echo "🔄 Tente executar novamente este script em alguns minutos"
fi

echo ""
echo "🛠️  Comandos úteis:"
echo "   docker logs oracle-free              # Ver logs"
echo "   docker stop oracle-free             # Parar"
echo "   docker start oracle-free            # Iniciar"
echo "   docker rm -f oracle-free            # Remover"
echo "   docker exec -it oracle-free bash    # Acessar container"
echo "   docker exec -it oracle-free sqlplus fiap/123456@FREEPDB1  # SQL*Plus" 
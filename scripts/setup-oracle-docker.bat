@echo off
REM Script para configurar Oracle Database Free no Docker
REM Sistema de Monitoramento IoT com ESP32
REM Compatível com Windows

setlocal EnableDelayedExpansion

echo 🚀 Configurando Oracle Database Free no Docker...
echo ==================================================

REM Verificar se Docker está instalado
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Docker não está instalado!
    echo 📥 Baixe em: https://www.docker.com/products/docker-desktop/
    pause
    exit /b 1
)

echo ✅ Docker encontrado
docker --version

REM Verificar se container já existe
docker ps -a | findstr "oracle-free" >nul 2>&1
if %errorlevel% == 0 (
    echo ⚠️  Container 'oracle-free' já existe
    set /p "resposta=Deseja removê-lo e criar novo? (s/N): "
    if /i "!resposta!"=="s" (
        echo 🗑️  Removendo container existente...
        docker rm -f oracle-free 2>nul
        docker volume rm oracle-data 2>nul
    ) else (
        echo 🔄 Usando container existente...
        docker start oracle-free
        
        REM Verificar se usuário FIAP já existe
        echo 🔍 Verificando usuário FIAP...
        docker exec oracle-free sqlplus -s fiap/123456@FREEPDB1 -c "SELECT 'FIAP_USER_EXISTS' FROM DUAL; EXIT;" >nul 2>&1
        if !errorlevel! == 0 (
            echo ✅ Usuário FIAP já configurado!
            echo 📊 Sistema pronto para uso!
            goto :end
        ) else (
            echo 🔧 Usuário FIAP não encontrado, criando...
        )
    )
)

REM Verificar memória disponível (Windows)
echo 🔍 Verificando recursos do sistema...
for /f "tokens=2 delims==" %%i in ('wmic computersystem get TotalPhysicalMemory /value ^| findstr "="') do set "memory=%%i"
set /a "memory_gb=!memory! / 1024 / 1024 / 1024"
echo 💾 Memória disponível: !memory_gb!GB

if !memory_gb! lss 8 (
    echo ⚠️  Recomendado: 8GB+ de RAM para Oracle
    set /p "continuar=Continuar mesmo assim? (s/N): "
    if /i not "!continuar!"=="s" (
        exit /b 1
    )
)

REM Criar e executar container Oracle se não existir
docker ps -a | findstr "oracle-free" >nul 2>&1
if %errorlevel% neq 0 (
    echo 📦 Criando container Oracle Database Free...
    $dockerCommand = @"
    docker run -d ^
      --name oracle-free ^
      -p 1521:1521 ^
      -p 5500:5500 ^
      -e ORACLE_PWD=123456 ^
      -e ORACLE_CHARACTERSET=AL32UTF8 ^
      -v oracle-data:/opt/oracle/oradata ^
      container-registry.oracle.com/database/free:latest
)

echo ⏳ Aguardando inicialização do Oracle...
echo    (Isso pode levar 5-10 minutos na primeira vez)
echo    Pressione Ctrl+C para parar de acompanhar os logs

REM Verificar se ficou pronto (Windows PowerShell para timeout)
set "ready=false"
set "attempts=0"

:check_ready
if !attempts! geq 60 goto :timeout_reached

docker logs oracle-free 2>&1 | findstr "DATABASE IS READY TO USE" >nul 2>&1
if %errorlevel% == 0 (
    set "ready=true"
    goto :database_ready
)

set /a "attempts+=1"
set /a "seconds=!attempts! * 10"
echo ⏳ Ainda inicializando... (!seconds!s)
timeout /t 10 /nobreak >nul
goto :check_ready

:timeout_reached
echo.
echo ❌ Oracle não ficou pronto no tempo esperado
echo 🔍 Verifique os logs: docker logs oracle-free
echo ⏭️  Pode ser que ainda esteja inicializando...
echo 🔄 Tente executar novamente este script em alguns minutos
goto :show_commands

:database_ready
echo.
echo ✅ Oracle Database está pronto!
echo 🔧 Criando usuário FIAP...

REM Aguardar mais um pouco para garantir que o serviço esteja completamente pronto
timeout /t 5 /nobreak >nul

REM Criar usuário FIAP no Oracle
echo SET PAGESIZE 0> temp_oracle_script.sql
echo SET FEEDBACK OFF>> temp_oracle_script.sql
echo SET HEADING OFF>> temp_oracle_script.sql
echo WHENEVER SQLERROR EXIT SQL.SQLCODE>> temp_oracle_script.sql
echo.>> temp_oracle_script.sql
echo -- Tentar remover usuário se já existir (ignora erro se não existir)>> temp_oracle_script.sql
echo BEGIN >> temp_oracle_script.sql
echo     EXECUTE IMMEDIATE 'DROP USER fiap CASCADE';>> temp_oracle_script.sql
echo EXCEPTION>> temp_oracle_script.sql
echo     WHEN OTHERS THEN>> temp_oracle_script.sql
echo         IF SQLCODE != -1918 THEN -- -1918 = usuário não existe>> temp_oracle_script.sql
echo             RAISE;>> temp_oracle_script.sql
echo         END IF;>> temp_oracle_script.sql
echo END;>> temp_oracle_script.sql
echo />> temp_oracle_script.sql
echo.>> temp_oracle_script.sql
echo -- Criar usuário FIAP>> temp_oracle_script.sql
echo CREATE USER fiap IDENTIFIED BY 123456;>> temp_oracle_script.sql
echo.>> temp_oracle_script.sql
echo -- Conceder privilégios necessários>> temp_oracle_script.sql
echo GRANT CONNECT, RESOURCE, CREATE SESSION, CREATE TABLE, CREATE SEQUENCE TO fiap;>> temp_oracle_script.sql
echo GRANT UNLIMITED TABLESPACE TO fiap;>> temp_oracle_script.sql
echo.>> temp_oracle_script.sql
echo -- Confirmar criação>> temp_oracle_script.sql
echo SELECT 'USER_CREATED_SUCCESS' FROM DUAL;>> temp_oracle_script.sql
echo.>> temp_oracle_script.sql
echo EXIT;>> temp_oracle_script.sql

REM Executar script no Oracle
docker exec -i oracle-free sqlplus -s sys/123456@FREEPDB1 as sysdba < temp_oracle_script.sql > user_creation_result.txt 2>&1

REM Verificar se a criação foi bem-sucedida
findstr "USER_CREATED_SUCCESS" user_creation_result.txt >nul 2>&1
if %errorlevel% == 0 (
    echo ✅ Usuário FIAP criado com sucesso!
    
    REM Testar conexão com o usuário FIAP
    echo 🧪 Testando conexão do usuário FIAP...
    echo SELECT 'CONNECTION_OK' FROM DUAL; EXIT; | docker exec -i oracle-free sqlplus -s fiap/123456@FREEPDB1 > test_connection.txt 2>&1
    
    findstr "CONNECTION_OK" test_connection.txt >nul 2>&1
    if !errorlevel! == 0 (
        echo ✅ Conexão do usuário FIAP testada com sucesso!
    ) else (
        echo ⚠️  Aviso: Usuário criado mas teste de conexão falhou
    )
) else (
    echo ❌ Erro ao criar usuário FIAP
    echo 🔍 Detalhes do erro:
    type user_creation_result.txt
    echo ⚠️  Você pode tentar criar manualmente:
    echo    docker exec -it oracle-free sqlplus sys/123456@FREEPDB1 as sysdba
)

REM Limpar arquivos temporários
del temp_oracle_script.sql 2>nul
del user_creation_result.txt 2>nul
del test_connection.txt 2>nul

echo ==================================================
echo 📊 Informações de Conexão:
echo    Host: localhost
echo    Porta: 1521
echo    Service Name: FREEPDB1
echo    Usuário: fiap
echo    Senha: 123456
echo.
echo 🔗 String de Conexão Python:
echo    DB_DSN = 'localhost:1521/FREEPDB1'
echo.
echo 🔗 Para cliente de banco (ex: DBeaver):
echo    Tipo: Oracle
echo    Host: localhost
echo    Porta: 1521
echo    Database: FREEPDB1 (Service Name, não SID)
echo    Usuário: fiap
echo    Senha: 123456
echo.
echo 🌐 Enterprise Manager:
echo    https://localhost:5500/em
echo    Usuário: sys
echo    Senha: 123456
echo    Container: FREEPDB1
echo.
echo 💡 Próximos passos:
echo    1. cd sensor.ingest.local
echo    2. python servidor.py
echo    3. Testar: curl http://localhost:8000/health

:show_commands
echo.
echo 🛠️  Comandos úteis:
echo    docker logs oracle-free              # Ver logs
echo    docker stop oracle-free             # Parar
echo    docker start oracle-free            # Iniciar
echo    docker rm -f oracle-free            # Remover
echo    docker exec -it oracle-free bash    # Acessar container
echo    docker exec -it oracle-free sqlplus fiap/123456@FREEPDB1  # SQL*Plus

:end
echo.
pause 
# Script PowerShell para configurar Oracle Database Free no Docker
# Sistema de Monitoramento IoT com ESP32
# Compatível com Windows PowerShell 5.0+

param(
    [switch]$Force,
    [switch]$SkipMemoryCheck
)

# Configurações
$ContainerName = "oracle-free"
$VolumeName = "oracle-data"
$OraclePassword = "123456"
$ImageName = "container-registry.oracle.com/database/free:latest"

# Função para exibir mensagens coloridas
function Write-ColoredOutput {
    param(
        [string]$Message,
        [string]$Color = "White"
    )
    Write-Host $Message -ForegroundColor $Color
}

# Função para verificar se comando existe
function Test-Command {
    param([string]$Command)
    try {
        Get-Command $Command -ErrorAction Stop | Out-Null
        return $true
    }
    catch {
        return $false
    }
}

# Cabeçalho
Write-ColoredOutput "🚀 Configurando Oracle Database Free no Docker..." "Cyan"
Write-ColoredOutput "==================================================" "Cyan"

# 1. Verificar se Docker está instalado
Write-ColoredOutput "🔍 Verificando Docker..." "Yellow"
if (-not (Test-Command "docker")) {
    Write-ColoredOutput "❌ Docker não está instalado!" "Red"
    Write-ColoredOutput "📥 Baixe em: https://www.docker.com/products/docker-desktop/" "Yellow"
    exit 1
}

$dockerVersion = docker --version
Write-ColoredOutput "✅ Docker encontrado: $dockerVersion" "Green"

# 2. Verificar se container já existe
Write-ColoredOutput "🔍 Verificando container existente..." "Yellow"
$existingContainer = docker ps -a --filter "name=$ContainerName" --format "{{.Names}}" 2>$null

if ($existingContainer -eq $ContainerName) {
    Write-ColoredOutput "⚠️  Container '$ContainerName' já existe" "Yellow"
    
    if (-not $Force) {
        $response = Read-Host "Deseja removê-lo e criar novo? (s/N)"
        if ($response -notmatch "^[Ss]$") {
            Write-ColoredOutput "🔄 Usando container existente..." "Cyan"
            docker start $ContainerName | Out-Null
            
            # Verificar se usuário FIAP já existe
            Write-ColoredOutput "🔍 Verificando usuário FIAP..." "Yellow"
            $testUser = docker exec $ContainerName sqlplus -s fiap/123456@FREEPDB1 -c "SELECT 'FIAP_USER_EXISTS' FROM DUAL; EXIT;" 2>$null
            
            if ($LASTEXITCODE -eq 0) {
                Write-ColoredOutput "✅ Usuário FIAP já configurado!" "Green"
                Write-ColoredOutput "📊 Sistema pronto para uso!" "Green"
                exit 0
            } else {
                Write-ColoredOutput "🔧 Usuário FIAP não encontrado, criando..." "Yellow"
            }
        } else {
            $Force = $true
        }
    }
    
    if ($Force) {
        Write-ColoredOutput "🗑️  Removendo container existente..." "Yellow"
        docker rm -f $ContainerName 2>$null | Out-Null
        docker volume rm $VolumeName 2>$null | Out-Null
    }
}

# 3. Verificar recursos do sistema
if (-not $SkipMemoryCheck) {
    Write-ColoredOutput "🔍 Verificando recursos do sistema..." "Yellow"
    $memory = Get-WmiObject -Class Win32_ComputerSystem
    $memoryGB = [Math]::Round($memory.TotalPhysicalMemory / 1GB, 1)
    Write-ColoredOutput "💾 Memória disponível: ${memoryGB}GB" "Cyan"
    
    if ($memoryGB -lt 8) {
        Write-ColoredOutput "⚠️  Recomendado: 8GB+ de RAM para Oracle" "Yellow"
        $continue = Read-Host "Continuar mesmo assim? (s/N)"
        if ($continue -notmatch "^[Ss]$") {
            exit 1
        }
    }
}

# 4. Criar container Oracle se não existir
$runningContainer = docker ps --filter "name=$ContainerName" --format "{{.Names}}" 2>$null
if ($runningContainer -ne $ContainerName) {
    Write-ColoredOutput "📦 Criando container Oracle Database Free..." "Cyan"
    
    $dockerRun = @(
        "run", "-d",
        "--name", $ContainerName,
        "-p", "1521:1521",
        "-p", "5500:5500",
        "-e", "ORACLE_PWD=$OraclePassword",
        "-e", "ORACLE_CHARACTERSET=AL32UTF8",
        "-v", "${VolumeName}:/opt/oracle/oradata",
        $ImageName
    )
    
    docker @dockerRun | Out-Null
    
    if ($LASTEXITCODE -ne 0) {
        Write-ColoredOutput "❌ Erro ao criar container!" "Red"
        exit 1
    }
}

# 5. Aguardar inicialização
Write-ColoredOutput "⏳ Aguardando inicialização do Oracle..." "Yellow"
Write-ColoredOutput "   (Isso pode levar 5-10 minutos na primeira vez)" "Gray"
Write-ColoredOutput "   Pressione Ctrl+C para interromper" "Gray"

$maxAttempts = 60
$attempt = 0
$ready = $false

do {
    $attempt++
    $seconds = $attempt * 10
    
    $logs = docker logs $ContainerName 2>&1
    if ($logs -match "DATABASE IS READY TO USE") {
        $ready = $true
        break
    }
    
    Write-ColoredOutput "⏳ Ainda inicializando... (${seconds}s)" "Yellow"
    Start-Sleep -Seconds 10
    
} while ($attempt -lt $maxAttempts)

if (-not $ready) {
    Write-ColoredOutput "" "White"
    Write-ColoredOutput "❌ Oracle não ficou pronto no tempo esperado" "Red"
    Write-ColoredOutput "🔍 Verifique os logs: docker logs $ContainerName" "Yellow"
    Write-ColoredOutput "⏭️  Pode ser que ainda esteja inicializando..." "Gray"
    Write-ColoredOutput "🔄 Tente executar novamente este script em alguns minutos" "Gray"
} else {
    Write-ColoredOutput "" "White"
    Write-ColoredOutput "✅ Oracle Database está pronto!" "Green"
    Write-ColoredOutput "🔧 Criando usuário FIAP..." "Cyan"
    
    # Aguardar mais alguns segundos
    Start-Sleep -Seconds 5
    
    # 6. Criar usuário FIAP
    $sqlScript = @"
SET PAGESIZE 0
SET FEEDBACK OFF
SET HEADING OFF
WHENEVER SQLERROR EXIT SQL.SQLCODE

-- Tentar remover usuário se já existir
BEGIN
    EXECUTE IMMEDIATE 'DROP USER fiap CASCADE';
EXCEPTION
    WHEN OTHERS THEN
        IF SQLCODE != -1918 THEN
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
"@
    
    # Salvar script temporário
    $tempScript = [System.IO.Path]::GetTempFileName() + ".sql"
    $sqlScript | Out-File -FilePath $tempScript -Encoding ASCII
    
    try {
        # Executar script
        $result = Get-Content $tempScript | docker exec -i $ContainerName sqlplus -s sys/123456@FREEPDB1 as sysdba 2>&1
        
        if ($result -match "USER_CREATED_SUCCESS") {
            Write-ColoredOutput "✅ Usuário FIAP criado com sucesso!" "Green"
            
            # Testar conexão
            Write-ColoredOutput "🧪 Testando conexão do usuário FIAP..." "Yellow"
            $testResult = "SELECT 'CONNECTION_OK' FROM DUAL; EXIT;" | docker exec -i $ContainerName sqlplus -s fiap/123456@FREEPDB1 2>&1
            
            if ($testResult -match "CONNECTION_OK") {
                Write-ColoredOutput "✅ Conexão do usuário FIAP testada com sucesso!" "Green"
            } else {
                Write-ColoredOutput "⚠️  Aviso: Usuário criado mas teste de conexão falhou" "Yellow"
            }
        } else {
            Write-ColoredOutput "❌ Erro ao criar usuário FIAP" "Red"
            Write-ColoredOutput "🔍 Detalhes do erro:" "Yellow"
            Write-ColoredOutput $result "Red"
            Write-ColoredOutput "⚠️  Você pode tentar criar manualmente:" "Yellow"
            Write-ColoredOutput "   docker exec -it $ContainerName sqlplus sys/123456@FREEPDB1 as sysdba" "Gray"
        }
    } finally {
        # Limpar arquivo temporário
        Remove-Item $tempScript -Force -ErrorAction SilentlyContinue
    }
}

# 7. Exibir informações finais
Write-ColoredOutput "" "White"
Write-ColoredOutput "==================================================" "Cyan"
Write-ColoredOutput "📊 Informações de Conexão:" "White"
Write-ColoredOutput "   Host: localhost" "Gray"
Write-ColoredOutput "   Porta: 1521" "Gray"
Write-ColoredOutput "   Service Name: FREEPDB1" "Gray"
Write-ColoredOutput "   Usuário: fiap" "Gray"
Write-ColoredOutput "   Senha: 123456" "Gray"
Write-ColoredOutput "" "White"
Write-ColoredOutput "🔗 String de Conexão Python:" "White"
Write-ColoredOutput "   DB_DSN = 'localhost:1521/FREEPDB1'" "Gray"
Write-ColoredOutput "" "White"
Write-ColoredOutput "🔗 Para cliente de banco (ex: DBeaver):" "White"
Write-ColoredOutput "   Tipo: Oracle" "Gray"
Write-ColoredOutput "   Host: localhost" "Gray"
Write-ColoredOutput "   Porta: 1521" "Gray"
Write-ColoredOutput "   Database: FREEPDB1 (Service Name, não SID)" "Gray"
Write-ColoredOutput "   Usuário: fiap" "Gray"
Write-ColoredOutput "   Senha: 123456" "Gray"
Write-ColoredOutput "" "White"
Write-ColoredOutput "🌐 Enterprise Manager:" "White"
Write-ColoredOutput "   https://localhost:5500/em" "Gray"
Write-ColoredOutput "   Usuário: sys" "Gray"
Write-ColoredOutput "   Senha: 123456" "Gray"
Write-ColoredOutput "   Container: FREEPDB1" "Gray"
Write-ColoredOutput "" "White"
Write-ColoredOutput "💡 Próximos passos:" "White"
Write-ColoredOutput "   1. cd sensor.ingest.local" "Gray"
Write-ColoredOutput "   2. python servidor.py" "Gray"
Write-ColoredOutput "   3. Testar: curl http://localhost:8000/health" "Gray"
Write-ColoredOutput "" "White"
Write-ColoredOutput "🛠️  Comandos úteis:" "White"
Write-ColoredOutput "   docker logs $ContainerName              # Ver logs" "Gray"
Write-ColoredOutput "   docker stop $ContainerName             # Parar" "Gray"
Write-ColoredOutput "   docker start $ContainerName            # Iniciar" "Gray"
Write-ColoredOutput "   docker rm -f $ContainerName            # Remover" "Gray"
Write-ColoredOutput "   docker exec -it $ContainerName bash    # Acessar container" "Gray"
Write-ColoredOutput "   docker exec -it $ContainerName sqlplus fiap/123456@FREEPDB1  # SQL*Plus" "Gray"

Write-ColoredOutput "" "White"
Write-Host "Pressione qualquer tecla para continuar..." -NoNewline
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown") 
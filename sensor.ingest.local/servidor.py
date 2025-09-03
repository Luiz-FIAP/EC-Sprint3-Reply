from flask import Flask, request, jsonify
import oracledb
from datetime import datetime
from config import DB_CONFIG, SERVER_CONFIG, SENSOR_CONFIG, QUERY_CONFIG

app = Flask(__name__)

# *** Configurações do Banco de Dados Oracle ***
DB_USER = DB_CONFIG["user"]
DB_PASSWORD = DB_CONFIG["password"]
DB_DSN = DB_CONFIG["dsn"]
TABLE_NAME = DB_CONFIG["table_name"]

def conectar_db():
    """Conecta ao banco de dados Oracle."""
    try:
        conn = oracledb.connect(user=DB_USER, password=DB_PASSWORD, dsn=DB_DSN)
        cursor = conn.cursor()
        print("Conectado ao Oracle DB com sucesso!")
        return conn, cursor
    except oracledb.Error as error:
        print(f"Erro ao conectar ao Oracle: {error}")
        return None, None

def criar_tabela_se_nao_existir():
    f"""Cria a tabela '{TABLE_NAME}' no Oracle se ela não existir e insere dados iniciais."""
    conn, cursor = conectar_db()
    if conn and cursor:
        try:
            cursor.execute(f"""
                CREATE TABLE {TABLE_NAME} (
                    
            """)
            
            print(f"Tabela '{TABLE_NAME}' criada com sucesso!")
            print("📥 Inserindo dados iniciais...")
            
            
            # Verifica quantos registros foram inseridos
            cursor.execute(f"SELECT COUNT(*) FROM {TABLE_NAME}")
            total_records = cursor.fetchone()[0]
            print(f"✅ {total_records} registros inseridos com sucesso!")
            
            # Mostra distribuição por tipo de sensor
            cursor.execute(f"""
                SELECT sensor_type, COUNT(*) as records_per_type 
                FROM {TABLE_NAME} 
                GROUP BY sensor_type 
                ORDER BY sensor_type
            """)
            for tipo, contagem in cursor.fetchall():
                print(f"📊 {tipo}: {contagem} registros")
            
            conn.commit()
            print("✅ Tabela e dados iniciais criados com sucesso!")
            
        except oracledb.Error as error:
            if error.args[0].code == 955:  # ORA-00955: nome já existe
                print(f"A tabela '{TABLE_NAME}' já existe.")
            else:
                print(f"Erro ao criar a tabela: {error}")
                if conn:
                    conn.rollback()
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
    else:
        print("Não foi possível conectar ao DB para criar a tabela.")

criar_tabela_se_nao_existir()

def inserir_dados_sensor(sensor_type, sensor_value, timestamp_read=None):
    """Insere uma nova leitura de sensor na tabela."""
    print(f"🗄️ [BANCO] Iniciando inserção: {sensor_type} = {sensor_value}")
    
    conn, cursor = conectar_db()
    if conn and cursor:
        try:
            if timestamp_read is None:
                print(f"⏰ Usando timestamp atual (timestamp_read=None)")
                # Se não fornecido, usa timestamp atual
                cursor.execute(f"""
                    INSERT INTO {TABLE_NAME} (sensor_type, sensor_value)
                    VALUES (:sensor_type, :sensor_value)
                """, sensor_type=sensor_type, sensor_value=sensor_value)
                print(f"✅ Dados inseridos: {sensor_type} = {sensor_value} @ now")
            else:
                # ⭐ CORREÇÃO: Melhor tratamento de timestamp
                try:
                    print(f"⏰ Processando timestamp: {timestamp_read}")
                    # Converte timestamp de milissegundos para datetime
                    if timestamp_read > 1000000000000:  # Se for em milissegundos
                        timestamp_dt = datetime.fromtimestamp(timestamp_read/1000)
                        print(f"DEBUG: Convertendo {timestamp_read} ms para {timestamp_dt}")
                    else:  # Se for em segundos
                        timestamp_dt = datetime.fromtimestamp(timestamp_read)
                        print(f"DEBUG: Usando {timestamp_read} segundos como {timestamp_dt}")
                    
                    # ⭐ VALIDAÇÃO: Verificar se a data é razoável (entre 2024 e 2030)
                    min_date = datetime(2024, 1, 1)
                    max_date = datetime(2030, 12, 31)
                    
                    if not (min_date <= timestamp_dt <= max_date):
                        print(f"⚠️ AVISO: Timestamp fora do intervalo esperado: {timestamp_dt}")
                        print(f"⚠️ Usando timestamp atual em vez de {timestamp_dt}")
                        timestamp_dt = datetime.now()
                    
                    print(f"💾 Inserindo no banco com timestamp: {timestamp_dt}")
                    cursor.execute(f"""
                        INSERT INTO {TABLE_NAME} (sensor_type, sensor_value, timestamp_read)
                        VALUES (:sensor_type, :sensor_value, :timestamp_read)
                    """, sensor_type=sensor_type, sensor_value=sensor_value, 
                        timestamp_read=timestamp_dt)
                    
                    print(f"✅ Dados inseridos: {sensor_type} = {sensor_value} @ {timestamp_dt}")
                    
                except (ValueError, OSError) as e:
                    print(f"❌ Erro ao processar timestamp {timestamp_read}: {e}")
                    print("🔄 Usando timestamp atual como fallback")
                    cursor.execute(f"""
                        INSERT INTO {TABLE_NAME} (sensor_type, sensor_value)
                        VALUES (:sensor_type, :sensor_value)
                    """, sensor_type=sensor_type, sensor_value=sensor_value)
                    print(f"✅ Dados inseridos com timestamp atual: {sensor_type} = {sensor_value}")
            
            print(f"💾 Executando commit...")
            conn.commit()
            print(f"🎉 Commit realizado com sucesso!")
            return True
        except oracledb.Error as error:
            print(f"❌ Erro Oracle ao inserir dados: {error}")
            if conn:
                print(f"🔄 Executando rollback...")
                conn.rollback()
            return False
        except Exception as e:
            print(f"❌ Erro geral ao inserir dados: {e}")
            if conn:
                print(f"🔄 Executando rollback...")
                conn.rollback()
            return False
        finally:
            if cursor:
                cursor.close()
                print(f"🔒 Cursor fechado")
            if conn:
                conn.close()
                print(f"🔒 Conexão fechada")
    else:
        print(f"❌ Falha na conexão com o banco de dados")
        return False

def validate_sensor_data(sensor_type, sensor_value, timestamp=None):
    """
    Valida dados do sensor ANTES de tentar inserir no banco.
    Retorna (is_valid, error_message, http_code)
    """
    # 1. Validar timestamp se fornecido
    if timestamp is not None:
        try:
            # Verifica se o timestamp é um número válido
            timestamp_float = float(timestamp)
            # Converte de milissegundos para segundos se necessário
            if timestamp_float > 1e12:  # Se for em milissegundos
                timestamp_float = timestamp_float / 1000
            # Verifica se o timestamp está em um intervalo razoável (entre 2024 e 2030)
            timestamp_dt = datetime.fromtimestamp(timestamp_float)
            min_date = datetime(2024, 1, 1)
            max_date = datetime(2030, 12, 31)
            if not (min_date <= timestamp_dt <= max_date):
                return False, f"Timestamp fora do intervalo válido (2024-2030). Recebido: {timestamp_dt}", 400
        except (ValueError, TypeError, OSError) as e:
            return False, f"Timestamp inválido: {str(e)}", 400

    # 2. Validar se o tipo de sensor é suportado
    valid_types = SENSOR_CONFIG["valid_types"]
    if sensor_type not in valid_types:
        return False, f"Tipo de sensor inválido. Tipos suportados: {valid_types}", 400
    
    # 3. Validar faixa de valores para cada tipo de sensor
    value_ranges = SENSOR_CONFIG["max_value_range"]
    if sensor_type in value_ranges:
        min_val, max_val = value_ranges[sensor_type]
        if not (min_val <= sensor_value <= max_val):
            return False, f"Valor fora da faixa válida para {sensor_type}. Esperado: {min_val} - {max_val}, recebido: {sensor_value}", 400
    
    # 4. Validações específicas por tipo de sensor
    if sensor_type == "vibration":
        # Vibração deve ser 0 ou 1 (digital)
        if sensor_value not in [0, 1]:
            return False, f"Sensor de vibração deve ser 0 (sem vibração) ou 1 (com vibração). Recebido: {sensor_value}", 400
    
    elif sensor_type == "luminosity":
        # Luminosidade deve ser inteiro (ADC)
        if not isinstance(sensor_value, (int, float)) or sensor_value < 0:
            return False, f"Sensor de luminosidade deve ser valor não-negativo. Recebido: {sensor_value}", 400
        # Verificar se é valor ADC válido (0-4095 para ESP32)
        if sensor_value > 4095:
            return False, f"Valor de luminosidade muito alto (máximo 4095 para ESP32). Recebido: {sensor_value}", 400
    
    elif sensor_type in ["temperature", "humidity"]:
        # Verificar precisão (não mais que 2 casas decimais)
        if round(sensor_value, SENSOR_CONFIG["data_precision"]) != sensor_value:
            return False, f"Sensor {sensor_type} deve ter no máximo {SENSOR_CONFIG['data_precision']} casas decimais", 400
    
    return True, None, None

@app.route('/data', methods=['POST'])
def receive_data():
    """Endpoint para receber dados dos sensores via POST."""
    # ⭐ LOG: Requisição recebida
    client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.environ.get('REMOTE_ADDR', 'unknown'))
    print(f"\n📡 [ENTRADA] Requisição recebida de {client_ip} às {datetime.now().strftime('%H:%M:%S')}")
    
    try:
        # 1. Validar Content-Type
        print(f"🔍 Content-Type: {request.content_type}")
        if not request.is_json:
            print("❌ Content-Type inválido")
            return jsonify({
                "error": "Content-Type deve ser application/json",
                "details": "Envie dados no formato JSON com header 'Content-Type: application/json'"
            }), 400
        
        # 2. Validar se JSON é válido
        try:
            data = request.get_json()
            print(f"📥 Dados recebidos: {data}")
        except Exception as e:
            print(f"❌ Erro ao parsear JSON: {e}")
            return jsonify({
                "error": "JSON inválido",
                "details": f"Erro ao interpretar JSON: {str(e)}"
            }), 400
        
        if not data:
            print("❌ JSON vazio")
            return jsonify({
                "error": "JSON vazio",
                "details": "Envie um objeto JSON com sensor_type e sensor_value"
            }), 400
        
        # 3. Extrair dados
        timestamp_param = data.get('timestamp')  # timestamp em milissegundos
        sensor_type = data.get('sensor_type')    # tipo do sensor
        sensor_value = data.get('sensor_value')  # valor lido
        
        print(f"🔧 Processando: {sensor_type} = {sensor_value} @ {timestamp_param}")

        # 4. Validar campos obrigatórios
        if None in [sensor_type, sensor_value]:
            missing_fields = []
            if sensor_type is None:
                missing_fields.append("sensor_type")
            if sensor_value is None:
                missing_fields.append("sensor_value")
            
            print(f"❌ Campos ausentes: {missing_fields}")
            return jsonify({
                "error": "Campos obrigatórios ausentes",
                "missing_fields": missing_fields,
                "example": {
                    "sensor_type": "temperature",
                    "sensor_value": 25.5,
                    "timestamp": int(datetime.now().timestamp() * 1000)
                }
            }), 400

        # 5. Validar tipos de dados
        if not isinstance(sensor_type, str):
            print(f"❌ sensor_type deve ser string, recebido: {type(sensor_type)}")
            return jsonify({
                "error": "sensor_type deve ser string",
                "received_type": str(type(sensor_type).__name__)
            }), 400

        try:
            sensor_value = float(sensor_value)
            timestamp = float(timestamp_param) if timestamp_param else None
            print(f"✅ Tipos convertidos: {sensor_type} = {sensor_value} @ {timestamp}")
        except (ValueError, TypeError):
            print(f"❌ Erro na conversão de tipos")
            return jsonify({
                "error": "Tipos de dados inválidos",
                "details": "sensor_value deve ser numérico, timestamp deve ser numérico (opcional)"
            }), 400

        # 6. ⭐ VALIDAÇÃO PRINCIPAL DO SENSOR (ANTES DO BANCO!)
        print(f"🔍 Validando dados do sensor...")
        is_valid, error_msg, error_code = validate_sensor_data(sensor_type, sensor_value, timestamp)
        if not is_valid:
            print(f"❌ Validação falhou: {error_msg}")
            return jsonify({
                "error": "Dados do sensor inválidos",
                "details": error_msg,
                "received_data": {
                    "sensor_type": sensor_type,
                    "sensor_value": sensor_value,
                    "timestamp": timestamp
                }
            }), error_code

        # 7. Se chegou aqui, dados são válidos - pode inserir no banco
        print(f"✅ Dados válidos: {sensor_type} = {sensor_value}")
        print(f"💾 Tentando salvar no banco...")

        if inserir_dados_sensor(sensor_type, sensor_value, timestamp):
            print(f"🎉 SUCESSO! Dados salvos no banco")
            return jsonify({
                "status": "success",
                "message": "Dados recebidos e armazenados com sucesso",
                "data": {
                    "sensor_type": sensor_type,
                    "sensor_value": sensor_value,
                    "timestamp": timestamp,
                    "datetime": datetime.fromtimestamp(timestamp/1000).isoformat() if timestamp else None
                }
            }), 200
        else:
            print(f"❌ FALHA ao salvar no banco")
            return jsonify({
                "status": "partial_success", 
                "message": "Dados válidos recebidos mas falha ao armazenar no banco de dados",
                "details": "Verifique logs do servidor e conexão com Oracle"
            }), 202

    except Exception as e:
        print(f"❌ Erro inesperado no endpoint /data: {e}")
        import traceback
        print(f"🔍 Stack trace: {traceback.format_exc()}")
        return jsonify({
            "error": "Erro interno do servidor",
            "details": "Verifique logs do servidor para mais informações"
        }), 500

@app.route('/sensors', methods=['GET'])
def get_sensor_data():
    """Lista as leituras dos sensores com filtros opcionais."""
    conn, cursor = conectar_db()
    if not (conn and cursor):
        return jsonify({"error": "Erro de conexão com banco"}), 500

    try:
        sensor_type = request.args.get('sensor_type')
        limit = request.args.get('limit', str(QUERY_CONFIG["default_limit"]))
        
        query = f"""
            SELECT id, timestamp_read, sensor_type, sensor_value, created_at
            FROM {TABLE_NAME} 
        """
        params = {}
        
        if sensor_type:
            query += "WHERE sensor_type = :sensor_type "
            params['sensor_type'] = sensor_type
            
        query += "ORDER BY timestamp_read DESC FETCH FIRST :limit ROWS ONLY"
        params['limit'] = int(limit)

        cursor.execute(query, params)
        
        columns = [desc[0].lower() for desc in cursor.description]
        results = []
        
        for row in cursor:
            record = dict(zip(columns, row))
            # Converte timestamps para string ISO
            for key in ['timestamp_read', 'created_at']:
                if record[key]:
                    record[key] = record[key].isoformat()
            results.append(record)

        return jsonify({
            "status": "success",
            "count": len(results),
            "data": results
        })

    except Exception as e:
        print(f"❌ Erro ao consultar dados: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@app.route('/health', methods=['GET'])
def health_check():
    """Endpoint de saúde do serviço."""
    conn, cursor = conectar_db()
    db_status = "ok" if (conn and cursor) else "error"
    
    if conn and cursor:
        cursor.close()
        conn.close()
    
    return jsonify({
        "status": "ok",
        "database": db_status,
        "timestamp": datetime.now().isoformat()
    })

if __name__ == '__main__':
    print("🚀 Iniciando servidor de ingestão de dados IoT...")
    app.run(host=SERVER_CONFIG["host"], port=SERVER_CONFIG["port"], debug=SERVER_CONFIG["debug"]) 
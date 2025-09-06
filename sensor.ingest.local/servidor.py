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

def executar_initial_data_se_necessario():
    """
    Versão compatível com Windows usando arquivo temporário.
    """
    import subprocess
    import os
    import tempfile
    
    try:
        # Verificar se tabelas existem
        conn, cursor = conectar_db()
        if conn and cursor:
            try:
                cursor.execute("""
                    SELECT COUNT(*) FROM user_tables 
                    WHERE table_name IN ('DEVICES', 'SENSORS', 'SENSOR_TYPES', 'SENSOR_READINGS', 'ALERTS', 'DEVICE_CONFIGS')
                """)
                tabelas_existentes = cursor.fetchone()[0]
                print(f"📊 Tabelas encontradas: {tabelas_existentes}/6")
                
                if tabelas_existentes >= 6:
                    print("✅ Todas as tabelas já existem")
                    return True
            finally:
                cursor.close()
                conn.close()
        
        print("🔄 Executando initial_data.sql...")
        
        # Verificar se arquivo existe
        sql_file = os.path.abspath('initial_data.sql')
        if not os.path.exists(sql_file):
            print(f"❌ Arquivo não encontrado: {sql_file}")
            return False
            
        print(f"📁 Arquivo SQL: {sql_file}")
        
        # Usar sqlplus com arquivo temporário (compatível com Windows)
        from config import DB_CONFIG
        
        user = DB_CONFIG['user']
        password = DB_CONFIG['password']
        dsn = DB_CONFIG['dsn']
        
        print(f"🔗 Conectando como: {user}@{dsn}")
        
        # Criar arquivo temporário com comandos SQL
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sql', delete=False) as temp_file:
            temp_file.write(f"@{sql_file.replace(chr(92), '/')}\n")  # Usar barras Unix
            temp_file.write("EXIT;\n")
            temp_sql_file = temp_file.name
        
        try:
            # Executar sqlplus com arquivo temporário
            cmd = f'sqlplus -s {user}/{password}@{dsn} @{temp_sql_file}'
            
            print(f"⚡ Comando: {cmd}")
            
            # Executar com timeout
            result = subprocess.run(
                cmd, 
                shell=True, 
                capture_output=True, 
                text=True,
                timeout=60  # 60 segundos timeout
            )
            
            print(f"📋 Return code: {result.returncode}")
            
            # Mostrar saída (limitada para não poluir)
            stdout_lines = result.stdout.split('\n')[:20]  # Primeiras 20 linhas
            print(f"📋 STDOUT (primeiras linhas):\n" + '\n'.join(stdout_lines))
            
            if result.stderr:
                stderr_lines = result.stderr.split('\n')[:10]  # Primeiras 10 linhas de erro
                print(f"📋 STDERR:\n" + '\n'.join(stderr_lines))
            
            # Verificar se foi bem-sucedido
            success_indicators = [
                "Commit concluído",
                "Table created",
                "Index created", 
                "View created",
                "Trigger created"
            ]
            
            success_found = any(indicator in result.stdout for indicator in success_indicators)
            
            if result.returncode == 0 and success_found:
                print("🎉 Script executado com sucesso!")
                
                # Verificar se as tabelas foram realmente criadas
                conn, cursor = conectar_db()
                if conn and cursor:
                    try:
                        cursor.execute("""
                            SELECT COUNT(*) FROM user_tables 
                            WHERE table_name IN ('DEVICES', 'SENSORS', 'SENSOR_TYPES', 'SENSOR_READINGS', 'ALERTS', 'DEVICE_CONFIGS')
                        """)
                        tabelas_finais = cursor.fetchone()[0]
                        print(f"📊 Tabelas criadas: {tabelas_finais}/6")
                    finally:
                        cursor.close()
                        conn.close()
                
                return True
            else:
                print(f"❌ Falha na execução")
                print(f"📋 Saída completa:\n{result.stdout}")
                if result.stderr:
                    print(f"📋 Erros:\n{result.stderr}")
                return False
                
        finally:
            # Limpar arquivo temporário
            try:
                os.unlink(temp_sql_file)
            except:
                pass
            
    except subprocess.TimeoutExpired:
        print("❌ Timeout na execução do sqlplus")
        return False
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
        import traceback
        print(f"🔍 Traceback:\n{traceback.format_exc()}")
        return False

def inserir_dados_sensor(sensor_id, sensor_value, timestamp_read=None, quality="good", raw_value=None):
    """
    Insere dados na tabela SENSOR_READINGS.
    """
    conn, cursor = conectar_db()
    if conn and cursor:
        try:
            if timestamp_read is None:
                # Usar timestamp atual
                cursor.execute(f"""
                    INSERT INTO {TABLE_NAME} (sensor_id, sensor_value, quality, raw_value)
                    VALUES (:sensor_id, :sensor_value, :quality, :raw_value)
                """, sensor_id=sensor_id, sensor_value=sensor_value, quality=quality, raw_value=raw_value)
            else:
                # Processar timestamp fornecido
                try:
                    if timestamp_read > 1000000000000:  # milissegundos
                        timestamp_dt = datetime.fromtimestamp(timestamp_read/1000)
                    else:  # segundos
                        timestamp_dt = datetime.fromtimestamp(timestamp_read)
                    
                    # Validação de data
                    min_date = datetime(2024, 1, 1)
                    max_date = datetime(2030, 12, 31)
                    
                    if not (min_date <= timestamp_dt <= max_date):
                        print(f"⚠️ Timestamp fora do intervalo: {timestamp_dt}")
                        timestamp_dt = datetime.now()
                    
                    cursor.execute(f"""
                        INSERT INTO {TABLE_NAME} (sensor_id, sensor_value, timestamp, quality, raw_value)
                        VALUES (:sensor_id, :sensor_value, :timestamp, :quality, :raw_value)
                    """, sensor_id=sensor_id, sensor_value=sensor_value, 
                        timestamp=timestamp_dt, quality=quality, raw_value=raw_value)
                        
                except (ValueError, OSError) as e:
                    print(f"❌ Erro ao processar timestamp: {e}")
                    # Fallback para timestamp atual
                    cursor.execute(f"""
                        INSERT INTO {TABLE_NAME} (sensor_id, sensor_value, quality, raw_value)
                        VALUES (:sensor_id, :sensor_value, :quality, :raw_value)
                    """, sensor_id=sensor_id, sensor_value=sensor_value, quality=quality, raw_value=raw_value)
            
            conn.commit()
            print(f"✅ Dados inseridos com sucesso: {sensor_id} = {sensor_value} (Q: {quality})")
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
            if conn:
                conn.close()
    else:
        print("❌ Falha na conexão com o banco de dados")
        return False

def validate_sensor_data(sensor_id, sensor_value, timestamp=None, sensor_type=None):
    """
    Valida dados do sensor.
    """
    # 1. Validar se sensor_id existe na tabela SENSORS
    conn, cursor = conectar_db()
    if conn and cursor:
        try:
            cursor.execute("""
                SELECT s.sensor_type, st.min_value, st.max_value, st.precision_digits
                FROM sensors s
                JOIN sensor_types st ON s.sensor_type = st.type_id
                WHERE s.sensor_id = :sensor_id
            """, sensor_id=sensor_id)
            
            result = cursor.fetchone()
            if not result:
                return False, f"Sensor ID '{sensor_id}' não encontrado na base de dados", 400
                
            db_sensor_type, min_val, max_val, precision = result
            
            # 2. Validar tipo de sensor se fornecido
            if sensor_type and sensor_type != db_sensor_type:
                return False, f"Tipo de sensor incorreto. Esperado: {db_sensor_type}, recebido: {sensor_type}", 400
            
            # 3. Validar faixa de valores
            if min_val is not None and max_val is not None:
                if not (min_val <= sensor_value <= max_val):
                    return False, f"Valor fora da faixa válida. Esperado: {min_val}-{max_val}, recebido: {sensor_value}", 400
            
            # 4. Validar timestamp se fornecido
            if timestamp is not None:
                try:
                    if timestamp > 1e12:
                        timestamp = timestamp / 1000
                    timestamp_dt = datetime.fromtimestamp(timestamp)
                    min_date = datetime(2024, 1, 1)
                    max_date = datetime(2030, 12, 31)
                    if not (min_date <= timestamp_dt <= max_date):
                        return False, f"Timestamp fora do intervalo válido (2024-2030)", 400
                except (ValueError, OSError):
                    return False, "Timestamp inválido", 400
            
            return True, None, None
            
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
    else:
        return False, "Erro de conexão com banco de dados", 500

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
        sensor_id = data.get('sensor_id')
        device_id = data.get('device_id')
        sensor_type = data.get('sensor_type')
        sensor_value = data.get('sensor_value')
        timestamp_param = data.get('timestamp')
        quality = data.get('quality', 'good')
        raw_value = data.get('raw_value')
        
        # 4. Validar campos obrigatórios
        if None in [sensor_id, sensor_value]:
            missing_fields = []
            if sensor_id is None:
                missing_fields.append("sensor_id")
            if sensor_value is None:
                missing_fields.append("sensor_value")
            
            return jsonify({
                "error": "Campos obrigatórios ausentes",
                "missing_fields": missing_fields,
                "example": {
                    "sensor_id": "ESP32_001_TEMP",
                    "device_id": "ESP32_001",
                    "sensor_type": "temperature",
                    "sensor_value": 25.5,
                    "timestamp": int(datetime.now().timestamp() * 1000),
                    "quality": "good"
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

        # 6. Validação principal
        print(f"🔍 Validando dados do sensor...")
        is_valid, error_msg, error_code = validate_sensor_data(
            sensor_id, sensor_value, timestamp_param, sensor_type
        )
        if not is_valid:
            print(f"❌ Validação falhou: {error_msg}")
            return jsonify({
                "error": "Dados do sensor inválidos",
                "details": error_msg,
                "received_data": {
                    "sensor_id": sensor_id,
                    "device_id": device_id,
                    "sensor_type": sensor_type,
                    "sensor_value": sensor_value,
                    "timestamp": timestamp,
                    "quality": quality
                }
            }), error_code

        # 7. Inserir dados
        # Log da qualidade recebida
        print(f"✅ Dados válidos: {sensor_id} = {sensor_value} (Q: {quality})")
        print(f"💾 Tentando salvar no banco...")

        if inserir_dados_sensor(sensor_id, sensor_value, timestamp_param, quality, raw_value):
            print(f"🎉 SUCESSO! Dados salvos no banco")
            return jsonify({
                "status": "success",
                "message": "Dados recebidos e armazenados com sucesso",
                "data": {
                    "sensor_id": sensor_id,
                    "device_id": device_id,
                    "sensor_type": sensor_type,
                    "sensor_value": sensor_value,
                    "quality": quality,
                    "raw_value": raw_value
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
        sensor_id = request.args.get('sensor_id')
        device_id = request.args.get('device_id')
        limit = request.args.get('limit', str(QUERY_CONFIG["default_limit"]))
        
        query = """
            SELECT sr.reading_id, sr.sensor_id, sr.timestamp, sr.sensor_value, 
                   sr.quality, s.sensor_name, s.sensor_type, d.device_name
            FROM sensor_readings sr
            JOIN sensors s ON sr.sensor_id = s.sensor_id
            JOIN devices d ON s.device_id = d.device_id
        """
        params = {}
        
        conditions = []
        if sensor_id:
            conditions.append("sr.sensor_id = :sensor_id")
            params['sensor_id'] = sensor_id
        if device_id:
            conditions.append("d.device_id = :device_id")
            params['device_id'] = device_id
            
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
            
        query += " ORDER BY sr.timestamp DESC FETCH FIRST :limit ROWS ONLY"
        params['limit'] = int(limit)

        cursor.execute(query, params)
        
        columns = [desc[0].lower() for desc in cursor.description]
        results = []
        
        for row in cursor:
            record = dict(zip(columns, row))
            # Converter timestamps
            if record.get('timestamp'):
                record['timestamp'] = record['timestamp'].isoformat()
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
    
    # Verificar e criar tabelas se necessário
    print("🔍 Verificando estrutura do banco de dados...")
    if executar_initial_data_se_necessario():
        print("✅ Banco de dados pronto!")
    else:
        print("❌ Problemas na configuração do banco. Verifique os logs.")
        exit(1)
    
    # Iniciar servidor
    app.run(host=SERVER_CONFIG["host"], port=SERVER_CONFIG["port"], debug=SERVER_CONFIG["debug"]) 
import oracledb

def test_connection():
    try:
        # Configurações do banco
        DB_USER = "system"
        DB_PASSWORD = "system"
        DB_DSN = "localhost/1521/xe"
        
        print("Tentando conectar ao Oracle...")
        conn = oracledb.connect(user=DB_USER, password=DB_PASSWORD, dsn=DB_DSN)
        cursor = conn.cursor()
        
        # Testa uma query simples
        cursor.execute("SELECT 1 FROM DUAL")
        result = cursor.fetchone()
        
        print("✅ Conexão bem sucedida!")
        print(f"Resultado do teste: {result}")
        
        cursor.close()
        conn.close()
        
    except oracledb.Error as error:
        print(f"❌ Erro ao conectar ao Oracle: {error}")
        print("\nPossíveis soluções:")
        print("1. Verifique se o Oracle está rodando")
        print("2. Verifique se as credenciais estão corretas")
        print("3. Verifique se o serviço XE está ativo")
        print("4. Verifique se a porta 1521 está liberada")

if __name__ == "__main__":
    test_connection() 
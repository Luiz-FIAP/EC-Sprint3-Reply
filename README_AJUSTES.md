# README de Ajustes e Melhorias

Este documento lista as principais correções, melhorias e configurações realizadas no projeto até o momento.

---

## 1. Configuração do Banco de Dados Oracle
- Ajustado o nome da tabela no Oracle e no código para garantir correspondência (`sensor_readings` ou `SENSOR_READINGS`).
- Corrigido o dicionário `DB_CONFIG` no `config.py` para usar a chave correta (`"table_name"`).
- Garantido que o usuário do banco de dados seja o mesmo utilizado para criar e acessar a tabela.
- **Confirmado que as datas registradas no banco Oracle agora estão corretas e atuais.**

## 2. Backend Flask
- Corrigido o DSN de conexão para o formato correto (`localhost:1521/xe` ou conforme o ambiente).
- Ajustado o código para buscar o nome da tabela com a chave correta do `config.py`.
- Corrigido endpoint `/sensors` para funcionar na porta correta (8000).

## 3. Dashboard com Streamlit
- Criado o arquivo `data/dashboard.py` para exibir os dados dos sensores em tempo real.
- Corrigido o endereço da API para buscar dados na porta correta (`http://localhost:8000/sensors?limit=100`).
- Ajustada a conversão de datas no pandas para evitar erros de parsing (`errors="coerce"`).

## 4. Código do Dispositivo (main.cpp)
- Garantido que o timestamp enviado para o backend seja em milissegundos (`data.timestamp * 1000`).
- Corrigido o tipo do timestamp enviado para o backend, usando `uint64_t` para evitar perda de precisão.
- Adicionado print de depuração para comparar o valor enviado no JSON e o valor do CSV/debug.
- Sincronização NTP revisada para garantir datas corretas.

## 5. Integração e Fluxo
- Testes realizados para garantir que os dados enviados pelo ESP32 são recebidos, validados e armazenados corretamente no Oracle.
- Dashboard Streamlit exibe os dados em tempo real, com gráficos interativos.
- **Confirmado que as datas no banco Oracle estão corretas e atualizadas após o ajuste do timestamp.**

---

## Como rodar o projeto

1. **Inicie o servidor Flask:**
   ```bash
   python sensor.ingest.local/servidor.py
   ```
2. **Inicie o dashboard Streamlit:**
   ```bash
   streamlit run data/dashboard.py
   ```
3. **Envie dados pelo simulador ou dispositivo.**
4. **Acesse o dashboard em:** [http://localhost:8501](http://localhost:8501)

---
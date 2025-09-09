# ML - Clusterização com Silhueta

Este módulo implementa uma pipeline de ML não supervisionado (clusterização) para identificar grupos de severidade como "bom", "alerta" e "crítico" a partir de leituras de sensores. O número de clusters é escolhido via método da Silhueta, com fallback para o índice de Calinski-Harabasz quando a qualidade (silhueta) for baixa.

## Estrutura

- `ml/generate_data.py`: gera um CSV sintético com leituras de sensores (alinhado ao ESP32)
- `ml/cluster_model.py`: treina KMeans, escolhe k por Silhueta (fallback CH), produz gráficos e relatório
- `ml/evaluate_model.py`: avalia o agrupamento com métricas externas e matriz de confusão
- `ml/predict.py`: roda inferência em um novo CSV usando artefatos salvos
- `ml/stream_serial_predict.py`: lê da Serial (PlatformIO) e prediz severidade em tempo real
- `ml/simulate_live.py`: simula “tempo real” a partir de um CSV para o dashboard
- `ml/live_dashboard.py`: dashboard Streamlit para acompanhar predições em tempo real
- `ml/requirements.txt`: dependências Python
- `ml/data/`: dados de entrada/gerados (`sensors.csv`)
- `ml/outputs/`: saídas do modelo (CSVs, figuras PNG, HTML interativo)
- `ml/reports/`: relatório HTML agregando resultados
- `ml/artifacts/`: artefatos do modelo (scaler, KMeans, metadados)

## Colunas do dataset (alinhadas ao ESP32)
- `timestamp`
- `temperatura_c`
- `umidade_pct`
- `vibracao_digital` (0/1)
- `luminosidade_analogica` (0–4095)
- `label_true` (apenas em dados sintéticos para avaliação)

## Como executar (com ambiente virtual)

```bash
cd Reply_Sprint_3/EC-Sprint3-Reply/ml
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# 1) Gerar dados (colunas alinhadas)
python generate_data.py --n-samples 3000

# 2) Treinar e gerar saídas (salva artefatos em ml/artifacts)
python cluster_model.py

# 3) Avaliar (usa label_true dos dados sintéticos)
python evaluate_model.py
```

## Predizer em novos dados (batch)

```bash
python predict.py --input data/sensors.csv --output outputs/predictions.csv
```

## Predição em tempo real (Serial / PlatformIO)

```bash
python stream_serial_predict.py --port /dev/ttyACM0 --baud 115200 --log outputs/serial_predictions.csv
```

## Dashboard em tempo real (navegador)

```bash
# Em outro terminal, com o venv ativado
# Testar as predições do modelo
streamlit run live_dashboard.py

# simula dados em tempo real para o live_dashboard.py
python simulate_live.py
```

## Simular “tempo real” sem Serial


```bash
# Alimenta o dashboard usando o CSV de predições (outputs/predictions.csv)
python simulate_live.py --source outputs/predictions.csv --target outputs/serial_predictions.csv --delay 0.5
```

Acesse no navegador a URL exibida (ex.: `http://localhost:8501`).

## Notas
- O mapeamento de clusters para severidades (`bom` → `alerta` → `crítico`) é feito ordenando os clusters por um escore de risco calculado a partir das features padronizadas.
- Se a melhor silhueta for menor que o limiar definido, usamos Calinski-Harabasz para escolher k.

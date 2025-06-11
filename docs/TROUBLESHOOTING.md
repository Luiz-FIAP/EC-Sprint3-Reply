# Guia de Solução de Problemas

## Erro de Compilação no PlatformIO

### Problema
Se você encontrar erros como `'SensorData' was not declared in this scope`, significa que há um problema na ordem das declarações no código C++.

### Solução
O código foi corrigido para declarar todas as estruturas e funções antes de serem usadas. Certifique-se de que:

1. **Estrutura SensorData** está declarada no início do arquivo
2. **Declarações de função** estão antes da função `setup()`
3. **Arquivo platformio.ini** está configurado corretamente

### Código Corrigido
O arquivo `src/main.cpp` agora tem a estrutura correta:
```cpp
// Estrutura declarada no início
struct SensorData {
  float temperature;
  float humidity;
  int vibration;
  int luminosity;
  unsigned long timestamp;
};

// Declarações de função
SensorData readSensors();
void printCSVData(SensorData data);
void printDebugData(SensorData data);

void setup() {
  // código do setup
}
```

### Para PlatformIO
1. Use o arquivo `platformio.ini` fornecido
2. Execute: `pio run` para compilar
3. Execute: `pio run --target upload` para carregar no ESP32

### Para Wokwi
1. Copie apenas o conteúdo de `src/main.cpp`
2. Cole no editor do Wokwi
3. Use o `diagram.json` para o circuito
4. Execute a simulação

## Dependências Python

### Problema
`ModuleNotFoundError: No module named 'matplotlib'`

### Solução
```bash
pip3 install -r requirements.txt
```

## Compatibilidade Seaborn

Se encontrar erro com `seaborn-v0_8`, substitua por:
```python
plt.style.use('default')
```

---
*Última atualização: Junho 2024* 
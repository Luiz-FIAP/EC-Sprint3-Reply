# ⚠️ INSTRUÇÕES IMPORTANTES - EVITAR ERRO DE DEBUG

## 🚫 NÃO FAÇA DEBUG NESTE PROJETO

Este é um projeto de **SIMULAÇÃO**, não um projeto para hardware físico. 

### ❌ **O QUE NÃO FAZER:**
- Não clicar em "Debug" no VS Code
- Não tentar conectar ESP32 físico
- Não usar F5 para debug
- Não configurar portas COM

### ✅ **O QUE FAZER:**

#### **1. Para SIMULAR o ESP32:**
```
1. Acesse: https://wokwi.com/projects/new/esp32
2. Copie o código de src/main.cpp
3. Copie o circuito de diagram.json  
4. Clique em ▶️ Play
```

#### **2. Para COMPILAR (se tiver PlatformIO):**
```bash
# Apenas compilar (sem debug):
pio run

# Ver saída serial (simulação):
pio device monitor
```

#### **3. Para ANALISAR DADOS:**
```bash
cd analysis
python3 data_visualization.py
```

## 🔧 **SE O ERRO PERSISTIR:**

### **No VS Code:**
1. Pressione `Ctrl+Shift+P` (ou `Cmd+Shift+P` no Mac)
2. Digite: "Debug: Stop"
3. Feche todas as abas de debug
4. Use apenas "Build" (🔨), nunca "Debug" (🐞)

### **Arquivos de Configuração:**
- ✅ `.pioinit` - Debug desabilitado
- ✅ `platformio.ini` - Sem configurações de debug
- ✅ `.vscode/settings.json` - Debug desabilitado

## 🎯 **OBJETIVO DO PROJETO:**
- ✅ Simular sensores IoT
- ✅ Gerar dados CSV
- ✅ Criar gráficos de análise
- ❌ **NÃO** fazer debug de hardware

---
*Use o Wokwi para ver o ESP32 funcionando! 🚀* 
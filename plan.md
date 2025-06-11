# Fase 1 – Análise de Requisitos

## Achados / entregáveis da fase

### 1. Requisitos funcionais explícitos
- Simular um circuito funcional com ESP32 com 3 sensores virtuais (temperatura, vibração, luminosidade).
- Programar a leitura dos sensores na plataforma de simulação (VScode, Wokwi, Platformio ou similar).
- Ajustar valores simulados para representar cenários realistas (manual, simulação interna ou dados públicos adaptados).
- Registrar dados lidos (via Monitor Serial, exportação para CSV ou simulação textual).
- Gerar ao menos um gráfico simples (linha, barra ou dispersão) com os dados coletados/simulados.
- Documentar o processo no GitHub público, incluindo prints do circuito, código, dados e análise.
- Incluir README claro e estruturado explicando o funcionamento do sistema.

### 2. Requisitos implícitos
- O código deve ser comentado e de fácil compreensão.
- A escolha dos sensores deve ser justificada.
- O fluxo de coleta, leitura e análise de dados deve ser demonstrado de ponta a ponta.
- O sistema deve ser facilmente reprodutível por terceiros (instruções claras no README).
- O circuito e a simulação devem ser suficientemente realistas para apoiar análises futuras (ex: IA, automação).

### 3. Requisitos não-funcionais
- Performance: Simulação deve ser responsiva e permitir coleta de dados em tempo real ou próximo disso.
- Manutenção: Código e documentação devem facilitar evolução futura (ex: inclusão de novos sensores).
- Testabilidade: O sistema deve permitir validação dos dados simulados e do fluxo de leitura.
- Reprodutibilidade: Todo o processo deve ser facilmente replicável por outros usuários.
- Usabilidade: Interface da simulação e documentação devem ser acessíveis a iniciantes.
- Segurança: Não aplicável diretamente, mas boas práticas de código e repositório devem ser seguidas.
- Escalabilidade: Não é foco imediato, mas a arquitetura deve permitir expansão para múltiplos sensores.

### 4. Perguntas de esclarecimento
- Há preferência por algum sensor específico (ex: temperatura, luminosidade, vibração, qualidade do ar)?
- Existe limitação de plataforma de simulação (VScode, Wokwi, Platformio, etc.)?
- O gráfico deve ser gerado obrigatoriamente em Python/R ou pode ser feito em outra linguagem/ferramenta?
- Alguma restrição quanto ao formato de exportação dos dados (CSV, JSON, etc.)?
- O foco é apenas a simulação ou haverá integração futura com sistemas reais/cloud?
- Alguma diretriz sobre o idioma da documentação/código (inglês ou português)? Documentação deve ser em Português.

## Confidence: 80 %

## Próximos passos
- Aguardar respostas às perguntas de esclarecimento para atingir confiança ≥ 90 % e avançar para a Fase 2 – Contexto do Sistema. 
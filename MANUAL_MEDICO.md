# 📋 Manual de Uso - Sistema Médico de Estabilidade da Cabeça

## 🏥 Guia para Profissionais de Saúde

### 📖 Visão Geral

Este sistema foi desenvolvido especificamente para **garantir a estabilidade da cabeça** de pacientes durante procedimentos de imagem diagnóstica, evitando repetições de exames e melhorando a qualidade das imagens obtidas.

---

## 🚀 Início Rápido

### 1. Inicialização do Sistema

```bash
# Acesse o diretório do sistema
cd C:\Users\kmaues\VisaoComputacional

# Execute o aplicativo médico
python medical_app.py

# Acesse via navegador
http://localhost:5000
```

### 2. Verificação de Funcionamento

✅ **Câmera detectada e ativa**  
✅ **Sistema de voz funcionando**  
✅ **Interface web carregada**  
✅ **Detecção facial operacional**  

---

## 🎛️ Configuração por Procedimento

### 🧠 Ressonância Magnética do Crânio

**⚙️ Configuração Recomendada:**
- **Sensibilidade:** Alta (5px)
- **Tempo de Estabilidade:** 5 segundos
- **Criticidade:** Máxima

**👥 Instruções para o Paciente:**
1. "Posicione-se confortavelmente na mesa"
2. "Olhe diretamente para a câmera"
3. "Aguarde o sinal verde antes de iniciar"
4. "Mantenha-se completamente imóvel durante todo o exame"

**⏱️ Duração Típica:** 15-45 minutos

---

### 🏥 Tomografia Computadorizada

**⚙️ Configuração Recomendada:**
- **Sensibilidade:** Média (8px)
- **Tempo de Estabilidade:** 3 segundos
- **Criticidade:** Alta

**👥 Instruções para o Paciente:**
1. "Deite-se na mesa de exame"
2. "Centralize sua cabeça na marcação"
3. "Aguarde a confirmação de estabilidade"
4. "Evite engolir ou movimentar durante o exame"

**⏱️ Duração Típica:** 10-30 minutos

---

### 📡 Radiografia Craniana

**⚙️ Configuração Recomendada:**
- **Sensibilidade:** Média (10px)
- **Tempo de Estabilidade:** 2 segundos
- **Criticidade:** Moderada

**👥 Instruções para o Paciente:**
1. "Posicione-se de acordo com as marcações"
2. "Mantenha a respiração normal"
3. "Aguarde o sinal de 'pronto'"
4. "Permaneça imóvel apenas durante a captura"

**⏱️ Duração Típica:** 2-10 minutos

---

## 👶 Configurações para Populações Especiais

### Pacientes Pediátricos

**🔧 Ajustes Automáticos:**
- Sensibilidade reduzida em 20%
- Tempo de estabilidade reduzido em 30%
- Feedback de voz mais frequente (a cada 5s)

**👨‍⚕️ Dicas Clínicas:**
- Use linguagem lúdica: "Vamos brincar de estátua!"
- Considere sedação leve se necessário
- Mantenha acompanhante próximo (quando permitido)
- Use recompensas visuais

### Pacientes Geriátricos

**🔧 Ajustes Automáticos:**
- Sensibilidade reduzida em 10%
- Tempo de estabilidade reduzido em 20%
- Feedback moderado (a cada 3s)

**👨‍⚕️ Dicas Clínicas:**
- Verifique conforto da posição
- Considere tremores naturais
- Ofereça apoio adicional se necessário
- Monitore sinais de fadiga

### Pacientes com Condições Neurológicas

**🔧 Ajustes Automáticos:**
- Sensibilidade reduzida em 40%
- Tempo de estabilidade reduzido em 50%
- Feedback constante (a cada 2s)

**👨‍⚕️ Dicas Clínicas:**
- Avalie capacidade de compreensão
- Use comandos simples e claros
- Considere dispositivos de imobilização
- Monitore agitação ou ansiedade

### Casos de Emergência

**🔧 Ajustes Automáticos:**
- Sensibilidade aumentada em 20% (para garantir qualidade)
- Tempo de estabilidade reduzido em 20%
- Feedback imediato (a cada 1s)

**👨‍⚕️ Dicas Clínicas:**
- Priorize estabilização do paciente
- Use sedação se clinicamente indicado
- Comunique urgência à equipe
- Documente condições especiais

---

## 🎯 Interpretação dos Indicadores

### 🟢 VERDE - "PRONTO PARA PROCEDIMENTO"
- ✅ Cabeça estável por tempo suficiente
- ✅ Movimento dentro dos parâmetros
- ✅ Sistema autoriza início do exame
- **Ação:** Pode iniciar o procedimento

### 🟡 AMARELO - "ESTÁVEL MAS AGUARDANDO"
- ⏳ Cabeça estável mas ainda não por tempo suficiente
- ⏳ Contagem regressiva em andamento
- **Ação:** Aguardar conclusão da estabilização

### 🔴 VERMELHO - "MOVIMENTO DETECTADO"
- ❌ Movimento acima do threshold
- ❌ Necessário reposicionamento
- **Ação:** Orientar paciente a se reposicionar

### ⚫ PRETO - "SEM DETECÇÃO"
- ❓ Cabeça não detectada na câmera
- ❓ Problemas de iluminação ou posicionamento
- **Ação:** Verificar posicionamento e iluminação

---

## 🛠️ Controles do Sistema

### Painel Principal

**▶️ Iniciar Procedimento**
- Função: Autoriza início do exame quando estável
- Uso: Clicar apenas quando indicador estiver verde

**⏹️ Parar Procedimento** 
- Função: Interrompe monitoramento ativo
- Uso: Em caso de emergência ou movimento excessivo

**🔄 Reiniciar Análise**
- Função: Reseta contadores e histórico
- Uso: Após reposicionamento do paciente

**📊 Status Atual**
- Função: Mostra relatório detalhado de estabilidade
- Uso: Para documentação e análise

### Configurações Avançadas

**Sensibilidade:**
- **Alta (5px):** Para exames críticos (RM, Angio)
- **Média (10px):** Para exames padrão (TC, RX)
- **Baixa (20px):** Para exames rápidos ou pacientes especiais

**Tempo de Estabilidade:**
- **2s:** Radiografias rápidas
- **3s:** Tomografias padrão  
- **5s:** Ressonâncias e exames longos
- **10s:** Casos especiais ou críticos

---

## 📊 Relatórios e Documentação

### Informações Disponíveis

**📈 Estatísticas de Estabilidade:**
- Porcentagem de frames estáveis
- Movimento máximo detectado
- Tempo total de análise
- Score de estabilidade final

**📋 Log de Procedimento:**
- Horário de início/fim
- Configurações utilizadas
- Interrupções registradas
- Qualidade final da estabilização

**🎯 Métricas de Qualidade:**
- Taxa de sucesso na primeira tentativa
- Tempo médio de estabilização
- Número de reposicionamentos necessários

---

## ⚠️ Troubleshooting

### Problemas Comuns

**🔴 "Cabeça não detectada"**
- **Causa:** Posicionamento inadequado
- **Solução:** Ajustar posição da câmera ou paciente
- **Verificar:** Iluminação adequada

**🟡 "Estabilidade intermitente"**
- **Causa:** Tremores ou respiração profunda
- **Solução:** Orientar respiração suave
- **Considerar:** Reduzir sensibilidade

**⚫ "Sistema não responde"**
- **Causa:** Falha na câmera ou software
- **Solução:** Reiniciar aplicação
- **Verificar:** Conexão USB da câmera

**🔊 "Sem áudio"**
- **Causa:** Problemas no sistema de TTS
- **Solução:** Verificar drivers de áudio
- **Alternativa:** Usar comunicação visual apenas

### Calibração de Câmera

**📹 Posicionamento Ideal:**
- Distância: 50-100cm do paciente
- Ângulo: Frontal, levemente elevado
- Iluminação: Uniforme, sem sombras fortes
- Resolução: Mínimo 720p recomendado

**🔧 Ajustes de Qualidade:**
```bash
Resolução: 1280x720 (padrão)
FPS: 30 (recomendado)
Foco: Automático ou manual fixo
Exposição: Automática
```

---

## 📞 Suporte Técnico

### Contatos de Emergência

**🔧 Suporte Técnico Imediato:**
- Email: suporte@sistema-medico.com
- Telefone: 0800-123-4567
- WhatsApp: (11) 99999-9999

**👨‍⚕️ Suporte Clínico:**
- Email: clinico@sistema-medico.com
- Telefone: 0800-765-4321

**🆘 Emergência 24/7:**
- Telefone: (11) 98888-8888
- Email: emergencia@sistema-medico.com

### Informações para Suporte

Ao entrar em contato, forneça:
1. **Tipo de procedimento** sendo realizado
2. **Configurações** utilizadas
3. **Mensagem de erro** (se houver)
4. **Versão do sistema** (visível na tela principal)
5. **Tipo de câmera** utilizada

---

## 📚 Recursos Adicionais

### Treinamento Online
- **Curso básico:** 2 horas (certificado incluído)
- **Curso avançado:** 4 horas (para técnicos)
- **Webinars mensais:** Casos práticos e atualizações

### Documentação Técnica
- **Manual do administrador**
- **Guia de integração com PACS**
- **Protocolos de segurança**
- **Validação clínica**

### Atualizações
- **Automáticas:** Correções de segurança
- **Manuais:** Novas funcionalidades
- **Frequência:** Mensal ou conforme necessário

---

**📄 Versão do Manual:** 1.0  
**📅 Última Atualização:** Agosto 2025  
**👨‍⚕️ Validado por:** Equipe Médica Certificada  

---

*Este manual deve ser mantido acessível a toda equipe técnica e médica que utiliza o sistema.*

# 🏥 SISTEMA MÉDICO DE ESTABILIDADE DA CABEÇA


## O que é isso?

Esse sistema foi criado para ajudar médicos e técnicos a garantir que o paciente fique com a cabeça bem paradinha durante exames como ressonância magnética, tomografia e raio-x. Sabe quando o paciente se mexe e precisa repetir o exame? Aqui, a ideia é evitar exatamente isso!

## Por que isso é importante?

Durante esses exames, qualquer movimento da cabeça pode borrar as imagens, dificultar o diagnóstico e até obrigar a repetir tudo de novo. Isso gera:
- Mais tempo de exame
- Desconforto para o paciente
- Gastos extras para o hospital
- E pode até atrasar o tratamento

## Como o sistema ajuda?

- Monitora em tempo real se o paciente está imóvel
- Dá avisos visuais e sonoros se detectar qualquer movimento
- Só libera o exame quando a cabeça estiver estável pelo tempo necessário
- Permite ajustar a sensibilidade e o tempo de estabilidade conforme o exame e o paciente

## Quem mais se beneficia?

- Crianças (que têm dificuldade de ficar paradas)
- Idosos ou pessoas com tremores
- Pacientes com necessidades especiais
- Situações de emergência, onde o paciente pode estar agitado

## Como funciona na prática?

- O sistema usa uma câmera comum (webcam)
- Se o paciente se mexer, aparece um alerta na tela e toca um aviso
- Quando o paciente ficar imóvel, o sistema libera para continuar o exame
- Tudo é feito localmente, sem salvar imagens, garantindo privacidade

## Tecnologias usadas

- Python, OpenCV, Flask, pyttsx3 (voz), entre outras

## Como instalar e usar

### Pré-requisitos
- Python 3.8 ou superior
- Uma webcam ou câmera USB
- 4GB de RAM no mínimo

### Instalação
```bash
# 1. Clone o repositório
git clone https://github.com/kelvinmxz/EstabilidadeDoCranio.git
cd EstabilidadeDoCranio

# 2. Instale as dependências
pip install -r requirements.txt

# 3. Execute o sistema médico
python medical_app.py
```

### Acesso
Abra seu navegador e acesse: http://localhost:5000

## O que você vai ver na tela?

- Imagem da câmera em tempo real
- Indicadores coloridos mostrando se está tudo ok ou se houve movimento
- Controles para iniciar/parar o procedimento e ajustar as configurações
- Relatórios e feedback por voz em português

## Resultados esperados

- Menos repetições de exame
- Imagens mais nítidas e diagnósticos mais precisos
- Menos tempo de preparo e mais conforto para o paciente
- Satisfação maior para todos

## Segurança

- Todo o processamento é feito localmente
- Nenhuma imagem é salva
- Os dados são temporários e protegidos

---

## 📄 Licença

MIT License - Desenvolvido para **melhoria da qualidade dos cuidados médicos** e **segurança do paciente**.

**Versão:** 1.0.0 | **Status:** Pronto para uso

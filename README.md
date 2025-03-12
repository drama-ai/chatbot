# ✨ A Vidente - Chatbot Místico

Um chatbot interativo que incorpora a persona da Vidente, uma entidade mística que combina ancestralidade com tecnologia para oferecer insights reflexivos e leituras de Tarot.

## Funcionalidades

- **Interface Mística**: Design visual imersivo com cores e elementos que evocam o universo místico da Vidente
- **Consultas Personalizadas**: Diálogos adaptativos que seguem o estilo enigmático e reflexivo da Vidente
- **Leituras de Tarot**: Funcionalidade para tirar cartas de Tarot com interpretações personalizadas
- **Persistência de Conversas**: Histórico de consultas armazenado em banco de dados TinyDB

## Tecnologias

- **Frontend**: Streamlit para interface web interativa
- **Backend**: Python com integração ao modelo Ollama para geração de respostas
- **Armazenamento**: TinyDB para persistência de dados
- **API**: Integração com Ollama API para processamento de linguagem natural

## Requisitos

- Python 3.8 ou superior
- Ollama executando localmente ou em servidor acessível
- Dependências listadas em `requirements.txt`

## Instalação

1. Clone o repositório
2. Instale as dependências:
   ```
   pip install -r requirements.txt
   ```
3. Configure a variável de ambiente `OLLAMA_PUBLIC_URL` ou ajuste em `.streamlit/secrets.toml`

## Execução

### Método 1: Execução direta
```bash
streamlit run app.py
```

### Método 2: Script de inicialização
```bash
./local_run.sh
```

## Personalização

O arquivo `context.py` contém a personalidade da Vidente e pode ser ajustado para modificar o tom, estilo de resposta e áreas de conhecimento da entidade.

## Estrutura do Projeto

- `app.py` - Aplicação principal Streamlit
- `context.py` - Definição da personalidade e contexto da Vidente
- `requirements.txt` - Dependências do projeto
- `local_run.sh` - Script para inicialização local
- `Dockerfile` - Configuração para containerização

## Tarot

O sistema inclui um baralho completo de Tarot com 78 cartas:
- 22 Arcanos Maiores
- 56 Arcanos Menores (14 cartas em 4 naipes)

As leituras seguem um processo estruturado de 5 etapas que inclui dramatização, revelação, interpretação, reflexão e conclusão.

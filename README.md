# 🔮 Chapéu de Bruxa

Bot de estudos e secretária pessoal para Discord, construído para suportar uma rotina séria de preparação para concursos públicos. Combina técnicas de aprendizado ativo (SM-2, Active Recall, Pomodoro) com automação via IA.

---

## Funcionalidades

- **Sessões de estudo** — registro com controle de tempo, energia, humor e qualidade, com encerramento automático após 4h
- **Flashcards com SM-2** — criação assistida por IA e revisão espaçada com algoritmo de repetição
- **Quiz estilo Cebraspe** — questões Certo/Errado carregadas via CSV com histórico de desempenho por disciplina
- **Dashboard diário** — resumo de sessões, flashcards e quiz do dia
- **Estatísticas** — visão geral e por disciplina com filtro de período

---

## Stack

- Python 3.11+
- [discord.py](https://discordpy.readthedocs.io/) v2.x
- [aiosqlite](https://aiosqlite.omnilib.dev/)
- [Anthropic Python SDK](https://github.com/anthropic/anthropic-sdk-python)
- [APScheduler](https://apscheduler.readthedocs.io/)
- [python-dotenv](https://pypi.org/project/python-dotenv/)

---

## Estrutura

```
chapeu-de-bruxa/
├── cogs/               # Funcionalidades do bot (um arquivo por módulo)
├── database/           # Conexão, inicialização e queries do banco
├── config/             # Configurações e carregamento de variáveis de ambiente
├── data/               # Arquivos estáticos (ex: quiz.csv)
├── .env.example        # Template de variáveis de ambiente
├── requirements.txt
└── main.py
```

---

## Instalação

**1. Clone o repositório**
```bash
git clone https://github.com/pedrovazs/chapeu-de-bruxa.git
cd chapeu-de-bruxa
```

**2. Crie e ative um ambiente virtual**
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

**3. Instale as dependências**
```bash
pip install -r requirements.txt
```

**4. Configure as variáveis de ambiente**
```bash
cp .env.example .env
```
Edite o `.env` com suas credenciais:
```
DISCORD_TOKEN=seu_token_aqui
ANTHROPIC_API_KEY=sua_chave_aqui
GUILD_ID=id_do_servidor_de_testes
```

**5. Inicie o bot**
```bash
python main.py
```

---

## Desenvolvimento

O projeto segue uma arquitetura em cogs. Cada funcionalidade é independente e vive no seu próprio arquivo dentro de `cogs/`. O banco de dados é gerenciado exclusivamente pelo módulo `database/database.py` — os cogs nunca fazem queries diretas.

A sincronização de slash commands durante desenvolvimento é feita por guild para propagação instantânea. Em produção, os comandos são registrados globalmente.

---

## Roadmap

### Camada 1 — MVP (em andamento)
- [x] Estrutura base e configuração
- [ ] Banco de dados e tabelas
- [ ] `/sessao` — iniciar, encerrar, histórico
- [ ] `/flashcard` — criar com IA, revisar com SM-2
- [ ] `/quiz` — Cebraspe C/E com histórico
- [ ] `/hoje` e `/stats`

### Camada 2 — Secretária de Rotina
- Mapa de lacunas, rastreador de legislação, modo Feynman, banco de erros, daily briefing, weekly review

### Camada 3 — Agente Autônomo
- Planejamento adaptativo, integração com calendário, briefings proativos

---

## Licença

MIT — veja [LICENSE](LICENSE) para detalhes.

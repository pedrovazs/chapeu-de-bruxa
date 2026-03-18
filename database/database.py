# database/database.py
import aiosqlite
import os

# Caminho absoluto para o arquivo do banco — funciona independente
# de onde o script é chamado no sistema de arquivos
DB_PATH = os.path.join(os.path.dirname(__file__), "chapeu.db")

async def init_db():
    """
    Inicializa o banco de dados criando todas as tabelas do MVP
    se elas ainda não existirem. Deve ser chamada uma vez na
    inicialização do bot, antes de qualquer comando ser executado.
    """
    async with aiosqlite.connect(DB_PATH) as db:

        # ── SESSÕES ──────────────────────────────────────────────
        # Registra cada sessão de estudo do usuário. O campo
        # encerrada_automaticamente distingue timeouts (4h) de
        # encerramentos manuais para fins estatísticos.
        await db.execute("""
            CREATE TABLE IF NOT EXISTS sessoes (
                id                        INTEGER PRIMARY KEY AUTOINCREMENT,
                usuario_id                TEXT    NOT NULL,
                subtopico                 TEXT    NOT NULL,
                iniciada_em               TEXT    NOT NULL,
                encerrada_em              TEXT,
                duracao_efetiva_min       INTEGER,
                energia_inicial           INTEGER,
                humor_final               INTEGER,
                qualidade                 INTEGER,
                anotacoes                 TEXT,
                encerrada_automaticamente INTEGER NOT NULL DEFAULT 0
            )
        """)

        # ── FLASHCARDS ───────────────────────────────────────────
        # Armazena os cartões e os dados do algoritmo SM-2.
        # ease_factor começa em 2.5 (padrão SM-2).
        # interval é o número de dias até a próxima revisão.
        # repeticoes conta quantas vezes o card foi revisado com sucesso.
        # proxima_revisao é a data (ISO 8601) em que o card deve aparecer.
        await db.execute("""
            CREATE TABLE IF NOT EXISTS flashcards (
                id               INTEGER PRIMARY KEY AUTOINCREMENT,
                usuario_id       TEXT    NOT NULL,
                frente           TEXT    NOT NULL,
                verso            TEXT    NOT NULL,
                topico           TEXT    NOT NULL,
                ease_factor      REAL    NOT NULL DEFAULT 2.5,
                intervalo        INTEGER NOT NULL DEFAULT 1,
                repeticoes       INTEGER NOT NULL DEFAULT 0,
                proxima_revisao  TEXT    NOT NULL,
                criado_em        TEXT    NOT NULL
            )
        """)

        # ── HISTÓRICO DE QUIZ ────────────────────────────────────
        # Cada linha é uma resposta a uma questão. Guardar disciplina
        # aqui (em vez de só no CSV) permite gerar estatísticas por
        # disciplina diretamente via SQL, sem precisar cruzar arquivos.
        await db.execute("""
            CREATE TABLE IF NOT EXISTS quiz_historico (
                id               INTEGER PRIMARY KEY AUTOINCREMENT,
                usuario_id       TEXT    NOT NULL,
                disciplina       TEXT    NOT NULL,
                enunciado        TEXT    NOT NULL,
                resposta_correta TEXT    NOT NULL,
                resposta_usuario TEXT    NOT NULL,
                acertou          INTEGER NOT NULL,
                respondido_em    TEXT    NOT NULL
            )
        """)

        await db.commit()
        print("✅ Banco de dados inicializado.")

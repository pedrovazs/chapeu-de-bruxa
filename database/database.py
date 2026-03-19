# database/database.py
#
# Camada de acesso a dados do bot. Este é o ÚNICO arquivo que conhece
# a existência do SQLite. Nenhum cog faz queries diretamente — tudo
# passa pelas funções aqui definidas.

import aiosqlite
import os
from datetime import datetime

# Caminho absoluto para o .db, relativo a este arquivo.
# Usar __file__ garante que funciona independente de onde o script é chamado.
DB_PATH = os.path.join(os.path.dirname(__file__), "chapeu.db")


# ── INICIALIZAÇÃO ─────────────────────────────────────────────────────────────

async def init_db():
    """
    Cria todas as tabelas do MVP se ainda não existirem.
    Deve ser chamada uma única vez durante a inicialização do bot,
    antes de qualquer cog ser carregado.
    """
    async with aiosqlite.connect(DB_PATH) as db:

        # SESSÕES
        # encerrada_automaticamente distingue timeouts (4h) de encerramentos
        # manuais — útil para filtrar estatísticas mais tarde.
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

        # FLASHCARDS
        # ease_factor, intervalo e repeticoes são o estado persistido do SM-2.
        # ultima_revisao permite contar quantos cards foram revisados hoje (para /hoje).
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
                ultima_revisao   TEXT,
                criado_em        TEXT    NOT NULL
            )
        """)

        # HISTÓRICO DE QUIZ
        # Guardar disciplina diretamente na tabela (e não só no CSV) permite
        # gerar estatísticas por disciplina com queries SQL simples,
        # sem precisar cruzar arquivos em memória.
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


# ── SESSÕES ───────────────────────────────────────────────────────────────────

async def inserir_sessao(usuario_id: str, subtopico: str, energia_inicial: int, iniciada_em: str) -> int:
    """Insere uma nova sessão aberta. Retorna o ID gerado pelo banco."""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "INSERT INTO sessoes (usuario_id, subtopico, energia_inicial, iniciada_em) VALUES (?, ?, ?, ?)",
            (usuario_id, subtopico, energia_inicial, iniciada_em)
        )
        await db.commit()
        # lastrowid é o ID autoincrement da linha recém-inserida
        return cursor.lastrowid


async def buscar_sessao_aberta(usuario_id: str) -> dict | None:
    """Retorna a sessão em aberto do usuário, ou None se não houver."""
    async with aiosqlite.connect(DB_PATH) as db:
        # row_factory = aiosqlite.Row permite acessar colunas por nome (row["coluna"])
        # em vez de por índice (row[0]), tornando o código muito mais legível.
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM sessoes WHERE usuario_id = ? AND encerrada_em IS NULL ORDER BY iniciada_em DESC LIMIT 1",
            (usuario_id,)
        ) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None


async def encerrar_sessao(sessao_id: int, encerrada_em: str, duracao_efetiva_min: int,
                           humor_final: int | None, qualidade: int | None,
                           anotacoes: str | None, automatica: bool = False):
    """Preenche os campos de encerramento de uma sessão existente."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            UPDATE sessoes SET
                encerrada_em              = ?,
                duracao_efetiva_min       = ?,
                humor_final               = ?,
                qualidade                 = ?,
                anotacoes                 = ?,
                encerrada_automaticamente = ?
            WHERE id = ?
        """, (encerrada_em, duracao_efetiva_min, humor_final, qualidade,
              anotacoes, int(automatica), sessao_id))
        await db.commit()


async def buscar_sessoes_expiradas(horas: int = 4) -> list:
    """
    Retorna todas as sessões abertas há mais de `horas` horas.
    Usada pelo job de timeout do APScheduler.
    """
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("""
            SELECT * FROM sessoes
            WHERE encerrada_em IS NULL
            AND iniciada_em <= datetime('now', ?)
        """, (f'-{horas} hours',)) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]


async def buscar_historico_sessoes(usuario_id: str, limite: int = 5) -> list:
    """Retorna as últimas `limite` sessões encerradas do usuário."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("""
            SELECT * FROM sessoes
            WHERE usuario_id = ? AND encerrada_em IS NOT NULL
            ORDER BY iniciada_em DESC LIMIT ?
        """, (usuario_id, limite)) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]


# ── FLASHCARDS ────────────────────────────────────────────────────────────────

async def inserir_flashcard(usuario_id: str, frente: str, verso: str, topico: str,
                             proxima_revisao: str, criado_em: str):
    """Insere um novo flashcard com os valores iniciais do SM-2 (padrão: 2.5/1/0)."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO flashcards (usuario_id, frente, verso, topico, proxima_revisao, criado_em)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (usuario_id, frente, verso, topico, proxima_revisao, criado_em))
        await db.commit()


async def buscar_flashcard_para_revisao(usuario_id: str) -> dict | None:
    """
    Retorna o próximo card pendente de revisão (proxima_revisao <= hoje),
    ordenado pelo mais atrasado primeiro.
    """
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        hoje = datetime.utcnow().date().isoformat()
        async with db.execute("""
            SELECT * FROM flashcards
            WHERE usuario_id = ? AND proxima_revisao <= ?
            ORDER BY proxima_revisao ASC LIMIT 1
        """, (usuario_id, hoje)) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None


async def atualizar_flashcard_sm2(flashcard_id: int, ease_factor: float, intervalo: int,
                                   repeticoes: int, proxima_revisao: str, ultima_revisao: str):
    """Persiste o novo estado SM-2 após uma revisão."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            UPDATE flashcards SET
                ease_factor     = ?,
                intervalo       = ?,
                repeticoes      = ?,
                proxima_revisao = ?,
                ultima_revisao  = ?
            WHERE id = ?
        """, (ease_factor, intervalo, repeticoes, proxima_revisao, ultima_revisao, flashcard_id))
        await db.commit()


async def contar_flashcards_pendentes(usuario_id: str) -> int:
    """Conta o total de flashcards com revisão pendente para hoje."""
    async with aiosqlite.connect(DB_PATH) as db:
        hoje = datetime.utcnow().date().isoformat()
        async with db.execute(
            "SELECT COUNT(*) FROM flashcards WHERE usuario_id = ? AND proxima_revisao <= ?",
            (usuario_id, hoje)
        ) as cursor:
            row = await cursor.fetchone()
            return row[0]


# ── QUIZ ──────────────────────────────────────────────────────────────────────

async def inserir_quiz_historico(usuario_id: str, disciplina: str, enunciado: str,
                                  resposta_correta: str, resposta_usuario: str,
                                  acertou: bool, respondido_em: str):
    """Registra uma resposta de quiz no histórico."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO quiz_historico
            (usuario_id, disciplina, enunciado, resposta_correta, resposta_usuario, acertou, respondido_em)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (usuario_id, disciplina, enunciado, resposta_correta, resposta_usuario, int(acertou), respondido_em))
        await db.commit()


async def buscar_stats_quiz(usuario_id: str, periodo_dias: int = 0) -> list:
    """
    Retorna estatísticas agregadas por disciplina.
    periodo_dias=0 significa total histórico (sem filtro de data).
    """
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        if periodo_dias > 0:
            async with db.execute("""
                SELECT disciplina, COUNT(*) as total, SUM(acertou) as acertos
                FROM quiz_historico
                WHERE usuario_id = ? AND respondido_em >= datetime('now', ?)
                GROUP BY disciplina ORDER BY disciplina
            """, (usuario_id, f'-{periodo_dias} days')) as cursor:
                rows = await cursor.fetchall()
        else:
            async with db.execute("""
                SELECT disciplina, COUNT(*) as total, SUM(acertou) as acertos
                FROM quiz_historico
                WHERE usuario_id = ?
                GROUP BY disciplina ORDER BY disciplina
            """, (usuario_id,)) as cursor:
                rows = await cursor.fetchall()
        return [dict(row) for row in rows]


# ── STATS ─────────────────────────────────────────────────────────────────────

async def buscar_stats_sessoes(usuario_id: str, periodo_dias: int = 0) -> dict:
    """Retorna métricas agregadas de sessões para o período."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        filtro = f"AND iniciada_em >= datetime('now', '-{periodo_dias} days')" if periodo_dias > 0 else ""
        async with db.execute(f"""
            SELECT
                COUNT(*)            as total_sessoes,
                COALESCE(SUM(duracao_efetiva_min), 0) as tempo_total_min,
                COALESCE(AVG(qualidade), 0)           as media_qualidade,
                COALESCE(AVG(energia_inicial), 0)     as media_energia
            FROM sessoes
            WHERE usuario_id = ? AND encerrada_em IS NOT NULL {filtro}
        """, (usuario_id,)) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else {}


async def buscar_resumo_hoje(usuario_id: str) -> dict:
    """
    Agrega as atividades do dia atual para o comando /hoje.
    Usa LIKE com o prefixo da data (formato ISO) para filtrar pelo dia.
    """
    async with aiosqlite.connect(DB_PATH) as db:
        hoje = datetime.utcnow().date().isoformat()

        # Sessões encerradas hoje
        async with db.execute("""
            SELECT COUNT(*) as sessoes, COALESCE(SUM(duracao_efetiva_min), 0) as tempo
            FROM sessoes
            WHERE usuario_id = ? AND iniciada_em LIKE ? AND encerrada_em IS NOT NULL
        """, (usuario_id, f"{hoje}%")) as cursor:
            s = await cursor.fetchone()

        # Flashcards revisados hoje (ultima_revisao preenchida hoje)
        async with db.execute("""
            SELECT COUNT(*) as revisados FROM flashcards
            WHERE usuario_id = ? AND ultima_revisao LIKE ?
        """, (usuario_id, f"{hoje}%")) as cursor:
            f = await cursor.fetchone()

        # Quiz respondido hoje
        async with db.execute("""
            SELECT COUNT(*) as total, COALESCE(SUM(acertou), 0) as acertos
            FROM quiz_historico
            WHERE usuario_id = ? AND respondido_em LIKE ?
        """, (usuario_id, f"{hoje}%")) as cursor:
            q = await cursor.fetchone()

        return {
            "sessoes":              s[0],
            "tempo_min":            s[1],
            "flashcards_revisados": f[0],
            "quiz_total":           q[0],
            "quiz_acertos":         q[1],
        }

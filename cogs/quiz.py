# cogs/quiz.py
#
# Cog responsável por /quiz jogar (questão C/E aleatória do CSV)
# e /quiz historico (desempenho por disciplina com filtro de período).

import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime
import csv
import random
import os

from database.database import inserir_quiz_historico, buscar_stats_quiz


# Caminho absoluto para o CSV, relativo a este arquivo.
# Os dois ".." sobem um nível da pasta cogs/ até a raiz do projeto,
# depois entram em data/.
CSV_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "quiz.csv")


def carregar_questoes() -> list[dict]:
    """
    Lê o arquivo CSV e retorna todas as questões como lista de dicts.
    Executado uma única vez na inicialização do cog — não relê o arquivo
    a cada comando, o que seria desnecessariamente lento.
    """
    questoes = []
    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            questoes.append(row)
    return questoes


# ── VIEW: QUESTÃO DE QUIZ ─────────────────────────────────────────────────────
#
# View com dois botões (Certo / Errado). Após a resposta, os botões são
# desabilitados e o gabarito com comentário é exibido.

class QuizView(discord.ui.View):

    def __init__(self, questao: dict, bot: commands.Bot):
        # timeout=60: se o usuário não responder em 1 minuto, a view expira
        super().__init__(timeout=60)
        self.questao = questao
        self.bot = bot

    @discord.ui.button(label="✅ Certo", style=discord.ButtonStyle.success)
    async def certo(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._processar_resposta(interaction, "C")

    @discord.ui.button(label="❌ Errado", style=discord.ButtonStyle.danger)
    async def errado(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._processar_resposta(interaction, "E")

    async def _processar_resposta(self, interaction: discord.Interaction, resposta: str):
        q = self.questao
        acertou = resposta == q["gabarito"]
        agora = datetime.utcnow().isoformat()
        usuario_id = str(interaction.user.id)

        await inserir_quiz_historico(
            usuario_id=usuario_id,
            disciplina=q["disciplina"],
            enunciado=q["enunciado"],
            resposta_correta=q["gabarito"],
            resposta_usuario=resposta,
            acertou=acertou,
            respondido_em=agora,
        )

        # Desabilita os botões para impedir múltiplas respostas à mesma questão
        for item in self.children:
            item.disabled = True

        resultado = "✅ **Correto!**" if acertou else "❌ **Errado!**"
        gabarito_str = "Certo" if q["gabarito"] == "C" else "Errado"

        # edit_message atualiza a mensagem original com o gabarito,
        # mantendo o contexto da questão visível para o usuário.
        await interaction.response.edit_message(
            content=(
                f"**{q['disciplina']}**\n\n"
                f"{q['enunciado']}\n\n"
                f"{resultado}\n"
                f"**Gabarito:** {gabarito_str}\n"
                f"📝 {q['comentario']}"
            ),
            view=self,
        )


# ── GROUP ─────────────────────────────────────────────────────────────────────

class QuizGroup(app_commands.Group, name="quiz", description="Quiz no estilo Cebraspe (Certo/Errado)"):

    def __init__(self, bot: commands.Bot):
        super().__init__()
        self.bot = bot
        # Carrega as questões em memória uma vez — acesso posterior é O(1)
        self.questoes = carregar_questoes()
        print(f"📋 {len(self.questoes)} questões de quiz carregadas.")

    @app_commands.command(name="jogar", description="Responda uma questão aleatória no estilo Cebraspe (C/E)")
    async def jogar(self, interaction: discord.Interaction):
        if not self.questoes:
            await interaction.response.send_message(
                "❌ Nenhuma questão encontrada. Verifique o arquivo data/quiz.csv.",
                ephemeral=True,
            )
            return

        # random.choice seleciona uma questão aleatória da lista em memória
        questao = random.choice(self.questoes)
        view = QuizView(questao, self.bot)

        await interaction.response.send_message(
            content=f"**{questao['disciplina']}**\n\n{questao['enunciado']}",
            view=view,
            ephemeral=True,
        )

    @app_commands.command(name="historico", description="Exibe seu desempenho no quiz por disciplina")
    @app_commands.describe(periodo="Período de análise")
    # app_commands.choices cria um dropdown no Discord com opções pré-definidas,
    # evitando que o usuário precise digitar o período manualmente.
    @app_commands.choices(periodo=[
        app_commands.Choice(name="Últimos 7 dias",  value=7),
        app_commands.Choice(name="Últimos 30 dias", value=30),
        app_commands.Choice(name="Total",           value=0),
    ])
    async def historico(self, interaction: discord.Interaction, periodo: app_commands.Choice[int] = None):
        usuario_id = str(interaction.user.id)
        periodo_dias = periodo.value if periodo else 0
        periodo_label = periodo.name if periodo else "Total"

        stats = await buscar_stats_quiz(usuario_id, periodo_dias)

        if not stats:
            await interaction.response.send_message(
                "📭 Nenhuma questão respondida no período.", ephemeral=True
            )
            return

        embed = discord.Embed(
            title=f"📊 Desempenho no Quiz — {periodo_label}",
            color=discord.Color.blue(),
        )

        total_geral = sum(s["total"] for s in stats)
        acertos_geral = sum(s["acertos"] for s in stats)
        pct_geral = round((acertos_geral / total_geral) * 100) if total_geral > 0 else 0

        embed.description = f"**Total:** {total_geral} questões | **Aproveitamento geral:** {pct_geral}%"

        for s in stats:
            pct = round((s["acertos"] / s["total"]) * 100) if s["total"] > 0 else 0
            barra = _barra_progresso(pct)
            embed.add_field(
                name=s["disciplina"],
                value=f"{barra} {pct}% ({s['acertos']}/{s['total']})",
                inline=False,
            )

        await interaction.response.send_message(embed=embed, ephemeral=True)


def _barra_progresso(pct: int, tamanho: int = 10) -> str:
    """
    Gera uma barra de progresso visual com caracteres Unicode.
    Ex: pct=70, tamanho=10 → "███████░░░"
    """
    preenchido = round(pct / 100 * tamanho)
    return "█" * preenchido + "░" * (tamanho - preenchido)


# ── COG ───────────────────────────────────────────────────────────────────────

class Quiz(commands.Cog):

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.bot.tree.add_command(QuizGroup(bot))

    def cog_unload(self):
        self.bot.tree.remove_command("quiz")


async def setup(bot: commands.Bot):
    await bot.add_cog(Quiz(bot))

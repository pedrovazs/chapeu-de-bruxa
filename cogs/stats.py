# cogs/stats.py
#
# Cog responsável por /hoje (resumo diário) e /stats (estatísticas por período).
# Diferente dos outros cogs, estes são comandos top-level (não subcomandos de um grupo),
# então usamos @app_commands.command() diretamente nos métodos do Cog.

import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime

from database.database import buscar_resumo_hoje, buscar_stats_sessoes, buscar_stats_quiz


class Stats(commands.Cog):

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # Quando @app_commands.command() é usado dentro de um commands.Cog,
    # o discord.py registra os comandos automaticamente na árvore quando
    # bot.add_cog() é chamado. Não precisamos de bot.tree.add_command() manual aqui.

    @app_commands.command(name="hoje", description="Resumo das suas atividades de estudo de hoje")
    async def hoje(self, interaction: discord.Interaction):
        # defer() porque fazemos múltiplas queries no banco.
        # Embora cada query seja rápida, o conjunto pode passar dos 3s em casos extremos.
        await interaction.response.defer(ephemeral=True)

        usuario_id = str(interaction.user.id)
        dados = await buscar_resumo_hoje(usuario_id)

        tempo_min = dados.get("tempo_min", 0)
        horas = tempo_min // 60
        minutos = tempo_min % 60
        tempo_str = f"{horas}h {minutos}min" if horas > 0 else f"{minutos}min"

        quiz_total   = dados.get("quiz_total", 0)
        quiz_acertos = dados.get("quiz_acertos", 0)
        pct_quiz = round((quiz_acertos / quiz_total) * 100) if quiz_total > 0 else 0

        hoje_str = datetime.utcnow().strftime("%d/%m/%Y")

        embed = discord.Embed(
            title=f"📅 Resumo de Hoje — {hoje_str}",
            color=discord.Color.green(),
        )

        embed.add_field(
            name="📚 Sessões",
            value=f"{dados.get('sessoes', 0)} sessão(ões)\n⏱ {tempo_str}",
            inline=True,
        )
        embed.add_field(
            name="🃏 Flashcards",
            value=f"{dados.get('flashcards_revisados', 0)} revisado(s)",
            inline=True,
        )

        quiz_value = (
            f"{quiz_total} questão(ões)\n✅ {pct_quiz}% de aproveitamento"
            if quiz_total > 0
            else "Nenhuma questão respondida"
        )
        embed.add_field(name="❓ Quiz", value=quiz_value, inline=True)

        # followup.send é usado após defer() — é a resposta tardia prometida pelo defer.
        await interaction.followup.send(embed=embed, ephemeral=True)

    @app_commands.command(name="stats", description="Estatísticas detalhadas de estudo por período")
    @app_commands.describe(periodo="Período de análise")
    @app_commands.choices(periodo=[
        app_commands.Choice(name="Últimos 7 dias",  value=7),
        app_commands.Choice(name="Últimos 30 dias", value=30),
        app_commands.Choice(name="Total",           value=0),
    ])
    async def stats(self, interaction: discord.Interaction, periodo: app_commands.Choice[int] = None):
        await interaction.response.defer(ephemeral=True)

        usuario_id   = str(interaction.user.id)
        periodo_dias = periodo.value if periodo else 0
        periodo_label = periodo.name if periodo else "Total"

        # Busca métricas de sessões e quiz em paralelo — como são awaits sequenciais,
        # não são realmente paralelas aqui; para paralelismo real usaríamos asyncio.gather().
        # Para o MVP, o desempenho sequencial é mais que suficiente.
        sessoes = await buscar_stats_sessoes(usuario_id, periodo_dias)
        quiz    = await buscar_stats_quiz(usuario_id, periodo_dias)

        tempo_min = sessoes.get("tempo_total_min", 0)
        horas   = int(tempo_min) // 60
        minutos = int(tempo_min) % 60
        tempo_str = f"{horas}h {minutos}min" if horas > 0 else f"{minutos}min"

        embed = discord.Embed(
            title=f"📊 Estatísticas — {periodo_label}",
            color=discord.Color.purple(),
        )

        # Bloco de sessões de estudo
        embed.add_field(
            name="📚 Sessões de Estudo",
            value=(
                f"Total: **{int(sessoes.get('total_sessoes', 0))}** sessões\n"
                f"Tempo total: **{tempo_str}**\n"
                f"Qualidade média: **{round(sessoes.get('media_qualidade', 0), 1)}/5**\n"
                f"Energia média: **{round(sessoes.get('media_energia', 0), 1)}/5**"
            ),
            inline=False,
        )

        # Bloco de quiz por disciplina
        if quiz:
            total_geral   = sum(s["total"] for s in quiz)
            acertos_geral = sum(s["acertos"] for s in quiz)
            pct_geral = round((acertos_geral / total_geral) * 100) if total_geral > 0 else 0

            linhas = [f"**Total:** {total_geral} questões | **Aproveitamento:** {pct_geral}%\n"]
            for s in quiz:
                pct = round((s["acertos"] / s["total"]) * 100) if s["total"] > 0 else 0
                linhas.append(f"• {s['disciplina']}: **{pct}%** ({s['acertos']}/{s['total']})")

            embed.add_field(
                name="❓ Quiz por Disciplina",
                value="\n".join(linhas),
                inline=False,
            )
        else:
            embed.add_field(
                name="❓ Quiz",
                value="Nenhuma questão respondida no período.",
                inline=False,
            )

        await interaction.followup.send(embed=embed, ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(Stats(bot))

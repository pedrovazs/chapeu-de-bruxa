# cogs/sessao.py
#
# Cog responsável pelos comandos /sessao iniciar, /sessao encerrar e
# /sessao historico, além do job de encerramento automático após 4h.

import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from database.database import (
    inserir_sessao,
    buscar_sessao_aberta,
    encerrar_sessao,
    buscar_sessoes_expiradas,
    buscar_historico_sessoes,
)


# ── MODAL: INICIAR ────────────────────────────────────────────────────────────
#
# Um Modal no Discord é um formulário popup com campos de texto.
# Para criar um, herde de discord.ui.Modal e defina os campos como
# atributos de classe usando discord.ui.TextInput.

class IniciarSessaoModal(discord.ui.Modal, title="Iniciar Sessão de Estudo"):

    subtopico = discord.ui.TextInput(
        label="Subtópico",
        placeholder="Ex: Direito Penal — Tipicidade",
        required=True,
        max_length=100,
    )

    # TextStyle.short = uma linha de texto simples (padrão)
    # TextStyle.long  = campo maior, estilo textarea
    energia = discord.ui.TextInput(
        label="Energia inicial (1 a 5)",
        placeholder="Ex: 4",
        required=True,
        max_length=1,
        style=discord.TextStyle.short,
    )

    def __init__(self, bot: commands.Bot):
        super().__init__()
        self.bot = bot

    # on_submit é chamado automaticamente quando o usuário clica em "Enviar".
    # ATENÇÃO: o `interaction` aqui é uma NOVA interação — diferente da que
    # abriu o modal. Você precisa responder a esta, não à anterior.
    async def on_submit(self, interaction: discord.Interaction):
        try:
            energia_valor = int(self.energia.value)
            if not 1 <= energia_valor <= 5:
                raise ValueError
        except ValueError:
            # ephemeral=True: só o usuário que enviou o comando vê esta mensagem
            await interaction.response.send_message(
                "❌ Energia deve ser um número entre 1 e 5.", ephemeral=True
            )
            return

        agora = datetime.utcnow().isoformat()
        usuario_id = str(interaction.user.id)

        sessao_id = await inserir_sessao(usuario_id, self.subtopico.value, energia_valor, agora)

        await interaction.response.send_message(
            f"🔮 Sessão iniciada!\n"
            f"**Subtópico:** {self.subtopico.value}\n"
            f"**Energia:** {energia_valor}/5\n"
            f"**ID:** #{sessao_id}",
            ephemeral=True,
        )

    # on_error captura exceções não tratadas dentro do on_submit.
    # Sem isso, o bot engole o erro silenciosamente e o usuário fica
    # olhando para um modal que nunca respondeu.
    async def on_error(self, interaction: discord.Interaction, error: Exception):
        await interaction.response.send_message(
            "❌ Algo deu errado. Tenta novamente.", ephemeral=True
        )
        raise error


# ── MODAL: ENCERRAR ───────────────────────────────────────────────────────────

class EncerrarSessaoModal(discord.ui.Modal, title="Encerrar Sessão de Estudo"):

    humor = discord.ui.TextInput(
        label="Humor final (1 a 5)",
        placeholder="Ex: 3",
        required=True,
        max_length=1,
    )

    qualidade = discord.ui.TextInput(
        label="Qualidade da sessão (1 a 5)",
        placeholder="Ex: 4",
        required=True,
        max_length=1,
    )

    anotacoes = discord.ui.TextInput(
        label="Anotações (opcional)",
        placeholder="Observações sobre a sessão...",
        required=False,
        max_length=500,
        style=discord.TextStyle.long,
    )

    def __init__(self, bot: commands.Bot, sessao: dict):
        super().__init__()
        self.bot = bot
        # A sessão aberta é passada pelo comando encerrar antes de abrir o modal,
        # para que on_submit possa calcular a duração e usar o ID correto.
        self.sessao = sessao

    async def on_submit(self, interaction: discord.Interaction):
        try:
            humor_valor = int(self.humor.value)
            qualidade_valor = int(self.qualidade.value)
            if not (1 <= humor_valor <= 5 and 1 <= qualidade_valor <= 5):
                raise ValueError
        except ValueError:
            await interaction.response.send_message(
                "❌ Humor e qualidade devem ser números entre 1 e 5.", ephemeral=True
            )
            return

        agora = datetime.utcnow()

        # Calcula a duração subtraindo o momento de início do momento atual.
        # datetime.fromisoformat() converte a string ISO 8601 de volta para datetime.
        iniciada_em = datetime.fromisoformat(self.sessao["iniciada_em"])
        duracao_min = int((agora - iniciada_em).total_seconds() / 60)

        await encerrar_sessao(
            sessao_id=self.sessao["id"],
            encerrada_em=agora.isoformat(),
            duracao_efetiva_min=duracao_min,
            humor_final=humor_valor,
            qualidade=qualidade_valor,
            anotacoes=self.anotacoes.value or None,
        )

        horas = duracao_min // 60
        minutos = duracao_min % 60
        duracao_str = f"{horas}h {minutos}min" if horas > 0 else f"{minutos}min"

        await interaction.response.send_message(
            f"✅ Sessão encerrada!\n"
            f"**Subtópico:** {self.sessao['subtopico']}\n"
            f"**Duração:** {duracao_str}\n"
            f"**Humor:** {humor_valor}/5 | **Qualidade:** {qualidade_valor}/5",
            ephemeral=True,
        )

    async def on_error(self, interaction: discord.Interaction, error: Exception):
        await interaction.response.send_message(
            "❌ Algo deu errado. Tenta novamente.", ephemeral=True
        )
        raise error


# ── GROUP ─────────────────────────────────────────────────────────────────────
#
# app_commands.Group representa o comando pai /sessao.
# Cada método com @app_commands.command() dentro dele vira um subcomando.

class SessaoGroup(app_commands.Group, name="sessao", description="Comandos de sessão de estudo"):

    def __init__(self, bot: commands.Bot):
        super().__init__()
        self.bot = bot

    @app_commands.command(name="iniciar", description="Inicia uma nova sessão de estudo")
    async def iniciar(self, interaction: discord.Interaction):
        usuario_id = str(interaction.user.id)

        # A verificação de sessão aberta precisa acontecer ANTES do send_modal,
        # pois uma interação só pode ter uma resposta. Se houver sessão aberta,
        # respondemos com erro. Se não houver, abrimos o modal.
        sessao_aberta = await buscar_sessao_aberta(usuario_id)

        if sessao_aberta:
            await interaction.response.send_message(
                f"⚠️ Você já tem uma sessão aberta: **{sessao_aberta['subtopico']}**\n"
                f"Use `/sessao encerrar` antes de iniciar uma nova.",
                ephemeral=True,
            )
            return

        await interaction.response.send_modal(IniciarSessaoModal(self.bot))

    @app_commands.command(name="encerrar", description="Encerra a sessão de estudo atual")
    async def encerrar(self, interaction: discord.Interaction):
        usuario_id = str(interaction.user.id)
        sessao_aberta = await buscar_sessao_aberta(usuario_id)

        if not sessao_aberta:
            await interaction.response.send_message(
                "⚠️ Você não tem nenhuma sessão aberta no momento.", ephemeral=True
            )
            return

        # Passa a sessão para o modal para que ele possa calcular a duração
        # e registrar o encerramento no ID correto.
        await interaction.response.send_modal(EncerrarSessaoModal(self.bot, sessao_aberta))

    @app_commands.command(name="historico", description="Exibe o histórico de sessões recentes")
    async def historico(self, interaction: discord.Interaction):
        usuario_id = str(interaction.user.id)
        sessoes = await buscar_historico_sessoes(usuario_id, limite=5)

        if not sessoes:
            await interaction.response.send_message(
                "📭 Nenhuma sessão encerrada encontrada.", ephemeral=True
            )
            return

        # discord.Embed é a forma de criar mensagens ricas e formatadas no Discord.
        embed = discord.Embed(title="📚 Histórico de Sessões", color=discord.Color.purple())

        for s in sessoes:
            iniciada = datetime.fromisoformat(s["iniciada_em"])
            data_str = iniciada.strftime("%d/%m %H:%M")
            duracao = s["duracao_efetiva_min"] or 0
            horas = duracao // 60
            minutos = duracao % 60
            duracao_str = f"{horas}h {minutos}min" if horas > 0 else f"{minutos}min"
            qualidade = s["qualidade"] or "—"
            auto = " *(auto)*" if s["encerrada_automaticamente"] else ""

            embed.add_field(
                name=f"📌 {s['subtopico']} — {data_str}{auto}",
                value=f"⏱ {duracao_str} | ⭐ Qualidade: {qualidade}/5",
                inline=False,
            )

        await interaction.response.send_message(embed=embed, ephemeral=True)


# ── COG ───────────────────────────────────────────────────────────────────────

class Sessao(commands.Cog):

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.bot.tree.add_command(SessaoGroup(bot))

        # AsyncIOScheduler roda dentro do mesmo event loop do discord.py,
        # o que permite que os jobs façam chamadas assíncronas normalmente.
        self.scheduler = AsyncIOScheduler()
        self.scheduler.add_job(
            self._verificar_sessoes_expiradas,
            trigger="interval",
            minutes=30,
            id="verificar_sessoes",
        )
        self.scheduler.start()
        print("🕐 Scheduler de sessões iniciado.")

    def cog_unload(self):
        # Para o scheduler e remove o grupo da árvore ao descarregar o cog.
        # Sem isso, um reload do cog duplicaria os jobs e os comandos.
        self.scheduler.shutdown(wait=False)
        self.bot.tree.remove_command("sessao")

    async def _verificar_sessoes_expiradas(self):
        """
        Job executado a cada 30 minutos que encerra automaticamente qualquer
        sessão aberta há mais de 4 horas, sem precisar de interação do usuário.
        """
        sessoes = await buscar_sessoes_expiradas(horas=4)

        for sessao in sessoes:
            agora = datetime.utcnow()
            iniciada_em = datetime.fromisoformat(sessao["iniciada_em"])
            duracao_min = int((agora - iniciada_em).total_seconds() / 60)

            await encerrar_sessao(
                sessao_id=sessao["id"],
                encerrada_em=agora.isoformat(),
                duracao_efetiva_min=duracao_min,
                humor_final=None,
                qualidade=None,
                anotacoes="Encerrada automaticamente por timeout (4h).",
                automatica=True,
            )
            print(f"⏰ Sessão #{sessao['id']} do usuário {sessao['usuario_id']} encerrada por timeout.")


async def setup(bot: commands.Bot):
    await bot.add_cog(Sessao(bot))

# cogs/sessao.py
import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime


# ── MODAL ────────────────────────────────────────────────────────────────────
#
# Um Modal no Discord é o equivalente a um formulário popup — ele abre na tela
# do usuário com campos de texto para preencher. É ideal para coletar múltiplas
# informações de uma vez sem precisar de vários comandos separados.
#
# Para criar um modal no discord.py, você herda de discord.ui.Modal e define
# os campos como atributos de classe usando discord.ui.TextInput.
# Cada TextInput vira um campo no formulário.

class IniciarSessaoModal(discord.ui.Modal, title="Iniciar Sessão de Estudo"):

    # TextInput é um campo de texto no formulário.
    # O argumento `label` é o título visível do campo.
    # `placeholder` é o texto cinza de exemplo dentro do campo.
    # `required=True` impede o envio se o campo estiver vazio.
    # `max_length` limita quantos caracteres o usuário pode digitar.
    subtopico = discord.ui.TextInput(
        label="Subtópico",
        placeholder="Ex: Direito Penal — Tipicidade",
        required=True,
        max_length=100
    )

    # `style=discord.TextStyle.short` é uma linha de texto simples.
    # Existe também `TextStyle.long` para campos maiores (tipo textarea).
    energia = discord.ui.TextInput(
        label="Energia inicial (1 a 5)",
        placeholder="Ex: 4",
        required=True,
        max_length=1,
        style=discord.TextStyle.short
    )

    # O construtor recebe o bot para que o modal possa acessar
    # o banco de dados ou outros recursos quando for submetido.
    def __init__(self, bot: commands.Bot):
        super().__init__()
        self.bot = bot

    # on_submit é o método que o discord.py chama automaticamente
    # quando o usuário preenche o formulário e clica em "Enviar".
    # O `interaction` aqui é uma NOVA interação — diferente da que
    # abriu o modal. Você precisa responder a esta, não à anterior.
    async def on_submit(self, interaction: discord.Interaction):

        # Validação da energia — o banco espera um inteiro entre 1 e 5.
        # Como o TextInput sempre retorna string, precisamos converter
        # e validar manualmente. O discord.py não faz isso por você.
        try:
            energia_valor = int(self.energia.value)
            if not 1 <= energia_valor <= 5:
                raise ValueError
        except ValueError:
            # ephemeral=True significa que a mensagem de erro só aparece
            # para o usuário que enviou o comando — ninguém mais vê.
            # É a forma correta de tratar erros de validação no Discord.
            await interaction.response.send_message(
                "❌ Energia deve ser um número entre 1 e 5.",
                ephemeral=True
            )
            return

        # datetime.utcnow().isoformat() gera uma string no formato
        # "2024-03-19T14:30:00.123456" — é o formato ISO 8601, que é
        # o padrão para armazenar datas em texto no SQLite.
        # Sempre use UTC para armazenar — converta para o fuso local
        # só na hora de exibir para o usuário.
        agora = datetime.utcnow().isoformat()

        # interaction.user.id é o ID único do usuário no Discord.
        # Armazenamos como string porque IDs do Discord são inteiros
        # muito grandes (snowflakes de 64 bits) e o SQLite lida melhor
        # com eles como TEXT do que como INTEGER.
        usuario_id = str(interaction.user.id)

        # Aqui vai a chamada para o banco de dados quando o database.py
        # tiver a função de inserção implementada. Por enquanto, o print
        # serve para verificar que o modal está funcionando corretamente.
        # TODO: await inserir_sessao(usuario_id, self.subtopico.value, energia_valor, agora)
        print(f"[DEBUG] Sessão iniciada — usuário: {usuario_id}, subtópico: {self.subtopico.value}, energia: {energia_valor}, hora: {agora}")

        # Confirmação visual para o usuário. ephemeral=True porque
        # o status de estudo de alguém não precisa poluir o canal.
        await interaction.response.send_message(
            f"🔮 Sessão iniciada!\n**Subtópico:** {self.subtopico.value}\n**Energia:** {energia_valor}/5",
            ephemeral=True
        )

    # on_error é chamado automaticamente se qualquer exceção não tratada
    # acontecer dentro do on_submit. Sem isso, o bot silenciosamente
    # engole o erro e o usuário fica olhando para um modal que não respondeu.
    async def on_error(self, interaction: discord.Interaction, error: Exception):
        await interaction.response.send_message(
            "❌ Algo deu errado. Tenta novamente.",
            ephemeral=True
        )
        raise error  # Re-lança para aparecer no terminal também


# ── GROUP ─────────────────────────────────────────────────────────────────────

class SessaoGroup(app_commands.Group, name="sessao", description="Comandos de sessão de estudo"):

    def __init__(self, bot: commands.Bot):
        super().__init__()
        self.bot = bot

    @app_commands.command(name="iniciar", description="Inicia uma nova sessão de estudo")
    async def iniciar(self, interaction: discord.Interaction):

        # interaction.response.send_modal() abre o formulário na tela
        # do usuário. É uma resposta — então só pode ser chamada UMA vez
        # por interação. Se você precisar responder de outra forma antes
        # (por exemplo, checar se já existe sessão aberta), precisa fazer
        # isso ANTES de chamar o send_modal, ou usar followup depois.
        await interaction.response.send_modal(IniciarSessaoModal(self.bot))

    @app_commands.command(name="encerrar", description="Encerra a sessão de estudo atual")
    async def encerrar(self, interaction: discord.Interaction):
        pass

    @app_commands.command(name="historico", description="Exibe o histórico de sessões")
    async def historico(self, interaction: discord.Interaction):
        pass


# ── COG ───────────────────────────────────────────────────────────────────────

class Sessao(commands.Cog):

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.bot.tree.add_command(SessaoGroup(bot))


async def setup(bot: commands.Bot):
    await bot.add_cog(Sessao(bot))

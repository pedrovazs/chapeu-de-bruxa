# cogs/sessao.py
import discord
from discord import app_commands
from discord.ext import commands


# O Group é a classe que representa o comando pai /sessao.
# Cada método decorado com @app_commands.command() dentro dela
# vira um subcomando: /sessao iniciar, /sessao encerrar, etc.
class SessaoGroup(app_commands.Group, name="sessao", description="Comandos de sessão de estudo"):

    def __init__(self, bot: commands.Bot):
        super().__init__()
        self.bot = bot

    @app_commands.command(name="iniciar", description="Inicia uma nova sessão de estudo")
    async def iniciar(self, interaction: discord.Interaction):
        pass

    @app_commands.command(name="encerrar", description="Encerra a sessão de estudo atual")
    async def encerrar(self, interaction: discord.Interaction):
        pass

    @app_commands.command(name="historico", description="Exibe o histórico de sessões")
    async def historico(self, interaction: discord.Interaction):
        pass


# O Cog é o container que o discord.py carrega via load_extension().
# Ele instancia o Group e o adiciona à árvore de comandos do bot.
class Sessao(commands.Cog):

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        # Registra o grupo de comandos na árvore do bot
        self.bot.tree.add_command(SessaoGroup(bot))


# Função obrigatória — é o ponto de entrada que o discord.py
# chama quando faz load_extension("cogs.sessao")
async def setup(bot: commands.Bot):
    await bot.add_cog(Sessao(bot))

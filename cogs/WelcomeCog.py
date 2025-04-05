import discord

from discord.ext import commands

class WelcomeCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.last_member = None
    
    @commands.Cog.listener()
    async def on_member_join(self, member):
        # Ignora bots para evitar mensagens indesejadas
        if member.bot:
            return

        # Tenta obter o canal de sistema configurado
        channel = member.guild.system_channel
        # Caso não haja um canal de sistema, busca um canal com o nome 'bem-vindo'
        if channel is None:
            channel = discord.utils.get(member.guild.text_channels, name="bem-vindo")

        if channel is not None:
            embed = discord.Embed(
                title="Bem-vindo(a)!",
                description=f"Olá {member.mention}, seja bem-vindo(a) ao servidor!",
                color=discord.Color.blue()
            )
            # Exibe o avatar do novo membro, se disponível
            if member.avatar:
                embed.set_thumbnail(url=member.avatar.url)
            await channel.send(embed=embed)

async def setup(bot):
    await bot.add_cog(WelcomeCog(bot))

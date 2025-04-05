import discord
from discord.ext import commands
from discord.ext.commands import Bot, Context, has_permissions

class ModerationCog(commands.Cog):
    def __init__(self, bot: Bot):
        self.bot = bot

    def cog_check(self, ctx: Context):
        # Permite apenas usuários com permissão de kick_members ou administrador
        return ctx.author.guild_permissions.kick_members or ctx.author.guild_permissions.administrator

    @commands.command(name="limpar")
    @has_permissions(manage_messages=True)
    async def limpar(self, ctx: Context, quantidade: int = 5):
        """Apaga uma quantidade definida de mensagens do canal."""
        deleted = await ctx.channel.purge(limit=quantidade)
        confirmation = await ctx.send(f"{len(deleted)} mensagens foram apagadas.")
        await confirmation.delete(delay=5)

    @commands.command(name="kick")
    @has_permissions(kick_members=True)
    async def kick(self, ctx: Context, membro: discord.Member, *, motivo: str = "Sem motivo especificado"):
        """Expulsa um usuário do servidor."""
        try:
            await membro.kick(reason=motivo)
            await ctx.send(f"{membro.mention} foi expulso. Motivo: {motivo}")
        except Exception as e:
            await ctx.send(f"Erro ao expulsar {membro.mention}: {e}")

    @commands.command(name="ban")
    @has_permissions(ban_members=True)
    async def ban(self, ctx: Context, membro: discord.Member, *, motivo: str = "Sem motivo especificado"):
        """Bane um usuário do servidor."""
        try:
            await membro.ban(reason=motivo)
            await ctx.send(f"{membro.mention} foi banido. Motivo: {motivo}")
        except Exception as e:
            await ctx.send(f"Erro ao banir {membro.mention}: {e}")

    @commands.command(name="unban")
    @has_permissions(ban_members=True)
    async def unban(self, ctx: Context, *, nome_usuario: str):
        """Desbane um usuário. Use o formato nome#discriminador."""
        bans = await ctx.guild.bans()
        nome, discriminador = nome_usuario.split("#")
        for ban_entry in bans:
            user = ban_entry.user
            if user.name == nome and user.discriminator == discriminador:
                await ctx.guild.unban(user)
                await ctx.send(f"{user.mention} foi desbanido.")
                return
        await ctx.send("Usuário não encontrado na lista de banidos.")

    @commands.command(name="mute")
    @has_permissions(manage_roles=True)
    async def mute(self, ctx: Context, membro: discord.Member, duracao: int, unidade: str = "m", *, motivo: str = "Sem motivo especificado"):
        """
        Muta um usuário por um determinado tempo usando timeout.
        Exemplo: !mute @usuário 10 m (mute de 10 minutos)
        Unidades disponíveis: s (segundos), m (minutos), h (horas), d (dias)
        """
        unidade = unidade.lower()
        if unidade == "s":
            delta = duracao
        elif unidade == "m":
            delta = duracao * 60
        elif unidade == "h":
            delta = duracao * 3600
        elif unidade == "d":
            delta = duracao * 86400
        else:
            await ctx.send("Unidade de tempo inválida. Use s, m, h ou d.")
            return

        try:
            until = discord.utils.utcnow() + discord.timedelta(seconds=delta)
            # Usando timeout (mute) do discord.py 2.0
            await membro.timeout(until=until, reason=motivo)
            await ctx.send(f"{membro.mention} foi mutado por {duracao}{unidade}. Motivo: {motivo}")
        except Exception as e:
            await ctx.send(f"Erro ao mutar {membro.mention}: {e}")

async def setup(bot: Bot):
    await bot.add_cog(ModerationCog(bot))

import discord
import random
import asyncio
from discord.ext import commands

class SpellCog(commands.Cog):
    """Cog que implementa feitiços de silêncio e confusão."""

    def __init__(self, bot):
        self.bot = bot
        self.confused_users = {}
        self.spell_uses = {}

        self.silence_gifs = [
            "https://media.giphy.com/media/U4DswrBJJG3aM/giphy.gif",
            "https://media.giphy.com/media/l2JehQ2GitHGdVG9y/giphy.gif",
            "https://media.giphy.com/media/3xz2BLBOt13X9AgjEA/giphy.gif",
            "https://media.giphy.com/media/5VKbvrjxpVJCM/giphy.gif",
        ]
        self.confusion_gifs = [
            "https://media.giphy.com/media/3o7aD2saalBwwftBIY/giphy.gif",
            "https://media.giphy.com/media/5xtDarv1LJFOzL56m8c/giphy.gif",
            "https://media.giphy.com/media/l378khQxt68syiWJy/giphy.gif",
        ]

    @commands.command(name="silencio")
    @commands.has_permissions(manage_roles=True)
    async def silencio(self, ctx, membro: discord.Member = None):
        """Silencia um membro por 1 minuto, removendo suas permissões de enviar mensagens e falar."""
        if not membro:
            return await ctx.send("❌ Você precisa mencionar um membro para lançar o feitiço!")

        if membro == ctx.author:
            return await ctx.send("❌ Você não pode lançar o feitiço em si mesmo!")

        if membro == self.bot.user:
            return await ctx.send("❌ HAHAHAHAHA! Tente de novo daqui 1000 anos!")

        autor_id = ctx.author.id
        limite_diario = 3

        if self.spell_uses.get(autor_id, 0) >= limite_diario:
            return await ctx.send(f"❌ Você já usou seu limite diário de {limite_diario} feitiços!")

        # Criar ou obter o cargo 'Silenciado'
        cargo_silenciado = discord.utils.get(ctx.guild.roles, name="Silenciado")
        if not cargo_silenciado:
            cargo_silenciado = await ctx.guild.create_role(name="Silenciado")

            for canal in ctx.guild.channels:
                await canal.set_permissions(cargo_silenciado, send_messages=False, speak=False)

        # Atribuir o cargo ao membro
        await membro.add_roles(cargo_silenciado, reason="Silenciado pelo feitiço de silêncio")

        self.spell_uses[autor_id] = self.spell_uses.get(autor_id, 0) + 1

        gif = random.choice(self.silence_gifs)
        embed = discord.Embed(
            title="🤫 Feitiço do Silêncio!",
            description=f"{membro.mention} foi silenciado por **1 minuto**! Fique quietinho, tá? 😉",
            color=discord.Color.dark_purple()
        )
        embed.set_image(url=gif)
        await ctx.send(embed=embed)

        await asyncio.sleep(60)

        # Remover o cargo após 1 minuto
        await membro.remove_roles(cargo_silenciado, reason="Fim do feitiço de silêncio")

        embed = discord.Embed(
            title="🔊 O feitiço foi quebrado!",
            description=f"{membro.mention} agora pode falar novamente!",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)

    @commands.command(name="confusao")
    @commands.has_permissions(manage_messages=True)
    async def confusao(self, ctx, membro: discord.Member = None):
        """Embaralha as mensagens de um membro por 2 minutos."""
        if not membro:
            return await ctx.send("❌ Você precisa mencionar um membro para lançar o feitiço!")

        if membro == ctx.author:
            return await ctx.send("❌ Você não pode lançar o feitiço em si mesmo!")

        if membro == self.bot.user:
            return await ctx.send("❌ Você não pode me deixar confusa, porque eu já sou!! Isso saiu errado..")

        autor_id = ctx.author.id
        limite_diario = 3

        if self.spell_uses.get(autor_id, 0) >= limite_diario:
            return await ctx.send(f"❌ Você já usou seu limite diário de {limite_diario} feitiços!")

        self.confused_users[membro.id] = True
        self.spell_uses[autor_id] = self.spell_uses.get(autor_id, 0) + 1

        gif = random.choice(self.confusion_gifs)
        embed = discord.Embed(
            title="😵‍💫 Feitiço da Confusão!",
            description=f"{membro.mention} está completamente confuso! Todas as suas mensagens serão embaralhadas por **1 minutos**!",
            color=discord.Color.orange()
        )
        embed.set_image(url=gif)
        await ctx.send(embed=embed)

        await asyncio.sleep(60)
        self.confused_users.pop(membro.id, None)

        embed = discord.Embed(
            title="🧠 A confusão passou!",
            description=f"{membro.mention} agora pode pensar direito novamente!",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)

    @commands.Cog.listener()
    async def on_message(self, message):
        """Intercepta as mensagens dos membros afetados pelo feitiço de confusão e embaralha o conteúdo."""
        if message.author.id in self.confused_users and not message.author.bot:
            embaralhado = ''.join(random.sample(message.content, len(message.content)))
            await message.channel.send(f"{message.author.mention} disse: {embaralhado}")
            await message.delete()

async def setup(bot):
    await bot.add_cog(SpellCog(bot))

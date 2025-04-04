import discord
import random
import asyncio

from discord.ext import commands

class SpellCog(commands.Cog):
    """Classe que gerencia os feitiços do Chapéu de Bruxa"""
    def __init__(self, bot):
        self.bot = bot
        self.silenced_users = {}  # Armazena usuários silenciados
        self.confused_users = {}  # Armazena usuários afetados pelo feitiço da confusão
        self.spell_uses = {}  # Contador de usos do feitiço
        self.silence_gifs = [  # Lista de GIFs engraçados para o feitiço de silêncio
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

    @commands.command()
    async def silencio(self, ctx, membro: discord.Member = None):
        """Lança o feitiço do silêncio em um usuário, impedindo-o de enviar mensagens por 1 minuto"""
        if not membro:
            return await ctx.send("❌ Alô? Em quem você quer jogar o feitiço, hein?")

        if membro == ctx.author:
            return await ctx.send("❌ Está maluco! Quem em sã consciência lançaria um feitiço de silêncio em si mesmo?")

        if membro == self.bot.user:
            return await ctx.send("❌ Hahahaha! Tente novamente quando estiver no nível 999")

        autor_id = ctx.author.id
        membro_id = membro.id

        # Define o limite diário de usos do feitiço
        limite_diario = 3  

        # Verifica se o autor já usou o feitiço hoje
        if autor_id in self.spell_uses and self.spell_uses[autor_id] >= limite_diario:
            return await ctx.send(f"❌ Você já usou seu limite diário de {limite_diario} feitiços!")

        # Adiciona o alvo à lista de silenciados
        self.silenced_users[membro_id] = True

        # Atualiza o contador de usos
        self.spell_uses[autor_id] = self.spell_uses.get(autor_id, 0) + 1

        # Escolhe um GIF aleatório
        gif_escolhido = random.choice(self.silence_gifs)

        embed = discord.Embed(
            title="🤫 Feitiço do Silêncio!",
            description=f"{membro.mention} foi silenciado por **1 minuto**! Fique quietinho ta? 😉",
            color=discord.Color.dark_purple()
        )
        embed.set_image(url=gif_escolhido)

        await ctx.send(embed=embed)

        # Aguarda 60 segundos e remove o efeito do feitiço
        await asyncio.sleep(60)
        self.silenced_users.pop(membro_id, None)

        embed = discord.Embed(
            title="🔊 O feitiço foi quebrado!",
            description=f"{membro.mention} agora pode falar novamente!",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)

    @commands.command()
    async def confusao(self, ctx, membro: discord.Member = None):
        """Lança o Feitiço da Confusão em um usuário, embaralhando suas mensagens por 1 minuto"""
        if not membro:
            return await ctx.send("❌ Você precisa mencionar alguém para lançar o feitiço!")

        if membro == ctx.author:
            return await ctx.send("❌ Você não pode lançar o feitiço em si mesmo!")

        if membro == self.bot.user:
            return await ctx.send("❌ Eu sou imune aos feitiços!")

        autor_id = ctx.author.id
        membro_id = membro.id
        limite_diario = 3  

        # Verifica se o autor já usou o feitiço hoje
        if self.spell_uses.get(autor_id, 0) >= limite_diario:
            return await ctx.send(f"❌ Você já usou seu limite diário de {limite_diario} feitiços!")

        # Adiciona o alvo à lista de confusão
        self.confused_users[membro_id] = True
        self.spell_uses[autor_id] = self.spell_uses.get(autor_id, 0) + 1

        gif_escolhido = random.choice(self.confusion_gifs)
        embed = discord.Embed(
            title="😵‍💫 Feitiço da Confusão!",
            description=f"{membro.mention} está completamente confuso! Todas as suas mensagens serão embaralhadas por **2 minutos**!",
            color=discord.Color.orange()
        )
        embed.set_image(url=gif_escolhido)

        await ctx.send(embed=embed)

        # Aguarda 60 segundos e remove o efeito do feitiço
        await asyncio.sleep(120)
        self.confused_users.pop(membro_id, None)

        embed = discord.Embed(
            title="😵‍💫 A confusão passou!",
            description=f"{membro.mention} agora pode pensar direito novamente!",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(SpellCog(bot))

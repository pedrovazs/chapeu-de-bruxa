import discord
import random
import asyncio
from discord.ext import commands

class SpellCog(commands.Cog):
    """Cog que implementa feitiços de silêncio e confusão."""

    def __init__(self, bot):
        self.bot = bot
        self.silenced_users = set()
        self.confused_users = set()
        self.eco_users = set()
        self.spell_uses = {}
        self.limite_diario = 3

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
        self.eco_gifs = [
            "https://media.giphy.com/media/3oEjI6SIIHBdRxXI40/giphy.gif",
            "https://media.giphy.com/media/xUPGcguWZHRC2HyBRS/giphy.gif",
        ]

    def _pode_lancar_feitico(self, autor_id):
        return self.spell_uses.get(autor_id, 0) <= self.limite_diario

    def _registrar_uso_feitico(self, autor_id):
        self.spell_uses[autor_id] = self.spell_uses.get(autor_id, 0) + 1

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        # Ignora mensagens de bots
        if message.author.bot:
            return

        # Processa comandos normalmente
        if message.content.startswith("!"):
            await self.bot.process_commands(message)
            return

        author_id = message.author.id

        # Prioridade: se o usuário estiver confuso, processa o efeito de confusão.
        if author_id in self.confused_users:
            try:
                # Embaralha o conteúdo da mensagem (apenas exemplo simples: embaralhar letras)
                scrambled = ''.join(random.sample(message.content, len(message.content)))
                await message.delete()
                await message.channel.send(f"😵‍💫 {message.author.mention} diz (confuso): {scrambled}")
            except discord.Forbidden:
                pass
            return
        
        # Se o usuário estiver no efeito de eco, envia uma cópia da mensagem como eco
        if author_id in self.eco_users:
            try:
                # Aqui, o bot simplesmente ecoa a mensagem com um prefixo "Eco:"
                await message.channel.send(f"🔊 Eco de {message.author.mention}: {message.content}")
            except discord.Forbidden:
                pass
            # Não deletamos a mensagem original para o efeito de eco
            # (Caso deseje, pode optar por deletá-la)
            return

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
        if not self._pode_lancar_feitico(autor_id):
            return await ctx.send(f"❌ Você já usou seu limite diário de {self.limite_diario} feitiços!")
        
        self._registrar_uso_feitico(autor_id)

        # Criar ou obter o cargo 'Silenciado'
        cargo = discord.utils.get(ctx.guild.roles, name="Silenciado")
        if not cargo:
            cargo = await ctx.guild.create_role(name="Silenciado")
            for canal in ctx.guild.text_channels:
                await canal.set_permissions(cargo, send_messages=False)
            for canal in ctx.guild.voice_channels:
                await canal.set_permissions(cargo, speak=False)

        # Atribuir o cargo ao membro
        await membro.add_roles(cargo, reason="Feitiço do Silêncio lançado")
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
        await membro.remove_roles(cargo, reason="Feitiço do Silêncio expirou")
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
            return await ctx.send("❌ Acho que você já está confuso por querer lançar o feitiço em si mesmo!")

        if membro == self.bot.user:
            return await ctx.send("❌ Você não pode me deixar confusa, porque eu já sou!! Isso saiu errado..")

        autor_id = ctx.author.id
        if not self._pode_lancar_feitico(autor_id):
            return await ctx.send(f"❌ Você já usou seu limite diário de {self.limite_diario} feitiços!")

        self._registrar_uso_feitico(autor_id)
        self.confused_users.add(membro.id)
        gif = random.choice(self.confusion_gifs)
        embed = discord.Embed(
            title="😵‍💫 Feitiço da Confusão!",
            description=f"{membro.mention} está completamente confuso! Suas mensagens serão embaralhadas por **2 minutos**!",
            color=discord.Color.orange()
        )
        embed.set_image(url=gif)
        await ctx.send(embed=embed)

        await asyncio.sleep(60)
        self.confused_users.discard(membro.id)
        embed = discord.Embed(
            title="🧠 A confusão se dissipou!",
            description=f"{membro.mention} recuperou a clareza mental!",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)

    @commands.command(name="eco")
    @commands.has_permissions(manage_messages=True)
    async def eco(self, ctx, membro: discord.Member = None, duracao: int = 60):
        """
        Lança o feitiço de Eco: Durante o tempo especificado (em segundos), todas as mensagens enviadas pelo usuário serão ecoadas pelo bot.
        Exemplo: !eco @usuário 90 (Eco por 90 segundos)
        """
        if not membro:
            return await ctx.send("❌ Você precisa mencionar um membro para lançar o feitiço!")
        if membro == ctx.author:
            return await ctx.send("❌ Sua cabeça já tem eco! Hahaha")
        if membro == self.bot.user:
            return await ctx.send("❌ Você ainda é fraco!")

        autor_id = ctx.author.id
        if not self._pode_lancar_feitico(autor_id):
            return await ctx.send(f"❌ Você já usou seu limite diário de {self.limite_diario} feitiços!")
        
        self._registrar_uso_feitico(autor_id)
        self.eco_users.add(membro.id)
        gif = random.choice(self.eco_gifs)
        embed = discord.Embed(
            title="🔊 Feitiço do Eco!",
            description=f"{membro.mention} agora terá suas mensagens ecoadas por **{duracao} segundos**!",
            color=discord.Color.dark_teal()
        )
        embed.set_image(url=gif)
        await ctx.send(embed=embed)

        await asyncio.sleep(duracao)
        self.eco_users.discard(membro.id)
        embed = discord.Embed(
            title="🎤 O eco cessou!",
            description=f"{membro.mention} agora fala normalmente.",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(SpellCog(bot))

import discord
import random
import asyncio

from discord.ext import commands

class SpellCog(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.silenced_users = set()  # Armazena usuários silenciados
        self.confused_users = set()  # Armazena usuários afetados pelo feitiço da confusão
        self.spell_uses = {}  # Contador de usos do feitiço
        self.limite_diario = 3

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

    def _pode_lancar_feitico(self, autor_id):
        return self.spell_uses.get(autor_id, 0) < self.limite_diario

    def _registrar_uso_feitico(self, autor_id):
        self.spell_uses[autor_id] = self.spell_uses.get(autor_id, 0) + 1

    async def _esperar_e_reverter(self, user_set, membro_id, tempo, mensagem, cor):
        await asyncio.sleep(tempo)
        user_set.discard(membro_id)
        embed = discord.Embed(
            title="🔮 O feitiço terminou!",
            description=mensagem,
            color=cor
        )
        await self.bot.get_channel(self.ultimo_canal).send(embed=embed)

    def scramble_text(self, text: str) -> str:
        """Embaralha cada palavra, mantendo a primeira e a última letra inalteradas, se possível."""
        def scramble_word(word):
            if len(word) > 3:
                middle = list(word[1:-1])
                random.shuffle(middle)
                return word[0] + ''.join(middle) + word[-1]
            return word
        words = text.split()
        return ' '.join(scramble_word(word) for word in words)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        # Ignora mensagens de bots
        if message.author.bot:
            return
        
        # Permite que comandos funcionem normalmente
        if message.content.startswith("!"):
            await self.bot.process_commands(message)
            return

        author_id = message.author.id

        # Se o usuário está silenciado, apaga a mensagem e não a exibe
        if author_id in self.silenced_users:
            try:
                await message.delete()
            except discord.Forbidden:
                pass
            return

        # Se o usuário está confuso, embaralha sua mensagem, apaga a original e envia a versão modificada
        if author_id in self.confused_users:
            try:
                scrambled = self.scramble_text(message.content)
                await message.delete()
                await message.channel.send(f"😵‍💫 {message.author.mention} diz (confuso): {scrambled}")
            except discord.Forbidden:
                pass
            return

    @commands.command()
    async def silencio(self, ctx, membro: discord.Member = None):
        """Lança o feitiço do silêncio em um usuário, impedindo-o de enviar mensagens por 1 minuto"""
        if not membro:
            return await ctx.send("❌ Alô? Em quem você quer jogar o feitiço, hein?")

        if membro == ctx.author:
            return await ctx.send("❌ Está maluco! Quem em sã consciência lançaria um feitiço de silêncio em si mesmo?")

        if membro == self.bot.user:
            return await ctx.send("❌ Hahahaha! Tente novamente quando estiver no nível 9999")

        autor_id, membro_id = ctx.author.id, membro.id 

        # Verifica se o autor já passou do limite diário
        if not self._pode_lancar_feitico(autor_id):
            return await ctx.send(f"❌ Você já usou seu limite diário de {self.limite_diario} feitiços!")

        # Adiciona o alvo à lista de silenciados
        self.silenced_users.add(membro_id)

        # Atualiza o contador de usos
        self._registrar_uso_feitico(autor_id)

        embed = discord.Embed(
            title="🤫 Feitiço do Silêncio!",
            description=f"{membro.mention} foi silenciado por **1 minuto**! Sshhh!",
            color=discord.Color.dark_purple()
        )
        embed.set_image(url=random.choice(self.silence_gifs))
        await ctx.send(embed=embed)

        self.ultimo_canal = ctx.channel.id
        await self._esperar_e_reverter(self.silenced_users, membro_id, 60, f"{membro.mention} pode falar novamente!", discord.Color.green())

    @commands.command()
    async def confusao(self, ctx, membro: discord.Member = None):
        """Embaralha as mensagens de um usuário por 2 minutos."""
        if not membro:
            return await ctx.send("❌ Você precisa mencionar alguém para lançar o feitiço!")

        if membro == ctx.author:
            return await ctx.send("❌ Lançar confusão em si mesmo? Que ousadia!")

        if membro == self.bot.user:
            return await ctx.send("❌ Você acha mesmo que pode me confundir? Heh!")

        autor_id, membro_id = ctx.author.id, membro.id

        if not self._pode_lancar_feitico(autor_id):
            return await ctx.send(f"❌ Você já usou seu limite diário de {self.limite_diario} feitiços!")

        self.confused_users.add(membro_id)
        self._registrar_uso_feitico(autor_id)

        embed = discord.Embed(
            title="😵‍💫 Feitiço da Confusão!",
            description=f"{membro.mention} está totalmente confuso! As palavras não fazem mais sentido por **2 minutos**!",
            color=discord.Color.orange()
        )
        embed.set_image(url=random.choice(self.confusion_gifs))
        await ctx.send(embed=embed)

        self.ultimo_canal = ctx.channel.id
        await self._esperar_e_reverter(self.confused_users, membro_id, 120, f"{membro.mention} recuperou a clareza mental!", discord.Color.green())


async def setup(bot):
    await bot.add_cog(SpellCog(bot))

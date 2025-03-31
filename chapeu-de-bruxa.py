import discord
import random
import wavelink
from discord.ext import commands
from duckduckgo_search import DDGS
from const import TOKEN, GIFS

TOKEN_DISCORD = TOKEN

intents = discord.Intents.default()
intents.messages = True
intents.guilds = True
intents.message_content = True
intents.voice_states = True

class ChapéuDeBruxa(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix=commands.when_mentioned_or("!"), intents=intents)

    async def setup_hook(self):
        """Carregar as Cogs e conectar ao Lavalink"""
        await self.add_cog(MusicCog(self))
        await self.add_cog(GeneralCog(self))
        await connect_lavalink(self)

    async def on_ready(self):
        print(f"{self.user.name} está no ar!")
        for guild in self.guilds:
            print(f"Conectado ao servidor: {guild.name} (ID: {guild.id})")

async def connect_lavalink(bot):
    """Conecta o bot ao servidor Lavalink"""
    try:
        await wavelink.NodePool.create_node(
            bot=bot,
            host="localhost",
            port=2333,
            password="youshallnotpass",
            region="us"
        )
        print("✅ Conectado ao Lavalink!")
    except Exception as e:
        print(f"❌ Erro ao conectar ao Lavalink: {e}")

class MusicCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def entrar(self, ctx):
        """Entra no canal de voz"""
        if not ctx.author.voice:
            return await ctx.send("❌ Você precisa estar em um canal de voz!")

        vc: wavelink.Player = await ctx.author.voice.channel.connect(cls=wavelink.Player)
        if vc:
            await ctx.send(f"🎵 Entrei no canal: {ctx.author.voice.channel.mention}")
        else:
            await ctx.send("❌ Não consegui entrar no canal de voz.")

    @commands.command()
    async def tocar(self, ctx, *, busca: str):
        """Toca uma música usando Wavelink v4"""
        vc: wavelink.Player = ctx.voice_client

        if not vc:
            return await ctx.send("❌ Eu não estou em um canal de voz. Use `!entrar` primeiro.")

        results = await wavelink.YouTubeTrack.search(query=busca)

        if not results:
            return await ctx.send("❌ Nenhuma música encontrada!")

        track = results[0]
        await vc.play(track)
        await ctx.send(f"🎶 Tocando agora: **{track.title}**")

    @commands.command()
    async def sair(self, ctx):
        """Sai do canal de voz"""
        vc: wavelink.Player = ctx.voice_client

        if not vc:
            return await ctx.send("❌ Eu não estou em um canal de voz.")

        await vc.disconnect()
        await ctx.send("👋 Saí do canal de voz.")

class GeneralCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def comandos(self, ctx):
        await ctx.send(f"Olá! Eu sou a **{ctx.bot.user.name}**, uma chatbot básica que pode fazer buscas na internet e responder algumas mensagens.")

    @commands.command()
    async def oi(self, ctx):
        await ctx.send(f"Olá, {ctx.author.mention}! Como vai?")

    @commands.command()
    async def ping(self, ctx):
        latency = round(self.bot.latency * 1000)
        await ctx.send(f"Pong! 🏓 Latência: {latency}ms")

    @commands.command()
    async def repetir(self, ctx, *, mensagem):
        await ctx.send(mensagem)

    @commands.command()
    async def pesquisar(self, ctx, *, consulta):
        await ctx.send(f"🔎 **Buscando por:** {consulta}...")

        try:
            with DDGS() as ddgs:
                resultados = ddgs.text(consulta, max_results=5)

            if not resultados:
                await ctx.send("❌ **Nenhum resultado encontrado.**")
                return

            embed = discord.Embed(
                title=f"🔎 Resultados para: {consulta}",
                description="Aqui estão os melhores links que encontrei:",
                color=discord.Color.purple()
            )

            for result in resultados:
                embed.add_field(name=result["title"], value=f"[Acesse aqui]({result['href']})", inline=False)

            embed.set_image(url=random.choice(GIFS))
            embed.set_footer(text="🧙‍♂️ Pesquisa feita por Chapéu de Bruxa!")

            await ctx.send(embed=embed)

        except Exception as e:
            await ctx.send("❌ **Erro ao buscar informações.**")
            print(f"Erro na resposta: {e}")

bot = ChapéuDeBruxa()

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if isinstance(message.channel, discord.DMChannel):
        await message.channel.send("Olá! Só posso responder em servidores.")
        return

    await bot.process_commands(message)

bot.run(TOKEN_DISCORD)

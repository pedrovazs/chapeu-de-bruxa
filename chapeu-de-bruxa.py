import discord
import random
import wavelink
import json
import asyncio
from discord.ext import commands
from duckduckgo_search import DDGS
from const import TOKEN, GIFS

TOKEN_DISCORD = TOKEN

intents = discord.Intents.default()
intents.messages = True
intents.guilds = True
intents.message_content = True
intents.voice_states = True
intents.members = True

class ChapéuDeBruxa(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix=commands.when_mentioned_or("!"), intents=intents)

    async def setup_hook(self):
        """Carregar as Cogs e conectar ao Lavalink"""
        await self.add_cog(MusicCog(self))
        await self.add_cog(GeneralCog(self))
        await self.add_cog(SpellCog(self))
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
            await ctx.send(f"🎵 Hey! Estou entrarndo no canal: {ctx.author.voice.channel.mention}")
        else:
            await ctx.send("❌ Não consegui entrar no canal de voz.")

    @commands.command()
    async def tocar(self, ctx, *, busca: str):
        """Toca uma música usando Wavelink v4"""

        # Obtém o player de áudio do servidor
        vc: wavelink.Player = ctx.voice_client

        # Se o bot não estiver em um canal de voz, conecta ao canal do autor
        if not vc:
            if not ctx.author.voice:
                return await ctx.send("❌ Você precisa estar em um canal de voz para tocar música!")
            
            vc = await ctx.author.voice.channel.connect(cls=wavelink.Player)

        # Obtém um nó ativo do Lavalink
        node = wavelink.NodePool.get_node()
        if not node:
            return await ctx.send("❌ Nenhum nó Lavalink disponível!")

        # Busca a música no YouTube
        try:
            results = await wavelink.YouTubeTrack.search(busca, node=wavelink.NodePool.get_node())
        except Exception as e:
            return await ctx.send(f"❌ Erro ao buscar música: {e}")

        if not results:
            return await ctx.send("❌ Nenhuma música encontrada!")

        track = results[0]  # Pega a primeira música encontrada

        try:
            await vc.play(track)  # Reproduz a música
        except Exception as e:
            return await ctx.send(f"❌ Erro ao tocar música: {e}")

        await ctx.send(f"🎶 Tocando agora: **{track.title}**")

    @commands.command()
    async def sair(self, ctx):
        """Sai do canal de voz"""
        vc: wavelink.Player = ctx.voice_client

        if not vc:
            return await ctx.send("❌ Eu não estou em um canal de voz.")

        await vc.disconnect()
        await ctx.send("👋 Tchau Tchau, estou saindo do canal de voz.")

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
        
    @commands.command()
    async def zoar(self, ctx, membro: discord.Member = None):
        """Manda um insulto engraçado para um usuário"""
        if not membro:
            return await ctx.send("❌ Preciso que mencione alguém para poder zoar..")

        try:
            with open("json/insultos.json", "r", encoding="utf-8") as f:
                insultos = json.load(f)

            insulto = random.choice(insultos)
            await ctx.send(f"😆 {membro.mention}, {insulto}")

        except Exception as e:
            await ctx.send("❌ Erro ao buscar insultos!")
            print(f"Erro: {e}")
    
    @commands.command()
    async def piada(self, ctx):
        try:
            with open("json/piadas.json", "r", encoding="utf-8") as f:
                piadas = json.load(f)

            piada = random.choice(piadas)
            await ctx.send(f"😆 {piada}")

        except Exception as e:
            await ctx.send("❌ Erro ao buscar uma piada!")
            print(f"Erro: {e}")
    
    @commands.command()
    async def curiosidades(self, ctx):
        try:
            with open("json/curiosidades.json", "r", encoding="utf-8") as f:
                curiosidades = json.load(f)
            
            curiosidade = random.choice(curiosidades)
            await ctx.send(f"👩‍🎓 Curiosidade do dia! \n {curiosidade}")
        
        except Exception as e:
            await ctx.send(f"❌ Erro ao buscar uma curiosidade!")
            print(f"Erro: {e}")

class SpellCog(commands.Cog):
    """Classe que gerencia os feitiços do Chapéu de Bruxa"""
    def __init__(self, bot):
        self.bot = bot
        self.silenced_users = {}  # Armazena usuários silenciados
        self.spell_uses = {}  # Contador de usos do feitiço

    @commands.command()
    async def silencio(self, ctx, membro: discord.Member = None):
        """Lança o feitiço do silêncio em um usuário, impedindo-o de enviar mensagens por 1 minuto"""
        if not membro:
            return await ctx.send("❌ Mas em quem você vai lançar o feitiço!?")

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

        await ctx.send(f"🔮 {membro.mention} foi silenciado por **1 minuto**! Shhh... 🤫")

        # Aguarda 60 segundos e remove o efeito do feitiço
        await asyncio.sleep(60)
        self.silenced_users.pop(membro_id, None)
        await ctx.send(f"🔊 {membro.mention} o feitiço foi desfeito! Agora você pode falar")

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

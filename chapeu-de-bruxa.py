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
        embed = discord.Embed(
            title="🧙‍♀️🔮✨ Comandos disponíveis!",
            description=f"Lista do que eu posso fazer: \n1) !oi \n2) !ping \n3) !repetir \n4) !pesquisar \n5) !zoar \n6) !piada \n7) !curiosidade \n\nE também posso lançar alguns feitiços! 🪄✨",
            color=discord.Color.dark_grey()
            )
        await ctx.send(embed=embed)

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
            embed = discord.Embed(
            title="👩‍🎓 Curiosidade do dia!",
            description=f"{curiosidade}",
            color=discord.Color.blurple()
            )
            await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(f"❌ Erro ao buscar uma curiosidade! Oh não!!")
            print(f"Erro: {e}")

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

bot = ChapéuDeBruxa()

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if isinstance(message.channel, discord.DMChannel):
        await message.channel.send("Olá! Só posso responder em servidores.")
        return
    if message.author.id in bot.get_cog("SpellCog").silenced_users:
            try:
                await message.delete()
            except discord.Forbidden:
                print(f"❌ Não tenho permissão para deletar mensagens em {message.channel}")
            except discord.NotFound:
                pass  # Mensagem já foi deletada
    if message.author.id in bot.get_cog("SpellCog").confused_users:
            if message.content:
                palavras = message.content.split()
                random.shuffle(palavras)
                mensagem_embaralhada = " ".join(palavras)
                
                try:
                    await message.delete()
                    await message.channel.send(f"🤪 **{message.author.display_name}:** {mensagem_embaralhada}")
                except discord.Forbidden:
                    print(f"❌ Não tenho permissão para deletar mensagens em {message.channel}")

    await bot.process_commands(message)

bot.run(TOKEN_DISCORD)

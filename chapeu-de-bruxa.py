import discord
import random
from const import TOKEN, GIFS
from discord.ext import commands
from duckduckgo_search import DDGS

TOKEN_DISCORD = TOKEN

intents = discord.Intents.default()
intents.messages = True
intents.guilds = True
intents.message_content = True

chapeuBruxa = commands.Bot(command_prefix=commands.when_mentioned_or("!"), intents=intents)

@chapeuBruxa.event
async def on_ready():
    print(f"{chapeuBruxa.user.name} está no ar!")
    for guild in chapeuBruxa.guilds:
        print(f"Conectado ao servidor: {guild.name} (ID: {guild.id})")

@chapeuBruxa.event
async def on_message(message):
    if message.author == chapeuBruxa.user:
        return

    if isinstance(message.channel, discord.DMChannel):
        await message.channel.send("Olá! Só posso responder em servidores.")
        return

    await chapeuBruxa.process_commands(message)

@chapeuBruxa.command()
async def oi(ctx):
    await ctx.send(f"Olá, {ctx.author.mention}! Como vai?")

@chapeuBruxa.command()
async def ping(ctx):
    latency = round(chapeuBruxa.latency * 1000)
    await ctx.send(f"Pong! 🏓 Latência: {latency}ms")

@chapeuBruxa.command()
async def repetir(ctx, *, mensagem):
    await ctx.send(mensagem)

@chapeuBruxa.command()
async def pesquisar(ctx, *, consulta):
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
        print(f"erro na resposta: {e}")

chapeuBruxa.run(TOKEN_DISCORD)

import discord
import random
from const import TOKEN
from discord.ext import commands
from duckduckgo_search import DDGS

TOKEN_DISCORD = TOKEN

GIFS = [
    "https://media.giphy.com/media/3o7abldj0b3rxrZUxW/giphy.gif",
    "https://media.giphy.com/media/26BRv0ThflsHCqDrG/giphy.gif",
    "https://media.giphy.com/media/3o7TKU8RvQuomFfUUU/giphy.gif"
]

intents = discord.Intents.default()
intents.messages = True
intents.guilds = True
intents.message_content = True

bot = commands.Bot(command_prefix=commands.when_mentioned_or("!"), intents=intents)

@bot.event
async def on_ready():
    print(f"{bot.user.name} está no ar!")
    for guild in bot.guilds:
        print(f"Conectado ao servidor: {guild.name} (ID: {guild.id})")

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if isinstance(message.channel, discord.DMChannel):
        await message.channel.send("Olá! Só posso responder em servidores.")
        return

    await bot.process_commands(message)

@bot.command()
async def oi(ctx):
    await ctx.send(f"Olá, {ctx.author.mention}! Como vai?")

@bot.command()
async def ping(ctx):
    latency = round(bot.latency * 1000)
    await ctx.send(f"Pong! 🏓 Latência: {latency}ms")

@bot.command()
async def repetir(ctx, *, mensagem):
    await ctx.send(mensagem)

@bot.command()
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

        r# Adicionando os resultados ao embed
        for result in resultados:
            embed.add_field(name=result["title"], value=f"[Acesse aqui]({result['href']})", inline=False)

        # Adiciona um GIF aleatório para deixar mais divertido
        embed.set_image(url=random.choice(GIFS))
        embed.set_footer(text="🧙‍♂️ Pesquisa feita por Chapéu de Bruxa!")

        await ctx.send(embed=embed)

    except Exception as e:
        await ctx.send("❌ **Erro ao buscar informações.**")

bot.run(TOKEN_DISCORD)

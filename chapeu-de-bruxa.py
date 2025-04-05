import discord
import asyncio
import os
from dotenv import load_dotenv
from discord.ext import commands

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.messages = True
intents.guilds = True
intents.message_content = True
intents.voice_states = True
intents.members = True

# Instanciação do bot com o prefixo desejado
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"Bot {bot.user.name} está online!")

# Função para carregar todas as extensões (cogs) presentes na pasta "cogs"
async def load_extensions():
    for filename in os.listdir("./cogs"):
        if filename.endswith(".py"):
            extension = f"cogs.{filename[:-3]}"
            try:
                await bot.load_extension(extension)
                print(f"Carregado: {extension}")
            except Exception as e:
                print(f"Erro ao carregar a extensão {extension}: {e}")

# Função principal que inicia o bot
async def main():
    async with bot:
        await load_extensions()
        await bot.start(TOKEN)

if __name__ == "__main__":
    asyncio.run(main())

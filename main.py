# main.py
import discord
import asyncio
import os
from discord.ext import commands
from config.settings import DISCORD_TOKEN, GUILD_ID

# Define as permissões que o bot precisa para funcionar
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="", intents=intents)

@bot.event
async def on_ready():
    # Sincroniza os slash commands apenas no servidor de testes
    # para propagação instantânea durante o desenvolvimento
    guild = discord.Object(id=GUILD_ID)
    await bot.tree.sync(guild=guild)
    print(f"{bot.user.name} está no ar! 🔮✨")

async def load_extensions():
    for filename in os.listdir("./cogs"):
        if filename.endswith(".py") and filename != "__init__.py":
            extension = f"cogs.{filename[:-3]}"
            try:
                await bot.load_extension(extension)
                print(f"✅ Carregado: {extension}")
            except Exception as e:
                print(f"❌ Erro ao carregar {extension}: {e}")

async def main():
    async with bot:
        await load_extensions()
        await bot.start(DISCORD_TOKEN)

if __name__ == "__main__":
    asyncio.run(main())

# config/settings.py
from dotenv import load_dotenv
import os

# Carrega as variáveis do arquivo .env para o ambiente do processo
load_dotenv()

# Expõe as variáveis como constantes acessíveis em qualquer parte do projeto
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
GUILD_ID = int(os.getenv("GUILD_ID"))

import discord
import random
import json

from discord.ext import commands
from duckduckgo_search import DDGS
from const import GIFS

class GeneralCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def comandos(self, ctx):
        embed = discord.Embed(
            title="🧙‍♀️🔮✨ Comandos Disponíveis",
            color=discord.Color.dark_grey()
        )
        
        embed.add_field(
            name="Comandos Gerais",
            value="`!oi` - Saudações\n`!ping` - Verifica a latência\n`!repetir` - Repete sua mensagem\n`!pesquisar` - Realiza uma busca\n`!zoar` - Uma zoeira divertida",
            inline=False
        )
        
        embed.add_field(
            name="Diversão",
            value="`!piada` - Conta uma piada\n`!curiosidade` - Compartilha uma curiosidade",
            inline=False
        )
        
        embed.add_field(
            name="Feitiços Mágicos",
            value="Posso lançar feitiços incríveis para surpreender você! 🪄✨",
            inline=False
        )
        
        embed.set_footer(text="Experimente os comandos e divirta-se!")
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
            title="👩‍🎓 Aqui vai uma curiosidade!",
            description=f"{curiosidade}",
            color=discord.Color.blurple()
            )
            await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(f"❌ Erro ao buscar uma curiosidade! Oh não!!")
            print(f"Erro: {e}")

async def setup(bot):
    await bot.add_cog(GeneralCog(bot))

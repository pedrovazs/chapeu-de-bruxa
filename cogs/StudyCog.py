import discord
from discord.ext import commands
from discord.ext.commands import Context, Bot
import sqlite3
import os
from datetime import datetime

DB_PATH = "study_data.db"

# Cria o banco de dados se não existir
def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS study_data (
                user_id INTEGER PRIMARY KEY,
                total_minutes INTEGER DEFAULT 0,
                xp INTEGER DEFAULT 0,
                level INTEGER DEFAULT 1,
                last_study TEXT
            )
        ''')
        conn.commit()

class StudyCog(commands.Cog):
    def __init__(self, bot: Bot):
        self.bot = bot
        init_db()

    @commands.command(name="estudei")
    async def estudei(self, ctx: Context, minutos: int):
        """Registra tempo de estudo e calcula XP"""
        user_id = ctx.author.id
        xp_ganho = minutos * 2  # Exemplo: 2 XP por minuto

        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM study_data WHERE user_id = ?", (user_id,))
            row = cursor.fetchone()

            if row:
                total_minutos = row[1] + minutos
                total_xp = row[2] + xp_ganho
                level = (total_xp // 100) + 1
                cursor.execute('''
                    UPDATE study_data 
                    SET total_minutes=?, xp=?, level=?, last_study=?
                    WHERE user_id=?
                ''', (total_minutos, total_xp, level, datetime.utcnow().isoformat(), user_id))
            else:
                cursor.execute('''
                    INSERT INTO study_data (user_id, total_minutes, xp, level, last_study)
                    VALUES (?, ?, ?, ?, ?)
                ''', (user_id, minutos, xp_ganho, 1, datetime.utcnow().isoformat()))

            conn.commit()

        await ctx.send(f"🧠 {ctx.author.mention} registrou {minutos} minutos de estudo e ganhou {xp_ganho} XP!")

    @commands.command(name="xp")
    async def xp(self, ctx: Context):
        """Exibe o XP e o nível do usuário"""
        user_id = ctx.author.id

        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT xp, level, total_minutes FROM study_data WHERE user_id = ?", (user_id,))
            row = cursor.fetchone()

        if row:
            await ctx.send(f"📘 {ctx.author.mention} tem {row[0]} XP, está no nível {row[1]} e estudou {row[2]} minutos no total.")
        else:
            await ctx.send(f"🔍 {ctx.author.mention}, você ainda não registrou nenhum estudo. Use `!estudei [minutos]` para começar!")

async def setup(bot: Bot):
    await bot.add_cog(StudyCog(bot))

import discord
from discord.ext import commands
from discord.ext.commands import Context, Bot
import sqlite3
from datetime import datetime, timezone, timedelta

DB_PATH = "study_data.db"

# Inicializa as tabelas necessárias
def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS study_data (
                user_id INTEGER PRIMARY KEY,
                total_minutes INTEGER DEFAULT 0,
                xp INTEGER DEFAULT 0,
                level INTEGER DEFAULT 1,
                last_study TEXT,
                streak INTEGER DEFAULT 0
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS study_goals (
                user_id INTEGER,
                type TEXT, -- 'diaria' ou 'semanal'
                target_minutes INTEGER,
                current_minutes INTEGER DEFAULT 0,
                start_date TEXT,
                PRIMARY KEY (user_id, type)
            )
        ''')
        conn.commit()

class StudyGamificationCog(commands.Cog):
    def __init__(self, bot: Bot):
        self.bot = bot
        init_db()

    @commands.command(name="estudei")
    async def estudei(self, ctx: Context, minutos: int):
        """Registra tempo de estudo, XP e streak"""
        user_id = ctx.author.id
        xp_ganho = minutos * 1.5
        agora = datetime.now(timezone.utc)
        agora_str = agora.isoformat()

        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT total_minutes, xp, level, last_study, streak FROM study_data WHERE user_id = ?", (user_id,))
            row = cursor.fetchone()

            if row:
                total_minutos = row[0] + minutos
                total_xp = row[1] + xp_ganho
                level = (total_xp // 100) + 1

                # Verificar streak
                streak = row[4] or 0
                last_study = datetime.fromisoformat(row[3]) if row[3] else None
                if last_study:
                    delta = agora.date() - last_study.date()
                    if delta == timedelta(days=1):
                        streak += 1
                    elif delta > timedelta(days=1):
                        streak = 1
                else:
                    streak = 1

                cursor.execute('''
                    UPDATE study_data 
                    SET total_minutes=?, xp=?, level=?, last_study=?, streak=?
                    WHERE user_id=?
                ''', (total_minutos, total_xp, level, agora_str, streak, user_id))
            else:
                streak = 1
                cursor.execute('''
                    INSERT INTO study_data (user_id, total_minutes, xp, level, last_study, streak)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (user_id, minutos, xp_ganho, 1, agora_str, streak))

            # Atualiza as metas
            for tipo in ['diaria', 'semanal']:
                cursor.execute('''
                    SELECT target_minutes, current_minutes, start_date FROM study_goals
                    WHERE user_id=? AND type=?
                ''', (user_id, tipo))
                goal = cursor.fetchone()

                if goal:
                    start_date = datetime.fromisoformat(goal[2])
                    if (tipo == 'diaria' and agora.date() != start_date.date()) or \
                       (tipo == 'semanal' and agora.isocalendar()[1] != start_date.isocalendar()[1]):
                        # Reset da meta
                        cursor.execute('''
                            UPDATE study_goals SET current_minutes=?, start_date=?
                            WHERE user_id=? AND type=?
                        ''', (minutos, agora_str, user_id, tipo))
                    else:
                        cursor.execute('''
                            UPDATE study_goals SET current_minutes=current_minutes+?
                            WHERE user_id=? AND type=?
                        ''', (minutos, user_id, tipo))

            conn.commit()

        await ctx.send(f"🧠 {ctx.author.mention} registrou {minutos} minutos de estudo, ganhou {xp_ganho} XP e está com {streak} dia(s) de streak!")

    @commands.command(name="xp")
    async def xp(self, ctx: Context):
        """Exibe o XP e o nível do usuário"""
        user_id = ctx.author.id

        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT xp, level, total_minutes, streak FROM study_data WHERE user_id = ?", (user_id,))
            row = cursor.fetchone()

        if row:
            await ctx.send(f"📘 {ctx.author.mention} tem {row[0]} XP, está no nível {row[1]}, estudou {row[2]} minutos no total e está com {row[3]} dia(s) de streak.")
        else:
            await ctx.send(f"🔍 {ctx.author.mention}, você ainda não registrou nenhum estudo. Use `!estudei [minutos]` para começar!")

    @commands.command(name="meta")
    async def meta(self, ctx: Context, tipo: str, minutos: int):
        user_id = ctx.author.id
        tipo = tipo.lower()
        agora = datetime.now(timezone.utc)

        if tipo not in ['diaria', 'semanal']:
            await ctx.send("⚠️ Tipo de meta inválido. Use `diaria` ou `semanal`.")
            return

        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO study_goals (user_id, type, target_minutes, current_minutes, start_date)
                VALUES (?, ?, ?, 0, ?)
                ON CONFLICT(user_id, type) DO UPDATE SET target_minutes=excluded.target_minutes, current_minutes=0, start_date=excluded.start_date
            ''', (user_id, tipo, minutos, agora.isoformat()))
            conn.commit()

        await ctx.send(f"🎯 {ctx.author.mention}, sua meta {tipo} foi definida para {minutos} minutos!")

    @commands.command(name="minhasmetas")
    async def minhas_metas(self, ctx: Context):
        user_id = ctx.author.id
        agora = datetime.now(timezone.utc)

        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT type, target_minutes, current_minutes, start_date FROM study_goals WHERE user_id=?", (user_id,))
            metas = cursor.fetchall()

        if not metas:
            await ctx.send("📌 Você ainda não definiu nenhuma meta. Use `!meta diaria 60` ou `!meta semanal 300`.")
            return

        msg = "📊 **Suas Metas de Estudo:**\n"
        for tipo, alvo, atual, data in metas:
            progresso = f"{atual}/{alvo} minutos"
            status = "✅ Cumprida!" if atual >= alvo else "🚧 Em progresso"
            msg += f"\n• {tipo.title()}: {progresso} - {status}"

        await ctx.send(msg)

    @commands.command(name="ranking")
    async def ranking(self, ctx: Context):
        """Mostra o ranking dos que mais estudaram, com streak"""
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT user_id, total_minutes, xp, streak FROM study_data
                ORDER BY total_minutes DESC
                LIMIT 10
            ''')
            top_users = cursor.fetchall()

        if not top_users:
            await ctx.send("📉 Ninguém registrou estudo ainda.")
            return

        embed = discord.Embed(title="🏆 Top 10 Estudantes", color=discord.Color.purple())
        for idx, (user_id, minutos, xp, streak) in enumerate(top_users, start=1):
            user = await self.bot.fetch_user(user_id)
            embed.add_field(
                name=f"{idx}. {user.display_name}",
                value=f"{minutos} minutos • {xp} XP •    🔥 {streak} dia(s) de streak",
                inline=False
            )

        await ctx.send(embed=embed)

async def setup(bot: Bot):
    await bot.add_cog(StudyGamificationCog(bot))

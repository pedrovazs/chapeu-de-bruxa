# cogs/flashcard.py
#
# Cog responsável por /flashcard criar (sugestão via IA + select menu)
# e /flashcard revisar (fluxo de revisão com algoritmo SM-2).

import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime, timedelta
import json
import anthropic

from config.settings import ANTHROPIC_API_KEY
from database.database import (
    inserir_flashcard,
    buscar_flashcard_para_revisao,
    atualizar_flashcard_sm2,
    contar_flashcards_pendentes,
)


# ── SM-2 ──────────────────────────────────────────────────────────────────────
#
# O SM-2 (SuperMemo 2) é um algoritmo de repetição espaçada que decide
# quando cada card deve aparecer novamente com base na dificuldade percebida.
# O estado de cada card é formado por três variáveis:
#   - ease_factor: o multiplicador de intervalo (inicia em 2.5)
#   - intervalo: dias até a próxima revisão
#   - repeticoes: quantas vezes consecutivas o card foi respondido corretamente
#
# No nosso bot, o usuário avalia com 4 botões que mapeiam para valores de qualidade:
#   Fácil → 5 | Bom → 4 | Difícil → 3 | Errei → 1

def calcular_sm2(ease_factor: float, intervalo: int, repeticoes: int, qualidade: int) -> tuple:
    """
    Aplica o SM-2 e retorna o novo estado (ease_factor, intervalo, repeticoes).
    qualidade >= 3 significa que o usuário passou; < 3 significa que falhou.
    """
    if qualidade >= 3:
        # Passou: calcula próximo intervalo com base no histórico de acertos
        if repeticoes == 0:
            novo_intervalo = 1       # primeira vez: revisar amanhã
        elif repeticoes == 1:
            novo_intervalo = 6       # segunda vez: revisar em 6 dias
        else:
            # A partir da terceira vez, o intervalo cresce multiplicado pelo ease_factor.
            # Um ease_factor alto (card fácil) cresce rápido; um baixo (card difícil) cresce devagar.
            novo_intervalo = round(intervalo * ease_factor)

        # O ease_factor sobe quando a resposta é fácil e cai quando é difícil.
        # A fórmula penaliza mais respostas difíceis (qualidade 3) do que fáceis (qualidade 5).
        novo_ease = ease_factor + (0.1 - (5 - qualidade) * (0.08 + (5 - qualidade) * 0.02))
        novo_ease = max(1.3, novo_ease)   # piso de 1.3 — o SM-2 nunca deixa o card ficar "preso"
        novas_repeticoes = repeticoes + 1
    else:
        # Falhou: reseta o ciclo de revisão do zero
        novo_intervalo = 1
        novo_ease = ease_factor       # o ease_factor não é penalizado no erro (comportamento padrão SM-2)
        novas_repeticoes = 0

    return novo_ease, novo_intervalo, novas_repeticoes


# ── VIEW: SELEÇÃO DE FLASHCARDS ───────────────────────────────────────────────
#
# Após a IA sugerir os cards, esta View apresenta um Select menu onde o usuário
# escolhe quais salvar, seguido de um botão de confirmação.

class FlashcardSelectView(discord.ui.View):

    def __init__(self, sugestoes: list, topico: str, bot: commands.Bot):
        # timeout=120: a view expira em 2 minutos se o usuário não interagir
        super().__init__(timeout=120)
        self.sugestoes = sugestoes
        self.topico = topico
        self.bot = bot
        self.indices_selecionados = []

        # Cada SelectOption recebe o índice como value (string).
        # Na hora de salvar, convertemos de volta para int para acessar self.sugestoes[i].
        opcoes = [
            discord.SelectOption(
                label=s["frente"][:100],
                description=(s["verso"][:97] + "...") if len(s["verso"]) > 100 else s["verso"],
                value=str(i),
            )
            for i, s in enumerate(sugestoes)
        ]

        # min_values=1 impede o envio sem seleção.
        # max_values=len(sugestoes) permite selecionar todos de uma vez.
        select = discord.ui.Select(
            placeholder="Escolha os flashcards para salvar...",
            min_values=1,
            max_values=len(sugestoes),
            options=opcoes,
        )
        select.callback = self._on_select
        self.add_item(select)

        salvar = discord.ui.Button(label="💾 Salvar Selecionados", style=discord.ButtonStyle.success)
        salvar.callback = self._on_salvar
        self.add_item(salvar)

    async def _on_select(self, interaction: discord.Interaction):
        # Armazena os índices selecionados para uso no _on_salvar.
        # defer() sem resposta aqui — o feedback real vem do botão Salvar.
        self.indices_selecionados = interaction.data["values"]
        await interaction.response.defer()

    async def _on_salvar(self, interaction: discord.Interaction):
        if not self.indices_selecionados:
            await interaction.response.send_message(
                "⚠️ Selecione pelo menos um flashcard antes de salvar.", ephemeral=True
            )
            return

        hoje = datetime.utcnow().date().isoformat()
        agora = datetime.utcnow().isoformat()
        usuario_id = str(interaction.user.id)

        for idx in self.indices_selecionados:
            card = self.sugestoes[int(idx)]
            await inserir_flashcard(usuario_id, card["frente"], card["verso"], self.topico, hoje, agora)

        # Desabilita todos os itens para evitar que o usuário salve duas vezes
        for item in self.children:
            item.disabled = True

        await interaction.response.edit_message(
            content=f"✅ **{len(self.indices_selecionados)} flashcard(s)** salvos no tópico **{self.topico}**!",
            view=self,
        )


# ── VIEW: REVISÃO DE FLASHCARD ────────────────────────────────────────────────
#
# Fluxo em dois passos:
#   1. Mostra a frente do card com botão "Ver Resposta"
#   2. Ao clicar, mostra o verso e exibe os quatro botões de avaliação SM-2

class FlashcardRevisaoView(discord.ui.View):

    def __init__(self, flashcard: dict, bot: commands.Bot):
        super().__init__(timeout=120)
        self.flashcard = flashcard
        self.bot = bot

    @discord.ui.button(label="👁️ Ver Resposta", style=discord.ButtonStyle.primary)
    async def ver_resposta(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Remove o botão atual e adiciona os quatro botões de avaliação
        self.clear_items()
        self.add_item(self._botao_avaliacao("😅 Errei",   discord.ButtonStyle.danger,    1))
        self.add_item(self._botao_avaliacao("😓 Difícil", discord.ButtonStyle.secondary, 3))
        self.add_item(self._botao_avaliacao("🙂 Bom",     discord.ButtonStyle.primary,   4))
        self.add_item(self._botao_avaliacao("😄 Fácil",   discord.ButtonStyle.success,   5))

        await interaction.response.edit_message(
            content=(
                f"🃏 **Flashcard — {self.flashcard['topico']}**\n\n"
                f"**Frente:** {self.flashcard['frente']}\n"
                f"**Verso:** {self.flashcard['verso']}\n\n"
                f"Como foi?"
            ),
            view=self,
        )

    def _botao_avaliacao(self, label: str, style: discord.ButtonStyle, qualidade: int):
        """
        Cria um botão de avaliação com o valor de qualidade capturado no closure.
        Cada botão precisa passar um valor diferente para o SM-2 — o closure
        garante que cada callback "lembra" do seu próprio valor de qualidade.
        """
        button = discord.ui.Button(label=label, style=style)

        async def callback(interaction: discord.Interaction):
            await self._processar_avaliacao(interaction, qualidade)

        button.callback = callback
        return button

    async def _processar_avaliacao(self, interaction: discord.Interaction, qualidade: int):
        card = self.flashcard

        novo_ease, novo_intervalo, novas_repeticoes = calcular_sm2(
            ease_factor=card["ease_factor"],
            intervalo=card["intervalo"],
            repeticoes=card["repeticoes"],
            qualidade=qualidade,
        )

        agora = datetime.utcnow()
        proxima = (agora + timedelta(days=novo_intervalo)).date().isoformat()

        await atualizar_flashcard_sm2(
            flashcard_id=card["id"],
            ease_factor=novo_ease,
            intervalo=novo_intervalo,
            repeticoes=novas_repeticoes,
            proxima_revisao=proxima,
            ultima_revisao=agora.isoformat(),
        )

        for item in self.children:
            item.disabled = True

        labels = {5: "Fácil 😄", 4: "Bom 🙂", 3: "Difícil 😓", 1: "Errei 😅"}

        await interaction.response.edit_message(
            content=(
                f"✅ **Avaliação registrada:** {labels.get(qualidade, '?')}\n"
                f"📅 Próxima revisão em **{novo_intervalo} dia(s)** ({proxima})\n"
                f"🔄 Sequência de acertos: {novas_repeticoes}"
            ),
            view=self,
        )


# ── GROUP ─────────────────────────────────────────────────────────────────────

class FlashcardGroup(app_commands.Group, name="flashcard", description="Comandos de flashcard"):

    def __init__(self, bot: commands.Bot):
        super().__init__()
        self.bot = bot
        # AsyncAnthropic é o cliente assíncrono do SDK — compatível com o event loop do discord.py.
        # É instanciado uma vez aqui e reutilizado em todas as chamadas ao comando /criar.
        self.client = anthropic.AsyncAnthropic(api_key=ANTHROPIC_API_KEY)

    @app_commands.command(name="criar", description="Gera sugestões de flashcards com IA para um tópico")
    @app_commands.describe(topico="Tópico ou subtópico para gerar os flashcards")
    async def criar(self, interaction: discord.Interaction, topico: str):
        # defer() é obrigatório aqui porque a chamada à API da Anthropic pode
        # demorar mais de 3 segundos — o prazo padrão do Discord para responder.
        # Após o defer(), temos até 15 minutos para enviar a resposta com followup.
        await interaction.response.defer(ephemeral=True)

        try:
            response = await self.client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=1000,
                system=(
                    "Você é um especialista em criação de flashcards para concursos públicos brasileiros. "
                    "Responda APENAS com um array JSON válido contendo de 3 a 5 objetos, "
                    "cada um com as chaves 'frente' (pergunta ou conceito, máx. 100 chars) "
                    "e 'verso' (resposta objetiva, máx. 200 chars). "
                    "Sem texto adicional, sem markdown, sem explicações. Apenas o JSON puro."
                ),
                messages=[{"role": "user", "content": f"Crie flashcards sobre: {topico}"}],
            )

            # O modelo retorna texto puro — extraímos e parseamos o JSON.
            # strip() remove espaços e quebras de linha que possam quebrar o parse.
            sugestoes = json.loads(response.content[0].text.strip())

        except (json.JSONDecodeError, IndexError, KeyError) as e:
            await interaction.followup.send(
                "❌ A IA retornou um formato inesperado. Tenta novamente.", ephemeral=True
            )
            raise e
        except Exception as e:
            await interaction.followup.send(
                "❌ Erro ao conectar com a API. Verifique a chave e tente novamente.", ephemeral=True
            )
            raise e

        view = FlashcardSelectView(sugestoes, topico, self.bot)

        # Mostra as sugestões em texto antes do select menu para o usuário
        # já saber o que está selecionando sem precisar expandir cada opção.
        linhas = [f"🤖 **Sugestões para:** {topico}\n"]
        for i, s in enumerate(sugestoes, 1):
            linhas.append(f"**{i}.** {s['frente']}\n> {s['verso']}")

        await interaction.followup.send("\n".join(linhas), view=view, ephemeral=True)

    @app_commands.command(name="revisar", description="Inicia uma revisão com repetição espaçada (SM-2)")
    async def revisar(self, interaction: discord.Interaction):
        usuario_id = str(interaction.user.id)
        flashcard = await buscar_flashcard_para_revisao(usuario_id)

        if not flashcard:
            pendentes = await contar_flashcards_pendentes(usuario_id)
            await interaction.response.send_message(
                f"✅ Nenhum flashcard pendente de revisão hoje!\n"
                f"Total de cards cadastrados: **{pendentes}**",
                ephemeral=True,
            )
            return

        view = FlashcardRevisaoView(flashcard, self.bot)

        await interaction.response.send_message(
            content=(
                f"🃏 **Flashcard — {flashcard['topico']}**\n\n"
                f"**Frente:** {flashcard['frente']}\n\n"
                f"*(Clique em Ver Resposta quando estiver pronto)*"
            ),
            view=view,
            ephemeral=True,
        )


# ── COG ───────────────────────────────────────────────────────────────────────

class Flashcard(commands.Cog):

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.bot.tree.add_command(FlashcardGroup(bot))

    def cog_unload(self):
        self.bot.tree.remove_command("flashcard")


async def setup(bot: commands.Bot):
    await bot.add_cog(Flashcard(bot))

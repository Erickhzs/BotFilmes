import os
import logging
from anthropic import Anthropic
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# ── Logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ── Clientes ─────────────────────────────────────────────────────────────────
anthropic = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

# ── System prompt ─────────────────────────────────────────────────────────────
SYSTEM_PROMPT = """Você é PROD_BOT, um especialista em recomendação de produtos.

Seu estilo:
- Direto e objetivo, mas amigável
- Faça no máximo 2 perguntas por vez
- Sempre pergunte sobre: orçamento, uso principal, preferências
- Ao recomendar, dê 2-3 opções concretas com nome real, faixa de preço e justificativa
- Formate bem para o Telegram usando *negrito*, _itálico_ e emojis
- Finalize com: 🏆 *Recomendação principal:* [produto]
- Pergunte se quer mais detalhes após recomendar

Formato das recomendações:
📦 *[Nome do Produto]*
💰 Preço: R$ XX.XXX
✅ Melhor para: ...
⚡ Destaque: ...

Nunca invente especificações falsas. Responda sempre em português do Brasil."""

# ── Histórico por usuário (em memória) ───────────────────────────────────────
user_histories: dict[int, list] = {}

def get_history(user_id: int) -> list:
    return user_histories.setdefault(user_id, [])

def clear_history(user_id: int):
    user_histories[user_id] = []

# ── Handlers ──────────────────────────────────────────────────────────────────
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    clear_history(update.effective_user.id)
    await update.message.reply_text(
        "🤖 *PROD\\_BOT — Recomendador de Produtos*\n\n"
        "Olá! Sou seu assistente especialista em recomendação de produtos.\n\n"
        "Me diga:\n"
        "• Que tipo de produto você busca?\n"
        "• Qual é seu orçamento?\n\n"
        "Vou te indicar as melhores opções! 🎯\n\n"
        "_Use /reset para reiniciar a conversa._",
        parse_mode="Markdown"
    )

async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    clear_history(update.effective_user.id)
    await update.message.reply_text(
        "🔄 Conversa reiniciada! Me diga o que você está buscando.",
        parse_mode="Markdown"
    )

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "ℹ️ *Como usar o PROD\\_BOT:*\n\n"
        "1. Diga qual produto você quer\n"
        "2. Responda as perguntas sobre orçamento e uso\n"
        "3. Receba recomendações personalizadas!\n\n"
        "*Comandos:*\n"
        "/start — Iniciar conversa\n"
        "/reset — Reiniciar do zero\n"
        "/help — Esta mensagem",
        parse_mode="Markdown"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_text = update.message.text

    history = get_history(user_id)
    history.append({"role": "user", "content": user_text})

    # Indicador de digitação
    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id,
        action="typing"
    )

    try:
        response = anthropic.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1000,
            system=SYSTEM_PROMPT,
            messages=history
        )

        reply = response.content[0].text
        history.append({"role": "assistant", "content": reply})

        # Limita histórico a 20 mensagens para economizar tokens
        if len(history) > 20:
            user_histories[user_id] = history[-20:]

        await update.message.reply_text(reply, parse_mode="Markdown")

    except Exception as e:
        logger.error(f"Erro ao chamar Claude: {e}")
        await update.message.reply_text(
            "⚠️ Ocorreu um erro. Tente novamente em instantes."
        )

# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    token = os.environ["TELEGRAM_TOKEN"]
    app = ApplicationBuilder().token(token).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("reset", reset))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("PROD_BOT iniciado e aguardando mensagens...")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()

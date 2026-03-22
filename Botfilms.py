import os
import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, filters
)

TOKEN = os.environ.get("TOKEN")
ADMIN_ID = int(os.environ.get("ADMIN_ID"))
DB_FILE = "filmes.json"

def load_db():
    if not os.path.exists(DB_FILE):
        return {}
    with open(DB_FILE, "r") as f:
        return json.load(f)

def save_db(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎬 *Bem-vindo ao MovieBot!*\n\nUse /filmes para ver os filmes disponíveis.",
        parse_mode="Markdown"
    )

async def listar_filmes(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    db = load_db()
    if not db:
        await update.message.reply_text("😕 Nenhum filme disponível ainda.")
        return
    botoes = []
    for nome in db:
        botoes.append([InlineKeyboardButton(f"🎥 {nome}", callback_data=f"filme:{nome}")])
    markup = InlineKeyboardMarkup(botoes)
    await update.message.reply_text("📽 *Filmes disponíveis:*", reply_markup=markup, parse_mode="Markdown")

async def enviar_filme(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    nome = query.data.replace("filme:", "")
    db = load_db()
    if nome not in db:
        await query.message.reply_text("❌ Filme não encontrado.")
        return
    file_id = db[nome]
    await query.message.reply_text(f"⏳ Enviando *{nome}*...", parse_mode="Markdown")
    await ctx.bot.send_document(chat_id=query.message.chat_id, document=file_id, caption=f"🎬 {nome}")

async def receber_arquivo(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if user_id != ADMIN_ID:
        await update.message.reply_text("⛔ Apenas o admin pode enviar filmes.")
        return
    doc = update.message.document or update.message.video
    if not doc:
        await update.message.reply_text("❌ Envie um arquivo de vídeo/documento.")
        return
    nome = update.message.caption or getattr(doc, 'file_name', None) or "Filme sem nome"
    file_id = doc.file_id
    db = load_db()
    db[nome] = file_id
    save_db(db)
    await update.message.reply_text(f"✅ *{nome}* adicionado com sucesso!", parse_mode="Markdown")

async def deletar_filme(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != ADMIN_ID:
        await update.message.reply_text("⛔ Apenas o admin.")
        return
    if not ctx.args:
        await update.message.reply_text("Uso: /deletar Nome do Filme")
        return
    nome = " ".join(ctx.args)
    db = load_db()
    if nome in db:
        del db[nome]
        save_db(db)
        await update.message.reply_text(f"🗑 *{nome}* removido.", parse_mode="Markdown")
    else:
        await update.message.reply_text("❌ Filme não encontrado.")

app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("filmes", listar_filmes))
app.add_handler(CommandHandler("deletar", deletar_filme))
app.add_handler(CallbackQueryHandler(enviar_filme, pattern="^filme:"))
app.add_handler(MessageHandler(filters.Document.ALL | filters.VIDEO, receber_arquivo))

print("🤖 Bot rodando...")
app.run_polling()
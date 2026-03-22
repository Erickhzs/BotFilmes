from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import sqlite3
import os

TOKEN = os.getenv("TOKEN")

# Conectar banco
conn = sqlite3.connect("movies.db", check_same_thread=False)
cursor = conn.cursor()

# Criar tabela
cursor.execute("""
CREATE TABLE IF NOT EXISTS movies (
    name TEXT PRIMARY KEY,
    link TEXT
)
""")
conn.commit()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎬 Bot de Filmes com banco\n\n"
        "Comandos:\n"
        "/add nome link\n"
        "/list\n"
        "/watch nome"
    )

async def add_movie(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2:
        await update.message.reply_text("❌ Use: /add nome link")
        return

    name = context.args[0].lower()
    link = context.args[1]

    cursor.execute("INSERT OR REPLACE INTO movies VALUES (?, ?)", (name, link))
    conn.commit()

    await update.message.reply_text(f"✅ '{name}' salvo!")

async def list_movies(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cursor.execute("SELECT name FROM movies")
    results = cursor.fetchall()

    if not results:
        await update.message.reply_text("📭 Nenhum filme.")
        return

    msg = "🎬 Filmes:\n\n"
    for row in results:
        msg += f"- {row[0]}\n"

    await update.message.reply_text(msg)

async def watch_movie(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 1:
        await update.message.reply_text("❌ Use: /watch nome")
        return

    name = context.args[0].lower()

    cursor.execute("SELECT link FROM movies WHERE name=?", (name,))
    result = cursor.fetchone()

    if result:
        await update.message.reply_text(f"🍿 {result[0]}")
    else:
        await update.message.reply_text("❌ Filme não encontrado.")

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("add", add_movie))
app.add_handler(CommandHandler("list", list_movies))
app.add_handler(CommandHandler("watch", watch_movie))

app.run_polling()

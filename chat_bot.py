# 🎯 Import our magical tools
import os
from dotenv import load_dotenv  # This helps us keep secrets safe!
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from bot.tools import TOOLS, check_ads_alert
from bot.bot import bot
from bot.prompts import get_system_prompt

# 🔐 Load our secret settings
load_dotenv()

# 🔑 Get the bot token (like getting the key to start our bot)
TOKEN = os.getenv('TELEGRAM_TOKEN')

# 👋 This function runs when someone starts the bot
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Greets users when they first start the bot"""
    await update.message.reply_text('Hello! 👋 I am your friendly bot assistant! Send me any message and I will respond! 🌟')

# 🔔 Periodic job: check ads spend and send alert if threshold exceeded
async def check_and_send_alert(context: ContextTypes.DEFAULT_TYPE):
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    if not chat_id:
        return
    alert = check_ads_alert()
    if alert:
        await context.bot.send_message(chat_id=chat_id, text=alert, parse_mode="Markdown")


# 💬 This function handles any messages people send
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Responds to user messages with a friendly message"""
    print("User", update.message.from_user.first_name, "said:", update.message.text)

    # Store chat_id so the alert job knows where to send proactive messages
    context.bot_data["chat_id"] = update.effective_chat.id

    # Initialize the conversation history
    if 'messages' not in context.user_data:
        context.user_data['messages'] = [
            {"role": "system", "content": get_system_prompt(update.message.text)}
        ]

    # Add the user's message to the conversation history
    context.user_data['messages'].append(
        {"role": "user", "content": update.message.text}
    )
    
    response = bot(context.user_data['messages'])

    # Add the bot's response to the conversation history
    context.user_data['messages'].append(
        {"role": "assistant", "content": response}
    )

    # Send the response to the user
    await update.message.reply_text(response)

    # await update.message.reply_text("I got your message! 📫 Right now I'm just learning to talk, but soon I'll be much smarter! ✨")

# 🚨 This function handles any errors that might happen
async def error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Logs errors"""
    print(f'Oops! 😅 Update {update} caused error {context.error}')

# 🎮 Main function that runs our bot
def main():
    # Create the bot application
    app = Application.builder().token(TOKEN).build()
    
    # Tell the bot what to do with different types of messages
    app.add_handler(CommandHandler('start', start_command))  # Handles /start command
    app.add_handler(MessageHandler(filters.TEXT, handle_message))  # Handles text messages

    # Add our error handler
    app.add_error_handler(error)

    # Check ads spend alert every hour (first check 10s after startup)
    app.job_queue.run_repeating(check_and_send_alert, interval=3600, first=10)

    # Start the bot
    print('🚀 Starting bot...')
    app.run_polling(poll_interval=1)

if __name__ == '__main__':
    main()
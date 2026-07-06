import os
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from deep_translator import GoogleTranslator
from langdetect import detect, DetectorFactory
from langdetect.lang_detect_exception import LangDetectException

# Set seed for consistent language detection
DetectorFactory.seed = 0

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Get bot token from environment variable
TOKEN = os.getenv('TELEGRAM_TOKEN')

# Default target language
TARGET_LANG = 'en'

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a welcome message when /start is issued."""
    welcome_text = (
        "👋 Hello! I'm Language1000 Translator Bot.\n\n"
        "Simply send me any text in any language, and I'll automatically detect it "
        "and translate it to English.\n\n"
        "📝 Commands:\n"
        "/start - Show this message\n"
        "/help - Show help\n"
        "/lang - Set target language (e.g., /lang es for Spanish)\n"
        "/info - Show your current settings"
    )
    await update.message.reply_text(welcome_text)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send help message."""
    help_text = (
        "📖 How to use me:\n\n"
        "1. Send me any text message\n"
        "2. I'll detect the language automatically\n"
        "3. I'll translate it to English (or your chosen target language)\n\n"
        "Commands:\n"
        "/start - Welcome message\n"
        "/help - This help text\n"
        "/lang <code> - Set target language (e.g., /lang es, /lang fr, /lang de)\n"
        "/info - Show your current settings\n\n"
        "Supported language codes: en, es, fr, de, it, pt, ru, ja, ko, zh, ar, hi, and more!"
    )
    await update.message.reply_text(help_text)

async def set_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Set the target language for translation."""
    user_id = update.effective_user.id
    
    if not context.args:
        await update.message.reply_text(
            "Please provide a language code. Example: /lang es\n\n"
            "Common codes: en (English), es (Spanish), fr (French), de (German), "
            "it (Italian), pt (Portuguese), ru (Russian), ja (Japanese), ko (Korean), "
            "zh (Chinese), ar (Arabic), hi (Hindi)"
        )
        return
    
    lang_code = context.args[0].lower()
    
    # Check if language code is valid (simple validation)
    try:
        # Try to translate a test text to validate the language code
        GoogleTranslator(source='auto', target=lang_code).translate("test")
        context.user_data['target_lang'] = lang_code
        await update.message.reply_text(f"✅ Target language set to: {lang_code}")
    except Exception:
        await update.message.reply_text(
            f"❌ Invalid language code: '{lang_code}'. Please use a valid code like en, es, fr, de, etc."
        )

async def info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show user's current settings."""
    user_id = update.effective_user.id
    target_lang = context.user_data.get('target_lang', TARGET_LANG)
    
    info_text = (
        f"📊 Your current settings:\n"
        f"• Target language: {target_lang}\n"
        f"• Auto-detect source language: Yes\n\n"
        f"To change target language, use: /lang <code>"
    )
    await update.message.reply_text(info_text)

async def translate_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Detect language and translate any text message."""
    user_id = update.effective_user.id
    text = update.message.text
    
    if not text:
        await update.message.reply_text("Please send me some text to translate.")
        return
    
    try:
        # Detect the source language
        source_lang = detect(text)
        logger.info(f"Detected language: {source_lang} for text: {text[:50]}...")
        
        # Get user's target language preference, fallback to 'en'
        target_lang = context.user_data.get('target_lang', TARGET_LANG)
        
        # If source and target are the same, notify user
        if source_lang == target_lang:
            await update.message.reply_text(
                f"📝 Your message appears to already be in {target_lang}. "
                f"No translation needed.\n\n"
                f"To translate to a different language, use: /lang <code>"
            )
            return
        
        # Perform translation
        translator = GoogleTranslator(source=source_lang, target=target_lang)
        translated_text = translator.translate(text)
        
        # Send the translation result
        response = (
            f"🌐 **Translation**\n"
            f"From: `{source_lang}`\n"
            f"To: `{target_lang}`\n\n"
            f"📝 **Original:**\n{text}\n\n"
            f"✅ **Translated:**\n{translated_text}"
        )
        await update.message.reply_text(response, parse_mode='Markdown')
        
    except LangDetectException:
        await update.message.reply_text(
            "❌ Sorry, I couldn't detect the language. Please send a longer text or check your input."
        )
    except Exception as e:
        logger.error(f"Translation error: {e}")
        await update.message.reply_text(
            "❌ Sorry, something went wrong during translation. Please try again later."
        )

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Log errors."""
    logger.warning(f"Update {update} caused error {context.error}")

def main():
    """Start the bot."""
    if not TOKEN:
        logger.error("TELEGRAM_TOKEN environment variable not set!")
        return
    
    # Create the Application
    application = ApplicationBuilder().token(TOKEN).build()
    
    # Register command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("lang", set_language))
    application.add_handler(CommandHandler("info", info))
    
    # Register message handler for text messages
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, translate_message))
    
    # Register error handler
    application.add_error_handler(error_handler)
    
    # Start the bot using long polling
    logger.info("🚀 Bot is starting...")
    application.run_polling()

if __name__ == '__main__':
    main()

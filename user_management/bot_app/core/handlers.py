import logging
import asyncio
import base64
import io
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters, Application
from bot_app.config import Config
from bot_app.core.services import (
    get_user_info, 
    shorten_url_service, 
    promote_to_vip_service,
    list_urls_service,
    delete_url_service
)
from app import db 

logger = logging.getLogger(__name__)

# Helper to run function with app context
def execute_with_context(app, func, *args, **kwargs):
    with app.app_context():
        # Ensure we return values, not objects bound to session
        return func(*args, **kwargs)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    flask_app = context.application.bot_data['flask_app']
    
    loop = asyncio.get_running_loop()
    
    # Get info dict
    info = await loop.run_in_executor(None, execute_with_context, flask_app, get_user_info, user_id)
    
    is_vip_user = info['is_vip']
    url_count = info['url_count']
    
    role_name = "VIP" if is_vip_user else "Free"
    limit_msg = "Unlimited" if is_vip_user else f"{url_count}/30"
    
    message = (
        f"👋 Welcome to URL Shortener Bot!\n\n"
        f"Your Status: *{role_name}*\n"
        f"Usage: {limit_msg}\n\n"
        f"To shorten a URL, just send me the link.\n"
        f"Example: `https://google.com`\n\n"
        f"To upgrade to VIP, use /upgrade."
    )
    await update.message.reply_text(message, parse_mode='Markdown')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = (
        "🤖 *Bot Commands:*\n"
        "/start - Check status\n"
        "/list - View your recent URLs\n"
        "/delete <key> - Delete a URL\n"
        "/upgrade - Upgrade to VIP\n\n"
        "*Shortening:*\n"
        "Just send a URL: `https://example.com`\n"
        "VIPs can set alias: `https://example.com my-alias`"
    )
    await update.message.reply_text(msg, parse_mode='Markdown')

async def upgrade(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = (
        "<b>Upgrade to VIP</b>\n\n"
        "Unlock unlimited URLs and custom aliases!\n"
        f"Price: {Config.VIP_PRICE}\n\n"
        f"Bank: {Config.VIP_BANK}\n"
        f"Account: <code>{Config.VIP_ACCOUNT}</code>\n\n"
        "Please transfer and <b>send the slip image</b> here."
    )
    await update.message.reply_text(msg, parse_mode='HTML')

async def handle_slip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not Config.ADMIN_TELEGRAM_ID:
        await update.message.reply_text("Admin contact not configured. Please contact support.")
        return

    user = update.effective_user
    photo = update.message.photo[-1] # Best quality
    caption = f"Slip from User: `{user.id}`\nName: {user.first_name}\nApprove cmd: `/approve {user.id}`"
    
    # Forward to Admin
    try:
        await context.bot.send_photo(
            chat_id=Config.ADMIN_TELEGRAM_ID,
            photo=photo.file_id,
            caption=caption,
            parse_mode='Markdown'
        )
        await update.message.reply_text("✅ Slip received! Waiting for admin approval.")
    except Exception as e:
        logger.error(f"Failed to forward slip: {e}")
        await update.message.reply_text("❌ Failed to send slip. Please try again.")

async def approve(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    flask_app = context.application.bot_data['flask_app']
    
    # Check if sender is admin
    if str(user_id) != str(Config.ADMIN_TELEGRAM_ID):
        return # Ignore non-admins
        
    try:
        target_uid = int(context.args[0]) # This is Telegram ID
    except (IndexError, ValueError):
        await update.message.reply_text("Usage: /approve <telegram_id>")
        return

    loop = asyncio.get_running_loop()
    
    success = await loop.run_in_executor(None, execute_with_context, flask_app, promote_to_vip_service, target_uid)
    
    if success:
        await update.message.reply_text(f"✅ User `{target_uid}` promoted to VIP successfully.")
        
        # Notify the user
        try:
            await context.bot.send_message(chat_id=target_uid, text="🎉 Your account has been upgraded to VIP! Enjoy unlimited URLs and custom aliases.")
        except Exception as e:
            await update.message.reply_text(f"⚠️ Promoted, but failed to notify user: {e}")
    else:
        await update.message.reply_text(f"❌ Failed to promote user `{target_uid}`. User might not exist.")
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    parts = text.split()
    target_url = parts[0]
    custom_alias = parts[1] if len(parts) > 1 else None
    
    user_id = update.effective_user.id
    flask_app = context.application.bot_data['flask_app']
    
    loop = asyncio.get_running_loop()
    
    # Shorten Service (Handles Auth internally)
    result = await loop.run_in_executor(None, execute_with_context, flask_app, shorten_url_service, user_id, target_url, custom_alias)
    
    if "error" in result:
        await update.message.reply_text(f"⚠️ {result['message']}")
    else:
        # DEBUG: Print result to see if qr_code exists
        print(f"DEBUG API Result: {result}")
        
        short_url = result.get('url')
        qr_code_data = result.get('qr_code')
        
        if short_url:
            msg_text = f"✅ Shortened: {short_url}"
            
            if qr_code_data and "base64," in qr_code_data:
                try:
                    # Decode Base64
                    base64_str = qr_code_data.split("base64,")[1]
                    img_data = base64.b64decode(base64_str)
                    photo_file = io.BytesIO(img_data)
                    photo_file.name = "qr_code.png"
                    
                    await update.message.reply_photo(photo=photo_file, caption=msg_text)
                except Exception as e:
                    logger.error(f"Failed to send QR code: {e}")
                    await update.message.reply_text(msg_text)
            else:
                await update.message.reply_text(msg_text)
        else:
            await update.message.reply_text("❌ Unknown error.")

import html

async def list_urls(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    flask_app = context.application.bot_data['flask_app']
    loop = asyncio.get_running_loop()
    
    urls = await loop.run_in_executor(None, execute_with_context, flask_app, list_urls_service, user_id)
    
    if not urls:
        await update.message.reply_text("📭 You haven't shortened any URLs yet.")
        return

    # Sort by created_at desc (if available) or just reverse
    urls = urls[-10:] # Get last 10
    urls.reverse() # Newest first
    
    msg = "<b>Your Recent URLs:</b>\n\n"
    for item in urls:
        orig = item.get('target_url', '???')
        short = item.get('url', '???') 
        
        # so we need to construct it or use what's available.
        key = item.get('key')
        clicks = item.get('clicks', 0)
        
        # Construct full URL if missing
        if 'url' not in item and key:
             short = f"{Config.SHORTENER_HOST}/{key}"
        
        secret = item.get('secret_key') or 'unknown'
        
        # Escape content for HTML
        safe_orig = html.escape(orig)
        safe_short = html.escape(short)
        safe_secret = html.escape(secret)
        
        msg += f"🔗 <a href='{safe_short}'>{safe_short}</a>\nOf: {safe_orig}\n📊 Clicks: {clicks}\n🗑 Delete: <code>/delete {safe_secret}</code>\n\n"
        
    await update.message.reply_text(msg, parse_mode='HTML', disable_web_page_preview=True)

async def delete_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    flask_app = context.application.bot_data['flask_app']
    
    try:
        secret_key = context.args[0]
    except (IndexError, ValueError):
        await update.message.reply_text("Usage: /delete <secret_key>\nCheck /list to find your secret keys.")
        return

    loop = asyncio.get_running_loop()
    result = await loop.run_in_executor(None, execute_with_context, flask_app, delete_url_service, user_id, secret_key)
    
    if result['success']:
        await update.message.reply_text("✅ URL deleted successfully.")
    else:
        await update.message.reply_text(f"❌ {result['message']}")

def setup_handlers(application: Application):
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("upgrade", upgrade))
    application.add_handler(CommandHandler("approve", approve))
    application.add_handler(CommandHandler("list", list_urls))
    application.add_handler(CommandHandler("delete", delete_url))
    
    # Handle Slips (Photos)
    application.add_handler(MessageHandler(filters.PHOTO, handle_slip))
    
    # Handle URLs (Text)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

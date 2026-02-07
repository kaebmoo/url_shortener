import logging
import asyncio
import base64
import io
import html
import time
from datetime import datetime
from collections import defaultdict
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ChatAction
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, CallbackQueryHandler, filters, Application
from telegram.error import RetryAfter, TimedOut
from bot_app.config import Config
from bot_app.core.services import (
    get_user_info,
    shorten_url_service,
    promote_to_vip_service,
    list_urls_service,
    delete_url_service,
    is_valid_url
)

logger = logging.getLogger(__name__)

# --- Rate Limiting ---
user_last_action = defaultdict(float)
RATE_LIMIT_SECONDS = 2

def check_rate_limit(user_id: int) -> bool:
    """Check if user is rate limited. Returns True if allowed, False if limited."""
    now = time.time()
    last = user_last_action[user_id]
    if now - last < RATE_LIMIT_SECONDS:
        return False
    user_last_action[user_id] = now
    return True

# --- Pending Requests Storage ---
# In-memory storage for pending upgrade requests
# Format: {telegram_id: {"name": str, "timestamp": datetime, "photo_file_id": str}}
pending_requests = {}

def add_pending_request(user_id: int, user_name: str, photo_file_id: str):
    """Add a pending upgrade request."""
    pending_requests[user_id] = {
        "name": user_name,
        "timestamp": datetime.now(),
        "photo_file_id": photo_file_id
    }

def remove_pending_request(user_id: int):
    """Remove a pending request after approval/rejection."""
    if user_id in pending_requests:
        del pending_requests[user_id]

def get_pending_requests():
    """Get all pending requests."""
    return pending_requests.copy()

# --- Helpers ---

def execute_with_context(app, func, *args, **kwargs):
    """Run function with Flask app context."""
    with app.app_context():
        return func(*args, **kwargs)

async def send_typing_action(update: Update):
    """Send typing indicator to show bot is processing."""
    try:
        await update.message.chat.send_action(ChatAction.TYPING)
    except Exception:
        pass

async def handle_telegram_error(update: Update, error: Exception):
    """Handle Telegram API errors gracefully."""
    if isinstance(error, RetryAfter):
        logger.warning(f"Rate limited by Telegram. Retry after {error.retry_after} seconds")
        await asyncio.sleep(error.retry_after)
        return True
    elif isinstance(error, TimedOut):
        logger.warning("Telegram request timed out")
        return False
    else:
        logger.error(f"Telegram error: {error}")
        return False

def is_admin(user_id: int) -> bool:
    """Check if user is admin."""
    return str(user_id) == str(Config.ADMIN_TELEGRAM_ID)

# --- Command Handlers ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if not check_rate_limit(user_id):
        return

    flask_app = context.application.bot_data['flask_app']

    await send_typing_action(update)

    loop = asyncio.get_running_loop()
    info = await loop.run_in_executor(None, execute_with_context, flask_app, get_user_info, user_id)

    is_vip_user = info['is_vip']
    url_count = info['url_count']

    role_name = "VIP ⭐" if is_vip_user else "Free"
    limit_msg = "Unlimited" if is_vip_user else f"{url_count}/30"

    message = (
        f"👋 Welcome to URL Shortener Bot!\n\n"
        f"Your Status: *{role_name}*\n"
        f"Usage: {limit_msg}\n\n"
        f"To shorten a URL, just send me the link.\n"
        f"Example: `https://google.com`\n\n"
        f"Commands: /help"
    )
    await update.message.reply_text(message, parse_mode='Markdown')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not check_rate_limit(update.effective_user.id):
        return

    msg = (
        "🤖 *Bot Commands:*\n\n"
        "/start - Check your status\n"
        "/list - View your recent URLs\n"
        "/delete <key> - Delete a URL\n"
        "/upgrade - Upgrade to VIP\n"
        "/help - Show this help\n\n"
        "*How to shorten:*\n"
        "Just send a URL: `https://example.com`\n\n"
        "*VIP Features:*\n"
        "• Unlimited URLs\n"
        "• Custom aliases: `https://example.com myalias`"
    )
    await update.message.reply_text(msg, parse_mode='Markdown')

async def upgrade(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not check_rate_limit(update.effective_user.id):
        return

    keyboard = [
        [InlineKeyboardButton("❌ Cancel", callback_data="cancel_upgrade")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    msg = (
        "<b>🌟 Upgrade to VIP</b>\n\n"
        "Unlock premium features:\n"
        "• ♾️ Unlimited URLs\n"
        "• ✨ Custom aliases\n"
        "• 🚀 Priority support\n\n"
        f"<b>Price:</b> {Config.VIP_PRICE}\n\n"
        f"<b>Bank:</b> {Config.VIP_BANK}\n"
        f"<b>Account:</b> <code>{Config.VIP_ACCOUNT}</code>\n\n"
        "📸 After transfer, <b>send the slip image</b> here."
    )
    await update.message.reply_text(msg, parse_mode='HTML', reply_markup=reply_markup)

async def cancel_upgrade_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle cancel button in upgrade flow."""
    query = update.callback_query
    await query.answer()

    await query.edit_message_text(
        "❌ Upgrade cancelled.\n\nUse /upgrade anytime to see the options again."
    )

# --- Slip & Admin Handlers ---

async def handle_slip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not check_rate_limit(update.effective_user.id):
        return

    if not Config.ADMIN_TELEGRAM_ID:
        await update.message.reply_text(
            "⚠️ Admin contact not configured.\n"
            "Please contact support for manual upgrade."
        )
        return

    user = update.effective_user
    photo = update.message.photo[-1]  # Best quality

    # Create inline keyboard for admin
    keyboard = [
        [
            InlineKeyboardButton("✅ Approve", callback_data=f"approve_{user.id}"),
            InlineKeyboardButton("❌ Reject", callback_data=f"reject_{user.id}")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    caption = (
        f"💳 <b>New Upgrade Request</b>\n\n"
        f"👤 User ID: <code>{user.id}</code>\n"
        f"📛 Name: {html.escape(user.first_name or 'Unknown')}\n"
        f"🕐 Time: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    )

    try:
        await context.bot.send_photo(
            chat_id=Config.ADMIN_TELEGRAM_ID,
            photo=photo.file_id,
            caption=caption,
            parse_mode='HTML',
            reply_markup=reply_markup
        )

        # Store pending request
        add_pending_request(user.id, user.first_name or "Unknown", photo.file_id)

        await update.message.reply_text(
            "✅ Slip received!\n\n"
            "Your request is being reviewed.\n"
            "You'll be notified once approved (usually within 24 hours)."
        )
    except RetryAfter as e:
        await asyncio.sleep(e.retry_after)
        await handle_slip(update, context)
    except Exception as e:
        logger.error(f"Failed to forward slip: {e}")
        await update.message.reply_text(
            "❌ Failed to send slip.\n"
            "Please try again later or contact support."
        )

async def approve_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle approve button click from admin."""
    query = update.callback_query

    # Verify admin
    if not is_admin(query.from_user.id):
        await query.answer("⛔ Unauthorized", show_alert=True)
        return

    # Extract user ID from callback data
    try:
        target_uid = int(query.data.split("_")[1])
    except (IndexError, ValueError):
        await query.answer("❌ Invalid request", show_alert=True)
        return

    await query.answer("Processing...")

    flask_app = context.application.bot_data['flask_app']
    loop = asyncio.get_running_loop()

    success = await loop.run_in_executor(
        None, execute_with_context, flask_app, promote_to_vip_service, target_uid
    )

    if success:
        # Remove from pending
        remove_pending_request(target_uid)

        # Update admin message
        await query.edit_message_caption(
            caption=f"{query.message.caption}\n\n✅ <b>APPROVED</b> by admin",
            parse_mode='HTML'
        )

        # Notify user
        try:
            await context.bot.send_message(
                chat_id=target_uid,
                text=(
                    "🎉 *Congratulations!*\n\n"
                    "Your account has been upgraded to VIP!\n\n"
                    "You now have:\n"
                    "• ♾️ Unlimited URLs\n"
                    "• ✨ Custom aliases\n\n"
                    "Enjoy! 🚀"
                ),
                parse_mode='Markdown'
            )
        except Exception as e:
            logger.warning(f"Could not notify user {target_uid}: {e}")
    else:
        await query.edit_message_caption(
            caption=f"{query.message.caption}\n\n❌ <b>FAILED</b> - User not found",
            parse_mode='HTML'
        )

async def reject_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle reject button click from admin."""
    query = update.callback_query

    # Verify admin
    if not is_admin(query.from_user.id):
        await query.answer("⛔ Unauthorized", show_alert=True)
        return

    # Extract user ID from callback data
    try:
        target_uid = int(query.data.split("_")[1])
    except (IndexError, ValueError):
        await query.answer("❌ Invalid request", show_alert=True)
        return

    # Show reason selection
    keyboard = [
        [InlineKeyboardButton("💳 Invalid slip", callback_data=f"reject_reason_{target_uid}_invalid")],
        [InlineKeyboardButton("💰 Amount incorrect", callback_data=f"reject_reason_{target_uid}_amount")],
        [InlineKeyboardButton("🔍 Cannot verify", callback_data=f"reject_reason_{target_uid}_verify")],
        [InlineKeyboardButton("❌ Other reason", callback_data=f"reject_reason_{target_uid}_other")],
        [InlineKeyboardButton("⬅️ Back", callback_data=f"back_{target_uid}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.answer()
    await query.edit_message_reply_markup(reply_markup=reply_markup)

async def reject_reason_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle rejection with reason."""
    query = update.callback_query

    if not is_admin(query.from_user.id):
        await query.answer("⛔ Unauthorized", show_alert=True)
        return

    # Parse callback: reject_reason_{user_id}_{reason}
    parts = query.data.split("_")
    try:
        target_uid = int(parts[2])
        reason_code = parts[3]
    except (IndexError, ValueError):
        await query.answer("❌ Invalid request", show_alert=True)
        return

    # Map reason codes to messages
    reason_messages = {
        "invalid": "The slip image is invalid or unclear.",
        "amount": "The transfer amount is incorrect.",
        "verify": "We couldn't verify the payment.",
        "other": "Your request could not be approved at this time."
    }
    reason = reason_messages.get(reason_code, "Your request was rejected.")

    await query.answer("Rejecting...")

    # Remove from pending
    remove_pending_request(target_uid)

    # Update admin message
    await query.edit_message_caption(
        caption=f"{query.message.caption}\n\n❌ <b>REJECTED</b>\nReason: {reason}",
        parse_mode='HTML'
    )

    # Notify user
    try:
        await context.bot.send_message(
            chat_id=target_uid,
            text=(
                "❌ *Upgrade Request Declined*\n\n"
                f"Reason: {reason}\n\n"
                "If you believe this is an error, please:\n"
                "1. Make sure your transfer is complete\n"
                "2. Send a clear slip image\n"
                "3. Try again with /upgrade"
            ),
            parse_mode='Markdown'
        )
    except Exception as e:
        logger.warning(f"Could not notify user {target_uid}: {e}")

async def back_to_approve_reject(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle back button to return to approve/reject options."""
    query = update.callback_query

    if not is_admin(query.from_user.id):
        await query.answer("⛔ Unauthorized", show_alert=True)
        return

    try:
        target_uid = int(query.data.split("_")[1])
    except (IndexError, ValueError):
        await query.answer("❌ Invalid request", show_alert=True)
        return

    keyboard = [
        [
            InlineKeyboardButton("✅ Approve", callback_data=f"approve_{target_uid}"),
            InlineKeyboardButton("❌ Reject", callback_data=f"reject_{target_uid}")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.answer()
    await query.edit_message_reply_markup(reply_markup=reply_markup)

async def approve(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Command-based approve (still works as backup)."""
    user_id = update.effective_user.id
    flask_app = context.application.bot_data['flask_app']

    if not is_admin(user_id):
        return

    try:
        target_uid = int(context.args[0])
    except (IndexError, ValueError):
        await update.message.reply_text(
            "Usage: `/approve <telegram_id>`\n"
            "Example: `/approve 123456789`",
            parse_mode='Markdown'
        )
        return

    await send_typing_action(update)

    loop = asyncio.get_running_loop()
    success = await loop.run_in_executor(None, execute_with_context, flask_app, promote_to_vip_service, target_uid)

    if success:
        remove_pending_request(target_uid)
        await update.message.reply_text(f"✅ User `{target_uid}` promoted to VIP!", parse_mode='Markdown')

        try:
            await context.bot.send_message(
                chat_id=target_uid,
                text=(
                    "🎉 *Congratulations!*\n\n"
                    "Your account has been upgraded to VIP!\n\n"
                    "You now have:\n"
                    "• ♾️ Unlimited URLs\n"
                    "• ✨ Custom aliases\n\n"
                    "Enjoy! 🚀"
                ),
                parse_mode='Markdown'
            )
        except Exception as e:
            await update.message.reply_text(f"⚠️ Promoted, but couldn't notify user: {e}")
    else:
        await update.message.reply_text(
            f"❌ Failed to promote user `{target_uid}`.\n"
            "User might not exist or hasn't used the bot yet.",
            parse_mode='Markdown'
        )

async def reject(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Command-based reject."""
    user_id = update.effective_user.id

    if not is_admin(user_id):
        return

    try:
        target_uid = int(context.args[0])
        reason = " ".join(context.args[1:]) if len(context.args) > 1 else "No reason provided."
    except (IndexError, ValueError):
        await update.message.reply_text(
            "Usage: `/reject <telegram_id> [reason]`\n"
            "Example: `/reject 123456789 Invalid slip`",
            parse_mode='Markdown'
        )
        return

    remove_pending_request(target_uid)
    await update.message.reply_text(f"❌ User `{target_uid}` rejected.", parse_mode='Markdown')

    try:
        await context.bot.send_message(
            chat_id=target_uid,
            text=(
                "❌ *Upgrade Request Declined*\n\n"
                f"Reason: {reason}\n\n"
                "If you believe this is an error, please:\n"
                "1. Make sure your transfer is complete\n"
                "2. Send a clear slip image\n"
                "3. Try again with /upgrade"
            ),
            parse_mode='Markdown'
        )
    except Exception as e:
        await update.message.reply_text(f"⚠️ Rejected, but couldn't notify user: {e}")

async def pending(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show pending upgrade requests (admin only)."""
    user_id = update.effective_user.id

    if not is_admin(user_id):
        return

    requests = get_pending_requests()

    if not requests:
        await update.message.reply_text("📭 No pending upgrade requests.")
        return

    msg = "<b>📋 Pending Upgrade Requests:</b>\n\n"
    for uid, data in requests.items():
        time_str = data['timestamp'].strftime('%Y-%m-%d %H:%M')
        msg += (
            f"👤 <b>{html.escape(data['name'])}</b>\n"
            f"   ID: <code>{uid}</code>\n"
            f"   🕐 {time_str}\n"
            f"   → /approve {uid}\n"
            f"   → /reject {uid}\n\n"
        )

    msg += f"<i>Total: {len(requests)} pending</i>"
    await update.message.reply_text(msg, parse_mode='HTML')

# --- URL Handlers ---

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if not check_rate_limit(user_id):
        await update.message.reply_text("⏳ Please wait a moment before sending another request.")
        return

    text = update.message.text.strip()
    if not text:
        return

    parts = text.split(maxsplit=1)
    target_url = parts[0]
    custom_alias = parts[1] if len(parts) > 1 else None

    # Quick validation before showing typing
    if not is_valid_url(target_url) and not target_url.startswith(('http://', 'https://')):
        if not is_valid_url('https://' + target_url):
            await update.message.reply_text(
                "⚠️ That doesn't look like a valid URL.\n\n"
                "Please send a URL like:\n"
                "`https://example.com`",
                parse_mode='Markdown'
            )
            return

    flask_app = context.application.bot_data['flask_app']

    await send_typing_action(update)

    loop = asyncio.get_running_loop()

    try:
        result = await loop.run_in_executor(
            None, execute_with_context, flask_app, shorten_url_service, user_id, target_url, custom_alias
        )
    except Exception as e:
        logger.error(f"Error in shorten service: {e}")
        await update.message.reply_text("❌ An error occurred. Please try again later.")
        return

    if "error" in result:
        error_type = result.get('error', '')
        message = result.get('message', 'Unknown error')

        if error_type == "Limit Exceeded":
            icon = "📊"
        elif error_type == "Invalid URL":
            icon = "🔗"
        elif error_type == "VIP Feature":
            icon = "⭐"
        elif error_type == "Conflict":
            icon = "⚠️"
        else:
            icon = "❌"

        await update.message.reply_text(f"{icon} {message}")
    else:
        short_url = result.get('url')
        qr_code_data = result.get('qr_code')

        if short_url:
            msg_text = f"✅ *Shortened successfully!*\n\n🔗 {short_url}"

            if qr_code_data and "base64," in qr_code_data:
                try:
                    base64_str = qr_code_data.split("base64,")[1]
                    img_data = base64.b64decode(base64_str)
                    photo_file = io.BytesIO(img_data)
                    photo_file.name = "qr_code.png"

                    await update.message.reply_photo(photo=photo_file, caption=msg_text, parse_mode='Markdown')
                except Exception as e:
                    logger.error(f"Failed to send QR code: {e}")
                    await update.message.reply_text(msg_text, parse_mode='Markdown')
            else:
                await update.message.reply_text(msg_text, parse_mode='Markdown')
        else:
            await update.message.reply_text("❌ Failed to shorten URL. Please try again.")

async def list_urls(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if not check_rate_limit(user_id):
        return

    flask_app = context.application.bot_data['flask_app']

    await send_typing_action(update)

    loop = asyncio.get_running_loop()
    urls = await loop.run_in_executor(None, execute_with_context, flask_app, list_urls_service, user_id)

    if not urls:
        await update.message.reply_text(
            "📭 You haven't shortened any URLs yet.\n\n"
            "Send me a URL to get started!"
        )
        return

    urls = urls[-10:]
    urls.reverse()

    msg = "<b>📋 Your Recent URLs:</b>\n\n"
    for i, item in enumerate(urls, 1):
        orig = item.get('target_url', '???')
        short = item.get('url', '???')
        key = item.get('key')
        clicks = item.get('clicks', 0)

        if 'url' not in item and key:
            short = f"{Config.SHORTENER_HOST}/{key}"

        secret = item.get('secret_key') or 'unknown'

        if len(orig) > 40:
            orig_display = orig[:37] + "..."
        else:
            orig_display = orig

        safe_orig = html.escape(orig_display)
        safe_short = html.escape(short)
        safe_secret = html.escape(secret)

        msg += (
            f"<b>{i}.</b> <a href='{safe_short}'>{safe_short}</a>\n"
            f"   └ {safe_orig}\n"
            f"   └ 📊 {clicks} clicks\n"
            f"   └ 🗑 <code>/delete {safe_secret}</code>\n\n"
        )

    await update.message.reply_text(msg, parse_mode='HTML', disable_web_page_preview=True)

async def delete_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if not check_rate_limit(user_id):
        return

    flask_app = context.application.bot_data['flask_app']

    try:
        secret_key = context.args[0]
    except (IndexError, ValueError):
        await update.message.reply_text(
            "Usage: `/delete <secret_key>`\n\n"
            "Use /list to find your secret keys.",
            parse_mode='Markdown'
        )
        return

    await send_typing_action(update)

    loop = asyncio.get_running_loop()
    result = await loop.run_in_executor(None, execute_with_context, flask_app, delete_url_service, user_id, secret_key)

    if result['success']:
        await update.message.reply_text("✅ URL deleted successfully!")
    else:
        await update.message.reply_text(f"❌ {result['message']}")

# --- Handler Setup ---

def setup_handlers(application: Application):
    """Register all handlers with the application."""
    # Command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("upgrade", upgrade))
    application.add_handler(CommandHandler("approve", approve))
    application.add_handler(CommandHandler("reject", reject))
    application.add_handler(CommandHandler("pending", pending))
    application.add_handler(CommandHandler("list", list_urls))
    application.add_handler(CommandHandler("delete", delete_url))

    # Callback handlers (for inline buttons)
    application.add_handler(CallbackQueryHandler(cancel_upgrade_callback, pattern="^cancel_upgrade$"))
    application.add_handler(CallbackQueryHandler(approve_callback, pattern="^approve_\\d+$"))
    application.add_handler(CallbackQueryHandler(reject_callback, pattern="^reject_\\d+$"))
    application.add_handler(CallbackQueryHandler(reject_reason_callback, pattern="^reject_reason_\\d+_"))
    application.add_handler(CallbackQueryHandler(back_to_approve_reject, pattern="^back_\\d+$"))

    # Photo handler (for slips)
    application.add_handler(MessageHandler(filters.PHOTO, handle_slip))

    # Text message handler (for URLs)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

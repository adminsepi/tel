import os
import subprocess
import time
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
import requests

# تنظیمات هاردکد
TELEGRAM_TOKEN = "7977369475:AAElCnt-uMl5XtrONdIVILTvRcyRQQqr2ik"
UPLOAD_FOLDER = "uploads"
SIGNED_FOLDER = "signed"
ADMIN_ID = 7934946400
CHANNELS = [
    {"name": "کانال پشتیبانی #سالس_استرول", "url": "https://t.me/salesestrol", "chat_id": -1002721560354},
    {"name": "کانال اختصاصی■VIP■", "url": "https://t.me/+XgPHewjiAdc1ZmI8", "chat_id": -1002337225404},
    {"name": "گروه چت و مشورت🔞", "url": "https://t.me/+EKFD_UpMaEpjODc0", "chat_id": -1002778968668}
]
KEYSTORE_PATH = "/app/my.keystore"
KEYSTORE_PASSWORD = "123456"
KEY_ALIAS = "mykey"
KEY_PASSWORD = "123456"
sign_queue = []

# ایجاد پوشه‌ها
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(SIGNED_FOLDER, exist_ok=True)

def is_real_member(user_id):
    for channel in CHANNELS:
        try:
            response = requests.get(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getChatMember?chat_id={channel['chat_id']}&user_id={user_id}").json()
            if not response.get('ok') or response['result']['status'] not in ['member', 'administrator', 'creator']:
                return False
        except:
            return False
    return True

def sign_apk(input_path, output_path):
    try:
        cmd = [
            "jarsigner", "-keystore", KEYSTORE_PATH,
            "-storepass", KEYSTORE_PASSWORD,
            "-keypass", KEY_PASSWORD,
            "-signedjar", output_path, input_path, KEY_ALIAS
        ]
        subprocess.run(cmd, check=True, capture_output=True, text=True)
        return True, None
    except subprocess.CalledProcessError as e:
        return False, f"خطا در امضا: {e.stderr}"
    except Exception as e:
        return False, f"خطای عمومی: {str(e)}"

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    join_buttons = [[{"text": f"عضویت در {ch['name']}", "url": ch['url']}] for ch in CHANNELS]
    join_buttons.append([{"text": "تایید عضویت ✅", "callback_data": "verify_me"}])
    await update.message.reply_html(
        """💥 پیام ادمین <b>#سالس_استرول</b>: 💥
🆔️ PV SUPPORTER: <b>@RealSalesestrol</b>
🔐 برای امضای فایل APK، لطفاً در کانال‌ها و گروه زیر عضو شوید:""",
        reply_markup={"inline_keyboard": join_buttons}
    )

async def sign_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if is_real_member(update.message.from_user.id):
        await update.message.reply_html(
            """🖋 لطفاً فایل APK خود را آپلود کنید.
امضا توسط <b>#سالس_استرول</b> با طرح‌های v2 و v3 انجام خواهد شد."""
        )
    else:
        failed = [ch['name'] for ch in CHANNELS if not is_real_member(update.message.from_user.id)]
        await update.message.reply_html(
            f"""⚠️ شما هنوز در موارد زیر عضو نشده‌اید:
{', '.join(failed)}

لطفاً ابتدا در کانال‌ها و گروه <b>#سالس_استرول</b> عضو شوید و دوباره تلاش کنید.""",
            reply_markup={"inline_keyboard": [
                [{"text": "عضویت", "url": CHANNELS[0]['url']}],
                [{"text": "تلاش مجدد", "callback_data": "verify_me"}]
            ]}
        )

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    file = update.message.document
    file_name = file.file_name
    mime_type = file.mime_type
    file_size_kb = file.file_size / 1024

    if not (mime_type == 'application/vnd.android.package-archive' or file_name.lower().endswith('.apk')):
        await update.message.reply_text(f"⚠️ فایل {file_name} یک APK معتبر نیست! لطفاً فایل APK آپلود کنید.")
        return

    if file_size_kb > 50 * 1024:
        await update.message.reply_text("⚠️ فایل APK خیلی بزرگه! حداکثر حجم مجاز 50 مگابایته.")
        return

    if not is_real_member(update.message.from_user.id):
        failed = [ch['name'] for ch in CHANNELS if not is_real_member(update.message.from_user.id)]
        await update.message.reply_html(
            f"""⚠️ شما هنوز در موارد زیر عضو نشده‌اید:
{', '.join(failed)}

لطفاً ابتدا در کانال‌ها و گروه <b>#سالس_استرول</b> عضو شوید.""",
            reply_markup={"inline_keyboard": [
                [{"text": "عضویت", "url": CHANNELS[0]['url']}],
                [{"text": "تلاش مجدد", "callback_data": "verify_me"}]
            ]}
        )
        return

    file_id = file.file_id
    file_url = await context.bot.get_file_url(file_id)
    input_path = os.path.join(UPLOAD_FOLDER, file_name)
    output_path = os.path.join(SIGNED_FOLDER, f"signed_{file_name}")

    with open(input_path, 'wb') as f:
        f.write(requests.get(file_url).content)

    sign_queue.append({"user_id": update.message.from_user.id, "chat_id": update.message.chat_id, "file_name": file_name})
    queue_pos = len(sign_queue)
    est_time = queue_pos * 30 // 60

    await update.message.reply_html(
        f"""✅ فایل APK شما ({file_name}) دریافت شد!
موقعیت شما در صف: {queue_pos}
تخمین زمان امضا: حدود {est_time} دقیقه
لطفاً صبر کنید..."""
    )

    if queue_pos == 1:
        while sign_queue:
            current = sign_queue[0]
            success, error = sign_apk(input_path, output_path)
            if success:
                with open(output_path, 'rb') as f:
                    await context.bot.send_document(
                        current["chat_id"],
                        f,
                        caption=f"""✅ فایل APK شما با موفقیت امضا شد (v2+v3، سازگار با اندروید 7.0+)!
امضا توسط <b>#سالس_استرول</b> | <b>@RealSalesestrol</b>""",
                        parse_mode='HTML'
                    )
                os.remove(input_path)
                os.remove(output_path)
            else:
                await context.bot.send_message(current["chat_id"], f"❌ خطا در امضای فایل: {error}")
            sign_queue.pop(0)
            time.sleep(1)  # جلوگیری از بار اضافی

async def verify_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if is_real_member(query.from_user.id):
        await query.edit_message_text(
            """🎉 عضویت شما تأیید شد!
برای امضای فایل APK، از دستور /sign استفاده کنید و سپس فایل APK خود را آپلود کنید.
مدیریت: <b>#سالس_استرول</b> | <b>@RealSalesestrol</b>""",
            parse_mode='HTML'
        )
    else:
        failed = [ch['name'] for ch in CHANNELS if not is_real_member(query.from_user.id)]
        await query.edit_message_text(
            f"""⚠️ شما هنوز در موارد زیر عضو نشده‌اید:
{', '.join(failed)}

لطفاً ابتدا در کانال‌ها و گروه <b>#سالس_استرول</b> عضو شوید و دوباره تلاش کنید.""",
            reply_markup={"inline_keyboard": [
                [{"text": "عضویت", "url": CHANNELS[0]['url']}],
                [{"text": "تلاش مجدد", "callback_data": "verify_me"}]
            ]}
        )

def main():
    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("sign", sign_command))
    application.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    application.add_handler(CallbackQueryHandler(verify_callback, pattern="verify_me"))

    application.run_polling()

if __name__ == '__main__':
    main()

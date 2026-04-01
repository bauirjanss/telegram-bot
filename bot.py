import csv
import datetime
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler

# --------- SOZLAMALAR ---------
TOKEN = "8388067635:AAEYYfJT0-RZ3SUZhrB8TL8kbagNzU3IO1g"
ADMIN_ID = 5475441465
CSV_FILE = "buyurtmalar.csv"

CARD = "8600 1234 5678 9999"
NAME = "AZAMAT"
USLUGA = 5000
# -----------------------------

def save_order(order_id, pozivnoy, user_info, car, phone, amount, status):
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(CSV_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([order_id, now, pozivnoy, user_info, car, phone, amount, status])

def get_next_order_id():
    try:
        with open(CSV_FILE, "r", encoding="utf-8") as f:
            return len(list(csv.reader(f))) + 1
    except:
        return 1

# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Format:\nPozivnoy, Mashina, Telefon, Summa\n\n"
        "Misol:\nAlpha, 01A123AA, +998901234567, 15000"
    )

# --------- ASOSIY LOGIKA ---------
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    # USER BOSILADIGAN LINK
    name = user.first_name if user.first_name else ""
    last = user.last_name if user.last_name else ""
    full_name = f"{name} {last}".strip()

    user_info = f"<a href='tg://user?id={user.id}'>{full_name}</a>"

    # --------- CHECK (RASМ) ---------
    if update.message.photo:
        order_id = get_next_order_id() - 1

        with open(CSV_FILE, "r", encoding="utf-8") as f:
            rows = list(csv.reader(f))
            last_row = rows[-1]

            pozivnoy = last_row[2]
            car = last_row[4]
            phone = last_row[5]

        keyboard = [
            [
                InlineKeyboardButton("✅ Qabul qilindi", callback_data=f"accept_{order_id}_{user.id}"),
                InlineKeyboardButton("❌ Qabul qilinmadi", callback_data=f"reject_{order_id}_{user.id}")
            ]
        ]

        await context.bot.send_photo(
            chat_id=ADMIN_ID,
            photo=update.message.photo[-1].file_id,
            caption=(
                f"🕵️‍♂️ Pozivnoy: {pozivnoy}\n"
                f"👤 User: {user_info}\n"
                f"🚗 Mashina: {car}\n"
                f"📞 Telefon: {phone}\n"
                f"Check tekshirilyapti"
            ),
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

        await update.message.reply_text("⏳ Check yuborildi, tekshirilmoqda")
        return

    # --------- BUYURTMA ---------
    parts = update.message.text.split(",")

    if len(parts) != 4:
        await update.message.reply_text("❌ Format xato")
        return

    pozivnoy = parts[0].strip()
    car = parts[1].strip()
    phone = parts[2].strip()

    try:
        amount = int(parts[3].strip())
    except:
        await update.message.reply_text("❌ Summa xato")
        return

    total = amount + USLUGA
    order_id = get_next_order_id()

    save_order(order_id, pozivnoy, user_info, car, phone, total, "Kutilmoqda")

    await update.message.reply_text(
        f"✅ Buyurtma qabul qilindi\n"
        f"ID: {order_id}\n"
        f"🕵️‍♂️ Pozivnoy: {pozivnoy}\n"
        f"🚗 Mashina: {car}\n"
        f"📞 Telefon: {phone}\n\n"
        f"💰 Summa: {amount}\n"
        f"💰 Usluga: {USLUGA}\n"
        f"💰 Jami: {total}\n\n"
        f"💳 Karta: {CARD}\n"
        f"Ism: {NAME}\n\n"
        f"📸 Check yuboring"
    )

# --------- TUGMALAR ---------
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data.split("_")
    action = data[0]
    order_id = data[1]
    user_id = data[2]

    with open(CSV_FILE, "r", encoding="utf-8") as f:
        rows = list(csv.reader(f))

    for i in range(len(rows)):
        if rows[i][0] == order_id:
            if action == "accept":
                rows[i][7] = "Tasdiqlandi"
            else:
                rows[i][7] = "Rad etildi"
            break

    with open(CSV_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerows(rows)

    if action == "accept":
        await context.bot.send_message(chat_id=user_id, text="✅ To‘lov tasdiqlandi")
        await query.edit_message_caption(caption=query.message.caption + "\n✅ Qabul qilindi", parse_mode="HTML")
    else:
        await context.bot.send_message(chat_id=user_id, text="❌ To‘lov rad etildi")
        await query.edit_message_caption(caption=query.message.caption + "\n❌ Rad etildi", parse_mode="HTML")

# --------- MAIN ---------
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(MessageHandler(filters.PHOTO, handle_message))
    app.add_handler(CallbackQueryHandler(button))

    print("Bot ishlayapti...")
    app.run_polling()

if __name__ == "__main__":
    main()

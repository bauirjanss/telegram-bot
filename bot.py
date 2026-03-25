import csv
import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler

# ----------------- SOZLAMALAR -----------------
TOKEN = "8388067635:AAEYYfJT0-RZ3SUZhrB8TL8kbagNzU3IO1g"
ADMIN_ID = 5475441465
CSV_FILE = "buyurtmalar.csv"
CARD = "9860 0824 7009 8912"
NAME = "BAYRAMBAY JUGINISOV"
SERVICE_FEE = 5000
# ----------------------------------------------

# Buyurtma saqlash
def save_order(order_id, pozivnoy, car, phone, amount, status):
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(CSV_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([order_id, now, pozivnoy, car, phone, amount, status])

def get_next_order_id():
    try:
        with open(CSV_FILE, "r", encoding="utf-8") as f:
            rows = list(csv.reader(f))
            return len(rows) + 1
    except:
        return 1

# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Salom! Buyurtma berish format: Pozivnoy, Mashina, Telefon, Summa\n"
        "Masalan:\n1234, 01A123AA, +998901234567, 15000"
    )

# /stats
async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    try:
        with open(CSV_FILE, "r", encoding="utf-8") as f:
            rows = list(csv.reader(f))
            total_orders = len(rows)
            total_profit = sum([int(row[5]) for row in rows if row[6] == "Tasdiqlangan"])
        await update.message.reply_text(
            f"📊 Buyurtmalar soni: {total_orders}\n💰 Foyda: {total_profit} so‘m"
        )
    except:
        await update.message.reply_text("Hozircha buyurtma yo‘q")

# /last
async def last(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    try:
        with open(CSV_FILE, "r", encoding="utf-8") as f:
            rows = list(csv.reader(f))
            last_rows = rows[-5:]
            msg = "📝 Oxirgi buyurtmalar:\n"
            for row in last_rows:
                msg += f"ID:{row[0]} | Pozivnoy:{row[2]} | Mashina:{row[3]} | Telefon:{row[4]} | Summa:{row[5]} | Status:{row[6]}\n"
        await update.message.reply_text(msg)
    except:
        await update.message.reply_text("Hozircha buyurtma yo‘q")

# Xabarlar
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    # Agar check (rasm) yuborsa
    if update.message.photo:
        order_id = get_next_order_id() - 1

        with open(CSV_FILE, "r", encoding="utf-8") as f:
            rows = list(csv.reader(f))
            last_order = rows[-1]
            pozivnoy = last_order[2]
            car = last_order[3]
            phone = last_order[4]

        keyboard = [
            [InlineKeyboardButton("✅ Qabul qilindi", callback_data=f"accept_{order_id}_{user_id}"),
             InlineKeyboardButton("❌ Qabul qilinmadi", callback_data=f"reject_{order_id}_{user_id}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await context.bot.send_photo(
            chat_id=ADMIN_ID,
            photo=update.message.photo[-1].file_id,
            caption=f"🕵️‍♂️ Pozivnoy: {pozivnoy}\n🚗 Mashina: {car}\n📞 Telefon: {phone}\nCheck tekshirilyapti",
            reply_markup=reply_markup
        )

        await update.message.reply_text("Check qabul qilindi ✅ Tekshirilmoqda")
        return

    # Matn (buyurtma)
    text = update.message.text
    parts = text.split(",")

    if len(parts) != 4:
        await update.message.reply_text("Xato format! Pozivnoy, Mashina, Telefon, Summa")
        return

    pozivnoy = parts[0].strip()
    car = parts[1].strip()
    phone = parts[2].strip()

    try:
        amount = int(parts[3].strip())
    except:
        await update.message.reply_text("Summa raqam bo‘lishi kerak")
        return

    total = amount + SERVICE_FEE
    order_id = get_next_order_id()

    save_order(order_id, pozivnoy, car, phone, total, "To'lov kutilmoqda")

    await update.message.reply_text(
        f"✅ Buyurtma qabul qilindi\n"
        f"ID: {order_id}\n"
        f"👤 Pozivnoy: {pozivnoy}\n"
        f"🚗 Mashina: {car}\n"
        f"📞 Telefon: {phone}\n"
        f"💰 Summa: {amount}\n"
        f"💸 Xizmat haqi: {SERVICE_FEE}\n"
        f"💳 Jami: {total}\n\n"
        f"💳 Karta: {CARD}\nIsm: {NAME}\n\n"
        f"❗️ To‘lovdan keyin screenshot yuboring"
    )

# Tugmalar
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data.split("_")
    action = data[0]
    order_id = data[1]
    user_id = data[2]

    try:
        with open(CSV_FILE, "r", encoding="utf-8") as f:
            rows = list(csv.reader(f))

        for i in range(len(rows)):
            if rows[i][0] == order_id:
                if action == "accept":
                    rows[i][6] = "Tasdiqlangan"
                else:
                    rows[i][6] = "Rad etilgan"
                break

        with open(CSV_FILE, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerows(rows)

    except Exception as e:
        print("Xato:", e)
        return

    if action == "accept":
        await context.bot.send_message(chat_id=user_id, text="✅ Buyurtmangiz qabul qilindi")
        await query.edit_message_caption(caption=query.message.caption + "\n✅ Qabul qilindi")
    else:
        await context.bot.send_message(chat_id=user_id, text="❌ Buyurtma rad etildi")
        await query.edit_message_caption(caption=query.message.caption + "\n❌ Qabul qilinmadi")

# MAIN
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("last", last))

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(MessageHandler(filters.PHOTO, handle_message))
    app.add_handler(CallbackQueryHandler(button))

    print("Bot ishlayapti...")
    app.run_polling()

if __name__ == "__main__":
    main()

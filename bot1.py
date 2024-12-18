import telebot
import random
import string
from telebot import types

# Bot token and configuration
TOKEN = "7825698482:AAGd7OGEk01y00GL2QH-LepKPLEQRCS82a0"
CHANNEL_ID = '-1002331286725'  # Subscription channel ID
CHANNEL_LINK = "https://t.me/linebet_bel3arabi"
GROUP_ID = '-1002499725054'  # Group ID to send confirmed requests
AFFILIATE_BOT_LINK = "https://t.me/Lb_ENG_AFF_P_bot"  # Affiliate bot link

# Initialize bot
bot = telebot.TeleBot(TOKEN)
user_data = {}  # Dictionary to store user data
request_to_user = {}  # Map request IDs to user IDs
used_request_ids = set()  # Set to track used request IDs

# Generate a unique request ID
def generate_request_id():
    while True:
        request_id = "#M" + ''.join(random.choices(string.digits, k=7))
        if request_id not in used_request_ids:
            used_request_ids.add(request_id)
            return request_id

# Start command: Welcome message
@bot.message_handler(commands=['start'])
def welcome_message(message):
    bot.send_message(
        message.chat.id,
        f"مرحبًا! لتقديم طلب بخصوص الإيداع أو السحب، يرجى الاشتراك في القناة عبر الرابط التالي:\n{CHANNEL_LINK}\nبعد الاشتراك، اضغط /verify للتحقق من اشتراكك والوصول إلى كافة وظائف البوت."
    )

# Verify if the user is subscribed to the channel
@bot.message_handler(commands=['verify'])
def verify_subscription(message):
    try:
        user_status = bot.get_chat_member(CHANNEL_ID, message.from_user.id).status
        if user_status in ['member', 'administrator', 'creator']:
            bot.send_message(message.chat.id, "تم التحقق من اشتراكك بنجاح! يمكنك الآن متابعة استخدام البوت.")
            request_account_id(message)
        else:
            bot.send_message(
                message.chat.id,
                f"يرجى الاشتراك في القناة عبر الرابط التالي:\n{CHANNEL_LINK}\nثم اضغط /verify بعد الاشتراك."
            )
    except telebot.apihelper.ApiTelegramException as e:
        bot.send_message(
            message.chat.id,
            "حدث خطأ أثناء التحقق من الاشتراك. يرجى التأكد من صلاحيات البوت وحاول مرة أخرى."
        )
        print(f"Error verifying subscription: {e}")

# Helper function to save data and proceed to the next step
def save_and_proceed(message, field, next_step):
    if message.text:
        user_data[message.from_user.id][field] = message.text
        next_step(message)
    else:
        bot.send_message(message.chat.id, "يرجى إدخال قيمة صحيحة.")
        next_step(message)

# Step-by-step data collection
def request_account_id(message):
    msg = bot.send_message(message.chat.id, "يرجى إدخال رقم تعريف الحساب الخاص بك (مثال: 1234567)")
    bot.register_next_step_handler(msg, validate_account_id)

def validate_account_id(message):
    if message.text.isdigit():
        user_data[message.from_user.id] = {'account_id': message.text}
        request_amount(message)
    else:
        bot.send_message(message.chat.id, "يرجى إدخال رقم حساب صحيح.")
        request_account_id(message)

def request_amount(message):
    msg = bot.send_message(message.chat.id, "أدخل مبلغ التحويل و العملة (مثال: 100 USD)")
    bot.register_next_step_handler(msg, lambda m: save_and_proceed(m, 'amount', request_transaction_date))

def request_transaction_date(message):
    msg = bot.send_message(message.chat.id, "أدخل تاريخ المعاملة (بصيغة YYYY-MM-DD، مثال: 2024-01-31)")
    bot.register_next_step_handler(msg, lambda m: save_and_proceed(m, 'transaction_date', request_bank))

def request_bank(message):
    msg = bot.send_message(message.chat.id, "أدخل اسم البنك و البلد (مثال: المغرب CIH)")
    bot.register_next_step_handler(msg, lambda m: save_and_proceed(m, 'bank', request_rib))

def request_rib(message):
    msg = bot.send_message(message.chat.id, "أدخل تفاصيل RIB أو الهاتف أو الحساب المستخدم للتحويل (مثال: 1234567)")
    bot.register_next_step_handler(msg, lambda m: save_and_proceed(m, 'rib', request_transaction_id))

def request_transaction_id(message):
    msg = bot.send_message(message.chat.id, "أدخل رقم تعريف المعاملة (Transaction ID) (مثال: 123456789)")
    bot.register_next_step_handler(msg, lambda m: save_and_proceed(m, 'transaction_id', request_email))

def request_email(message):
    msg = bot.send_message(message.chat.id, "أدخل بريدك الإلكتروني (مثال: user@example.com)")
    bot.register_next_step_handler(msg, lambda m: save_and_proceed(m, 'email', request_full_name))

def request_full_name(message):
    msg = bot.send_message(message.chat.id, "أدخل اسمك الكامل (مثال: أحمد علي)")
    bot.register_next_step_handler(msg, lambda m: save_and_proceed(m, 'full_name', request_request_type))

def request_request_type(message):
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    markup.add("إيداع", "سحب")
    msg = bot.send_message(message.chat.id, "هل هذا الطلب متعلق بالإيداع أم السحب؟", reply_markup=markup)
    bot.register_next_step_handler(msg, validate_request_type)

def validate_request_type(message):
    if message.text in ["إيداع", "سحب"]:
        user_data[message.from_user.id]['request_type'] = message.text
        request_proof(message)
    else:
        bot.send_message(message.chat.id, "يرجى اختيار إيداع أو سحب.")
        request_request_type(message)

def request_proof(message):
    msg = bot.send_message(message.chat.id, "يرجى تحميل صورة أو فيديو يثبت العملية.")
    bot.register_next_step_handler(msg, handle_proof_upload)

def handle_proof_upload(message):
    if message.content_type in ['photo', 'video']:
        user_data[message.from_user.id]['proof'] = message.photo[-1].file_id if message.content_type == 'photo' else message.video.file_id
        ask_message_for_manager(message)
    else:
        bot.send_message(message.chat.id, "يرجى تحميل صورة أو فيديو يثبت العملية.")
        request_proof(message)

def ask_message_for_manager(message):
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    markup.add("نعم", "لا")
    msg = bot.send_message(message.chat.id, "هل ترغب في إضافة رسالة للمدير؟", reply_markup=markup)
    bot.register_next_step_handler(msg, process_manager_message)

def process_manager_message(message):
    if message.text == "نعم":
        msg = bot.send_message(message.chat.id, "يرجى كتابة رسالتك للمدير:")
        bot.register_next_step_handler(msg, save_manager_message)
    elif message.text == "لا":
        confirm_request(message)
    else:
        bot.send_message(message.chat.id, "يرجى اختيار نعم أو لا.")
        ask_message_for_manager(message)

def save_manager_message(message):
    user_data[message.from_user.id]['manager_message'] = message.text
    confirm_request(message)

# Confirm request details and send to group
def confirm_request(message):
    data = user_data.get(message.from_user.id, {})
    request_id = generate_request_id()
    request_to_user[request_id] = message.from_user.id
    summary = (
        f"طلب جديد من {message.from_user.username} (@{message.from_user.username}) - {message.from_user.first_name} (ID: {message.from_user.id}):\n"
        f"    - رقم الحساب: {data.get('account_id')}\n"
        f"    - مبلغ التحويل: {data.get('amount')}\n"
        f"    - تاريخ المعاملة: {data.get('transaction_date')}\n"
        f"    - البنك: {data.get('bank')}\n"
        f"    - تفاصيل RIB: {data.get('rib')}\n"
        f"    - رقم المعاملة: {data.get('transaction_id')}\n"
        f"    - البريد الإلكتروني: {data.get('email')}\n"
        f"    - الاسم الكامل: {data.get('full_name')}\n"
        f"    - نوع الطلب: {data.get('request_type')}\n"
        f"    - معرف الطلب: {request_id}\n"
    )
    if 'manager_message' in data:
        summary += f"\nرسالة المستخدم للمدير: {data['manager_message']}\n"

    bot.send_message(message.chat.id, f"{summary}\nهل البيانات صحيحة؟", reply_markup=types.ReplyKeyboardMarkup(one_time_keyboard=True).add("نعم", "لا"))
    bot.register_next_step_handler(message, lambda m: finalize_request(m, summary, request_id))

def finalize_request(message, summary, request_id):
    if message.text == "نعم":
        bot.send_message(GROUP_ID, summary)
        proof = user_data[message.from_user.id].get('proof')
        if proof:
            bot.send_photo(GROUP_ID, proof, caption=f"Proof for Request ID: {request_id}")
        bot.send_message(message.chat.id, "تم إرسال طلبك بنجاح إلى الدعم. سيتم الرد عليك قريباً.")
        propose_affiliate_partnership(message)
    else:
        bot.send_message(message.chat.id, "يرجى تصحيح البيانات.")
        request_account_id(message)

def propose_affiliate_partnership(message):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("شراكة تابعة مع Linebet", url=AFFILIATE_BOT_LINK))
    bot.send_message(message.chat.id, "هل ترغب في أن تصبح شريكًا تابعًا لـ Linebet؟", reply_markup=markup)

# Handle manager's reply in the group
@bot.message_handler(commands=['reply'])
def handle_manager_reply(message):
    try:
        parts = message.text.split(' ', 2)
        if len(parts) < 3:
            bot.reply_to(message, "يرجى استخدام التنسيق: /reply [Request ID] [Message]")
            return
        request_id, reply_message = parts[1], parts[2]
        user_id = request_to_user.get(request_id)

        if user_id:
            bot.send_message(user_id, f"رد من المدير على طلبك {request_id}:\n{reply_message}\nيمكنك الرد باستخدام:\n/reply_user {request_id} [Message]")
        else:
            bot.reply_to(message, "لم يتم العثور على معرف الطلب.")
    except Exception as e:
        bot.reply_to(message, f"حدث خطأ أثناء إرسال الرد: {e}")

# Handle user reply to the manager
@bot.message_handler(commands=['reply_user'])
def handle_user_reply(message):
    try:
        parts = message.text.split(' ', 2)
        if len(parts) < 3:
            bot.reply_to(message, "يرجى استخدام التنسيق: /reply_user [Request ID] [Message]")
            return
        request_id, reply_message = parts[1], parts[2]
        bot.send_message(GROUP_ID, f"رد المستخدم على الطلب {request_id}:\n{reply_message}")
    except Exception as e:
        bot.reply_to(message, f"حدث خطأ أثناء إرسال الرد: {e}")

# Start the bot
bot.polling(timeout=60, long_polling_timeout=60)

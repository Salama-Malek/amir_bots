# ====================================================
# IMPORTS AND CONFIGURATION
# ====================================================
import telebot  # Telegram bot API library
import random  # For generating random request IDs
import string  # For working with strings in request IDs
import re  # Regular expressions for data validation
import sqlite3
from datetime import datetime
from telebot import types  # For creating custom Telegram keyboard layouts
import ssl
ssl._create_default_https_context = ssl._create_unverified_context

# To track ongoing conversations between managers and users
ongoing_conversations = {}



# ====================================================
# BOT TOKEN AND CONSTANTS
# ====================================================
TOKEN = "7825698482:AAGd7OGEk01y00GL2QH-LepKPLEQRCS82a0"  # Telegram bot token
CHANNEL_ID = '-1002331286725'  # ID of the subscription channel
CHANNEL_LINK = "https://t.me/linebet_bel3arabi"  # Subscription channel link
GROUP_ID = '-1002499725054'  # ID of the group to send confirmed requests
AFFILIATE_BOT_LINK = "https://t.me/Lb_ENG_AFF_P_bot"  # Affiliate bot link

bot = telebot.TeleBot(TOKEN)  # Initialize the Telegram bot

# ====================================================
# DATABASE INITIALIZATION
# ====================================================
def init_db():
    """Initialize the database and ensure all required tables exist."""
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    # Create user data table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_data (
            user_id INTEGER PRIMARY KEY,
            account_id TEXT,
            amount TEXT,
            currency TEXT,
            transaction_date TEXT,
            bank_name TEXT,
            bank_country TEXT,
            rib TEXT,
            transaction_id TEXT,
            email TEXT,
            full_name TEXT,
            request_type TEXT,
            proof TEXT,
            manager_message TEXT
        )
    ''')
    # Create rate limit table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS rate_limit (
            user_id INTEGER PRIMARY KEY,
            last_request_time TEXT
        )
    ''')
    conn.commit()
    conn.close()

# Initialize the database on startup
init_db()

# ====================================================
# DATABASE FUNCTIONS
# ====================================================
def get_db_connection():
    """Return a new database connection."""
    return sqlite3.connect('bot_data.db')

def save_user_data(user_id, data):
    """Save or update user data in the database."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Extract bank data
    bank_data = data.get('bank', {})
    bank_name = bank_data.get('bank_name', '')
    country = bank_data.get('country', '')

    # Handle 'amount' field correctly
    amount = data.get('amount', {})
    amount_value = amount.get('amount', '')
    currency = amount.get('currency', '')

    # Save data into database
    cursor.execute('''
        INSERT OR REPLACE INTO user_data (
            user_id, account_id, amount, currency, transaction_date,
            bank_name, bank_country, rib, transaction_id, email,
            full_name, request_type, proof, manager_message
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        user_id,
        data.get('account_id', ''),
        amount_value,
        currency,
        data.get('transaction_date', ''),
        bank_name,
        country,
        data.get('rib', ''),
        data.get('transaction_id', ''),
        data.get('email', ''),
        data.get('full_name', ''),
        data.get('request_type', ''),
        data.get('proof', ''),
        data.get('manager_message', '')
    ))
    conn.commit()
    conn.close()



def load_user_data(user_id):
    """Retrieve user data from the database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM user_data WHERE user_id = ?', (user_id,))
    row = cursor.fetchone()
    conn.close()

    if row:
        columns = [column[0] for column in cursor.description]
        user_data = dict(zip(columns, row))

        # Reconstruct 'amount' as a dictionary
        if user_data['amount'] and user_data['currency']:
            user_data['amount'] = {'amount': user_data['amount'], 'currency': user_data['currency']}

        # Reconstruct 'bank' as a dictionary
        if user_data['bank_name'] or user_data['bank_country']:
            user_data['bank'] = {'bank_name': user_data['bank_name'], 'country': user_data['bank_country']}

        return user_data

    return {}



def is_rate_limited(user_id, interval=30):
    """Check if a user is rate-limited based on the interval."""
    now = datetime.now()
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT last_request_time FROM rate_limit WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    if result:
        last_request_time = datetime.fromisoformat(result[0])
        if (now - last_request_time).seconds < interval:
            conn.close()
            return True
    cursor.execute('REPLACE INTO rate_limit (user_id, last_request_time) VALUES (?, ?)', (user_id, now.isoformat()))
    conn.commit()
    conn.close()
    return False

# ====================================================
# HELPER FUNCTIONS
# ====================================================
# To track used request IDs and ensure uniqueness
used_request_ids = set()


def generate_request_id():
    """
    Generate a unique request ID in the format #MXXXXXXX,
    where XXXXXXX is a random 7-digit number.
    Ensures uniqueness by checking against `used_request_ids`.
    """
    while True:
        request_id = "#M" + ''.join(random.choices(string.digits, k=7))
        if request_id not in used_request_ids:
            used_request_ids.add(request_id)
            return request_id


def validate_email(email):
    """
    Validate the format of an email address using regex.
    Returns True if the format is valid, False otherwise.
    """
    pattern = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    return re.match(pattern, email) is not None


def validate_date(date):
    """
    Validate the format of a date (YYYY-MM-DD) using regex.
    Returns True if the format is valid, False otherwise.
    """
    pattern = r'^\d{4}-\d{2}-\d{2}$'
    return re.match(pattern, date) is not None


def save_and_proceed(message, field, next_step, validation_func=None):
    """
    Save user input for a specific field and proceed to the next step.
    If validation fails, prompts the user to try again.
    """
    try:
        if not message.text:
            bot.send_message(message.chat.id, "⚠️ يرجى إدخال قيمة صحيحة.")
            next_step(message)  # Retry the current step
            return

        if validation_func and not validation_func(message.text):
            bot.send_message(message.chat.id, "❌ القيمة المدخلة غير صالحة. يرجى المحاولة مرة أخرى.")
            next_step(message)  # Retry the current step
            return

        if message.from_user.id not in user_data:
            user_data[message.from_user.id] = {}

        user_data[message.from_user.id][field] = message.text
        next_step(message)
    except Exception as e:
        bot.send_message(message.chat.id, "❌ حدث خطأ أثناء معالجة البيانات. يرجى المحاولة مرة أخرى.")
        print(f"Error in save_and_proceed: {e}")



# ====================================================
# BOT COMMAND HANDLERS
# ====================================================
@bot.message_handler(commands=['start'])
def welcome_message(message):
    """
    Handle the /start command.
    Sends a welcome message with instructions for subscribing to the channel.
    """
    bot.send_message(
        message.chat.id,
        (
            "👋 مرحبًا بك!\n"
            "لتقديم طلب بخصوص الإيداع أو السحب، يرجى الاشتراك في القناة عبر الرابط التالي:\n"
            f"{CHANNEL_LINK}\n"
            "بعد الاشتراك، اضغط /verify للتحقق من اشتراكك والوصول إلى كافة وظائف البوت."
        )
    )


@bot.message_handler(commands=['verify'])
def verify_subscription(message):
    """
    Handle the /verify command.
    Verifies if the user is subscribed to the required channel.
    """
    try:
        user_status = bot.get_chat_member(CHANNEL_ID, message.from_user.id).status
        if user_status in ['member', 'administrator', 'creator']:
            bot.send_message(
                message.chat.id,
                "✅ تم التحقق من اشتراكك بنجاح! يمكنك الآن متابعة استخدام البوت."
            )
            request_account_id(message)
        else:
            bot.send_message(
                message.chat.id,
                (
                    "⚠️ لم يتم العثور على اشتراكك.\n"
                    f"يرجى الاشتراك في القناة عبر الرابط التالي:\n{CHANNEL_LINK}\n"
                    "ثم اضغط /verify بعد الاشتراك."
                )
            )
    except Exception as e:
        bot.send_message(
            message.chat.id,
            "❌ حدث خطأ أثناء التحقق من الاشتراك. يرجى المحاولة مرة أخرى لاحقاً."
        )
        print(f"Error verifying subscription: {e}")


# ====================================================
# MANAGER TOOLS
# ====================================================
# Manager command to send a message to a user
@bot.message_handler(commands=['message'])
def message_user_from_manager(message):
    try:
        parts = message.text.split(' ', 2)
        if len(parts) < 3:
            bot.reply_to(message, "❌ يرجى استخدام التنسيق الصحيح:\n/message [User ID] [Message]")
            return
        
        user_id = int(parts[1])
        manager_message = parts[2]

        # Save the conversation context
        ongoing_conversations[user_id] = {
            "manager_id": message.chat.id,
            "manager_message": manager_message
        }

        bot.send_message(
            user_id,
            f"📩 <b>رسالة من الدعم:</b>\n{manager_message}\n\n🔄 يمكنك الرد مباشرةً هنا.",
            parse_mode="HTML"
        )
        bot.reply_to(message, "✅ تم إرسال الرسالة بنجاح إلى المستخدم.")
    except ValueError:
        bot.reply_to(message, "❌ المعرف (User ID) غير صحيح. يرجى إدخال رقم صالح.")
    except telebot.apihelper.ApiTelegramException:
        bot.reply_to(message, "⚠️ لا يمكن إرسال الرسالة. تحقق من أن معرف المستخدم صحيح أو أن المستخدم بدأ المحادثة مع البوت.")
    except Exception as e:
        bot.reply_to(message, f"❌ حدث خطأ أثناء إرسال الرسالة: {e}")



# Handle user replies in ongoing chat
@bot.message_handler(func=lambda message: True, content_types=['text'])
def handle_user_reply(message):
    try:
        if message.chat.id in ongoing_conversations:
            conversation = ongoing_conversations[message.chat.id]
            manager_id = conversation["manager_id"]

            bot.send_message(
                manager_id,
                f"💬 <b>رد من المستخدم</b> @{message.from_user.username} (ID: <code>{message.from_user.id}</code>):\n\n{message.text}",
                parse_mode="HTML"
            )
            bot.send_message(
                message.chat.id,
                "✅ تم إرسال ردك إلى الدعم."
            )
        else:
            bot.send_message(
                message.chat.id,
                "⚠️ لا توجد رسالة حالية للرد عليها. انتظر حتى يصلك رسالة من الدعم."
            )
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ حدث خطأ أثناء إرسال ردك: {e}")

from datetime import datetime
import telebot
from telebot import types
# other necessary imports

# ====================================================
# REQUEST PROCESSING AND VALIDATION
# ====================================================

def request_account_id(message):
    msg = bot.send_message(message.chat.id, "🔢 يرجى إدخال رقم تعريف الحساب الخاص بك (مثال: 1234567)")
    bot.register_next_step_handler(msg, validate_account_id)

def validate_account_id(message):
    if message.text.isdigit():  # Check if the input is a valid number
        user_data = load_user_data(message.from_user.id)  # Load existing data
        user_data['account_id'] = message.text  # Update with new account ID
        save_user_data(message.from_user.id, user_data)  # Save updated data
        request_amount(message)  # Proceed to next step
    else:
        bot.send_message(message.chat.id, "❌ يرجى إدخال رقم حساب صحيح (مثال: 1234567).")
        request_account_id(message)  # Retry the current step

def request_amount(message):
    msg = bot.send_message(message.chat.id, "💰 أدخل مبلغ التحويل و العملة (مثال: 100 USD)")
    bot.register_next_step_handler(msg, validate_amount)

def validate_amount(message):
    try:
        amount, currency = message.text.split()  # Splitting the amount and currency
        float(amount)  # Check if the amount is a valid number
        user_data = load_user_data(message.from_user.id)  # Load existing data
        user_data['amount'] = {'amount': amount, 'currency': currency}  # Store as a dict
        save_user_data(message.from_user.id, user_data)  # Save updated data
        request_transaction_date(message)  # Proceed to next step
    except ValueError:
        bot.send_message(message.chat.id, "❌ يرجى إدخال المبلغ بشكل صحيح (مثال: 100 USD).")
        request_amount(message)  # Retry the current step


def request_transaction_date(message):
    msg = bot.send_message(message.chat.id, "📅 أدخل تاريخ المعاملة (بصيغة YYYY-MM-DD، مثال: 2024-01-31)")
    bot.register_next_step_handler(msg, validate_date)

def validate_date(message):
    try:
        datetime.strptime(message.text, '%Y-%m-%d')  # Validate the date format
        user_data = load_user_data(message.from_user.id)  # Load user data
        user_data['transaction_date'] = message.text  # Update with new transaction date
        save_user_data(message.from_user.id, user_data)  # Save updated data
        request_bank(message)  # Proceed to next step
    except ValueError:
        bot.send_message(message.chat.id, "❌ يرجى إدخال التاريخ بشكل صحيح (بصيغة YYYY-MM-DD).")
        request_transaction_date(message)  # Retry the current step

def request_bank(message):
    msg = bot.send_message(message.chat.id, "🏦 أدخل اسم البنك و البلد (مثال: المغرب CIH)")
    bot.register_next_step_handler(msg, validate_bank)

def validate_bank(message):
    # Split input into words
    bank_data = message.text.split(maxsplit=1)  # Split into bank name and country
    if len(bank_data) == 2:  # Ensure bank name and country are provided
        bank_name, country = bank_data  # Unpack the values
        user_data = load_user_data(message.from_user.id)  # Load existing data
        user_data['bank'] = {'bank_name': bank_name, 'country': country}  # Save as a dictionary
        save_user_data(message.from_user.id, user_data)  # Save updated data
        request_rib(message)  # Proceed to next step
    else:
        bot.send_message(message.chat.id, "❌ يرجى إدخال اسم البنك و البلد بشكل صحيح (مثال: CIH المغرب).")
        request_bank(message)  # Retry current step


def request_rib(message):
    msg = bot.send_message(message.chat.id, "📜 أدخل تفاصيل RIB أو الهاتف أو الحساب المستخدم للتحويل (مثال: 1234567)")
    bot.register_next_step_handler(msg, validate_rib)

def validate_rib(message):
    if message.text.isdigit():  # RIB should be numeric
        user_data = load_user_data(message.from_user.id)  # Load user data
        user_data['rib'] = message.text  # Update RIB
        save_user_data(message.from_user.id, user_data)  # Save updated data
        request_transaction_id(message)  # Proceed to next step
    else:
        bot.send_message(message.chat.id, "❌ يرجى إدخال رقم RIB صحيح.")
        request_rib(message)  # Retry the current step

def request_transaction_id(message):
    msg = bot.send_message(message.chat.id, "🆔 أدخل رقم تعريف المعاملة (Transaction ID) (مثال: 123456789)")
    bot.register_next_step_handler(msg, validate_transaction_id)

def validate_transaction_id(message):
    if message.text.isdigit():  # Transaction ID should be numeric
        user_data = load_user_data(message.from_user.id)  # Load user data
        user_data['transaction_id'] = message.text  # Update transaction ID
        save_user_data(message.from_user.id, user_data)  # Save updated data
        request_email(message)  # Proceed to next step
    else:
        bot.send_message(message.chat.id, "❌ يرجى إدخال رقم تعريف المعاملة بشكل صحيح (مثال: 123456789).")
        request_transaction_id(message)  # Retry the current step

def request_email(message):
    msg = bot.send_message(message.chat.id, "📧 أدخل بريدك الإلكتروني (مثال: user@example.com)")
    bot.register_next_step_handler(msg, validate_email)

def validate_email(message):
    if re.match(r"[^@]+@[^@]+\.[^@]+", message.text):  # Simple email validation
        user_data = load_user_data(message.from_user.id)  # Load user data
        user_data['email'] = message.text  # Update email
        save_user_data(message.from_user.id, user_data)  # Save updated data
        request_full_name(message)  # Proceed to next step
    else:
        bot.send_message(message.chat.id, "❌ يرجى إدخال بريد إلكتروني صالح (مثال: user@example.com).")
        request_email(message)  # Retry the current step

def request_full_name(message):
    msg = bot.send_message(message.chat.id, "👤 أدخل اسمك الكامل (مثال: أحمد علي)")
    bot.register_next_step_handler(msg, validate_full_name)

def validate_full_name(message):
    if len(message.text.split()) >= 2:  # Ensure full name has at least first and last name
        user_data = load_user_data(message.from_user.id)  # Load user data
        user_data['full_name'] = message.text  # Update full name
        save_user_data(message.from_user.id, user_data)  # Save updated data
        request_request_type(message)  # Proceed to next step
    else:
        bot.send_message(message.chat.id, "❌ يرجى إدخال اسمك الكامل (مثال: أحمد علي).")
        request_full_name(message)  # Retry the current step

def request_request_type(message):
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("💵 إيداع", callback_data="type_إيداع"),
        types.InlineKeyboardButton("💸 سحب", callback_data="type_سحب")
    )
    bot.send_message(message.chat.id, "🔄 هل هذا الطلب متعلق بالإيداع أم السحب؟", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("type_"))
def validate_request_type(call):
    request_type = call.data.split("_")[1]
    user_data = load_user_data(call.message.chat.id)  # Load user data
    user_data['request_type'] = request_type  # Update request type
    save_user_data(call.message.chat.id, user_data)  # Save updated data
    request_proof(call.message)

def request_proof(message):
    msg = bot.send_message(message.chat.id, "يرجى تحميل صورة أو فيديو يثبت العملية.")
    bot.register_next_step_handler(msg, handle_proof_upload)

def handle_proof_upload(message):
    try:
        if message.content_type in ['photo', 'video']:
            user_data = load_user_data(message.from_user.id)  # Load user data
            file_id = message.photo[-1].file_id if message.content_type == 'photo' else message.video.file_id
            user_data['proof'] = file_id  # Update proof
            save_user_data(message.from_user.id, user_data)  # Save updated data
            ask_message_for_manager(message)
        else:
            bot.send_message(message.chat.id, "❌ يرجى تحميل صورة أو فيديو يثبت العملية.")
            request_proof(message)  # Retry
    except Exception as e:
        bot.send_message(message.chat.id, "❌ حدث خطأ أثناء تحميل الملف. يرجى المحاولة مرة أخرى.")
        print(f"Error in handle_proof_upload: {e}")
        request_proof(message)  # Retry


def ask_message_for_manager(message):
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("نعم", callback_data="message_yes"),
        types.InlineKeyboardButton("لا", callback_data="message_no")
    )
    bot.send_message(message.chat.id, "هل ترغب في إضافة رسالة للدعم؟", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data in ["message_yes", "message_no"])
def process_manager_message(call):
    if call.data == "message_yes":
        msg = bot.send_message(call.message.chat.id, "يرجى كتابة رسالتك للدعم:")
        bot.register_next_step_handler(msg, save_manager_message)
    elif call.data == "message_no":
        confirm_request(call.message)

def save_manager_message(message):
    user_data = load_user_data(message.from_user.id)  # Load user data
    user_data['manager_message'] = message.text  # Update manager message
    save_user_data(message.from_user.id, user_data)  # Save updated data
    confirm_request(message)  # Proceed to confirmation




# Add a function to confirm the request once everything is validated:
def confirm_request(message):
    bot.send_message(message.chat.id, "✅ تم تقديم طلبك بنجاح!")


    
# ====================================================
# The confirm_request function with added Inline Keyboard Navigation
# ====================================================
def confirm_request(message):
    user_id = message.from_user.id
    data = load_user_data(user_id)  # Load user data from the database
    request_id = generate_request_id()
    bank_name = data.get('bank', {}).get('bank_name', 'غير متوفر')
    country = data.get('bank', {}).get('country', 'غير متوفر')
    summary = (
        f"✅ تم تأكيد الطلب:\n"
        f"    - 👤 المستخدم: {message.from_user.first_name}\n"
        f"    - 🆔 معرف المستخدم: {user_id}\n"
        f"    - 🔗 اسم المستخدم: @{message.from_user.username if message.from_user.username else 'لا يوجد'}\n"
        f"    - 🔢 الحساب: {data.get('account_id', 'غير متوفر')}\n"
        f"    - 💰 المبلغ: {data.get('amount', {}).get('amount', 'غير متوفر')} {data.get('amount', {}).get('currency', '')}\n"
        f"    - 🏦 البنك: {bank_name} ({country})\n"
        f"    - 📜 RIB: {data.get('rib', 'غير متوفر')}\n"
        f"    - 🆔 المعاملة: {data.get('transaction_id', 'غير متوفر')}\n"
        f"    - 📧 البريد: {data.get('email', 'غير متوفر')}\n"
        f"    - 👤 الاسم: {data.get('full_name', 'غير متوفر')}\n"
        f"    - 🔄 النوع: {data.get('request_type', 'غير متوفر')}\n"
        f"    - 📝 الطلب: <code>{request_id}</code>\n"
    )
    if 'manager_message' in data:
        summary += f"💬 رسالة المستخدم إلى الدعم: <code>{data['manager_message']}</code>"

    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("✔️ نعم", callback_data=f"confirm_yes_{request_id}"),
        types.InlineKeyboardButton("❌ لا", callback_data=f"confirm_no_{request_id}")
    )

    bot.send_message(message.chat.id, summary, reply_markup=markup, parse_mode="HTML")





@bot.callback_query_handler(func=lambda call: call.data.startswith("confirm_"))
def handle_confirmation(call):
    action, request_id = call.data.split("_")[1:3]
    user_id = call.message.chat.id
    data = load_user_data(user_id)  # Load user data from the database

    if action == "yes":
        confirmation_message = (
            f"✅ تم تأكيد الطلب:\n"
            f"    - 👤 المستخدم: {call.message.chat.first_name}\n"
            f"    - 🆔 معرف المستخدم: {user_id}\n"
            f"    - 🔗 اسم المستخدم: @{call.message.chat.username if call.message.chat.username else 'لا يوجد'}\n"
            f"    - 🔢 الحساب: {data.get('account_id', 'غير متوفر')}\n"
            f"    - 💰 المبلغ: {data.get('amount', {}).get('amount', 'غير متوفر')} {data.get('amount', {}).get('currency', '')}\n"
            f"    - 🏦 البنك: {data.get('bank', {}).get('bank_name', 'غير متوفر')} ({data.get('bank', {}).get('country', '')})\n"
            f"    - 📜 RIB: {data.get('rib', 'غير متوفر')}\n"
            f"    - 🆔 المعاملة: {data.get('transaction_id', 'غير متوفر')}\n"
            f"    - 📧 البريد: {data.get('email', 'غير متوفر')}\n"
            f"    - 👤 الاسم: {data.get('full_name', 'غير متوفر')}\n"
            f"    - 🔄 النوع: {data.get('request_type', 'غير متوفر')}\n"
        )
        if 'manager_message' in data:
            confirmation_message += f"💬 رسالة المستخدم إلى الدعم: <code>{data['manager_message']}</code>"

        bot.send_message(GROUP_ID, confirmation_message, parse_mode="HTML")
        proof = data.get('proof')
        if proof:
            bot.send_photo(GROUP_ID, proof, caption=f"📷 دليل للطلب: <code>{request_id}</code>", parse_mode="HTML")
        bot.edit_message_text("🎉 تم إرسال طلبك بنجاح إلى الدعم. سيتم الرد عليك قريباً.", chat_id=call.message.chat.id, message_id=call.message.message_id)
    elif action == "no":
        bot.edit_message_text("⚠️ يرجى تصحيح البيانات.", chat_id=call.message.chat.id, message_id=call.message.message_id)
        request_account_id(call.message)




def propose_affiliate_partnership(message):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🤝 شراكة تابعة مع Linebet", url=AFFILIATE_BOT_LINK))
    bot.send_message(message.chat.id, "🔗 هل ترغب في أن تصبح شريكًا تابعًا لـ Linebet؟", reply_markup=markup)






# ====================================================
# START BOT POLLING
# ====================================================
import time

while True:
    try:
        bot.polling(timeout=60, long_polling_timeout=60)
    except Exception as e:
        print(f"Polling error: {e}. Retrying in 15 seconds...")
        time.sleep(15)


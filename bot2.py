from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
import logging

# Replace with your bot token
BOT_TOKEN = '8020664087:AAHIDGCfIktHdjJ5u_q_Wul4t4GNPOEaYVs'

# Links for the template messages
app_link = "https://lb-aff.com/L?tag=d_3140479m_66803c_apk1&site=3140479&ad=66803"
partner_app_link = "https://dkr84sogf1xdp.cloudfront.net/linebet/android/app.apk"
iphone_links = {
    "ar": "https://linebet.partners/ae/sign-in",
    "en": "https://linebet.partners/en-sign-in",
    "fr": "https://linebet.partners/fr-sign-in",
    "fa": "https://linebet.partners/fa-sign-in"
}

# Translations for each language
translations = {
    "promo_code_message": {
        "ar": """
سجل الان 🪙

🔴 اضغط للتسجيل: {custom_signup_links}

أدخل الرمز الترويجي عند التسجيل: {promo_code}
واحصل على مكافأة تصل إلى 💯 💸 على إيداعك الأول

دعم 24/7 للاعبين!

👇تطبيق الهاتف المحمول هنا 📱
🔵 اضغط لتحميل التطبيق: {app_link}
        """,
        "en": """
Sign up now 🪙

🔴 Click to sign up: {custom_signup_links}

Enter the promo code at registration: {promo_code}
Get a reward of up to 💯 💸 on your first deposit.

24/7 support for players!

👇Mobile app here 📱
🔵 Click to download the app: {app_link}
        """,
        "fr": """
Inscrivez-vous maintenant 🪙

🔴 Cliquez pour vous inscrire : {custom_signup_links}

Entrez le code promo lors de l'inscription : {promo_code}
Obtenez une récompense allant jusqu'à 💯 💸 sur votre premier dépôt.

Support 24/7 pour les joueurs!

👇Application mobile ici 📱
🔵 Cliquez pour télécharger l'application : {app_link}
        """,
        "fa": """
اکنون ثبت نام کنید 🪙

🔴 برای ثبت نام کلیک کنید: {custom_signup_links}

کد تبلیغاتی را هنگام ثبت نام وارد کنید: {promo_code}
پاداشی تا 💯 💸 در اولین سپرده خود دریافت کنید.

پشتیبانی 24/7 برای بازیکنان!

👇اپلیکیشن موبایل 📱
🔵 برای دانلود اپلیکیشن کلیک کنید: {app_link}
        """
    },
    "partner_account_message": {
        "ar": """
💬 تفاصيل التسجيل و الدخول إلى حساب الوكيل, عن طريق التطبيق التالي الخاص بالوكيل👇

قم بنسخ و لصق البيانات 👇 للدخول على حسابك الخاص بالوكيل 

اسم المستخدم: {username}
وكلمة المرور: {password}

🤖 تطبيق يحتوي على جميع بيانات التسجيل والإيداعات للاعبين بالإضافة إلى عمولتك: {partner_app_link}
❤️ لوكلاء الأيفون: {iphone_link}
        """,
        "en": """
💬 Agent account login details. Access the agent-specific application here👇

Copy and paste the details below to access your account

Username: {username}
Password: {password}

🤖 App with all registration data, deposits, and your commission: {partner_app_link}
❤️ For iPhone agents: {iphone_link}
        """,
        "fr": """
💬 Détails de connexion au compte agent. Accédez à l'application spécifique à l'agent ici👇

Copiez et collez les informations ci-dessous pour accéder à votre compte

Nom d'utilisateur : {username}
Mot de passe : {password}

🤖 Application avec toutes les données d'inscription, les dépôts et votre commission : {partner_app_link}
❤️ Pour les agents iPhone : {iphone_link}
        """,
        "fa": """
💬 جزئیات ورود به حساب نماینده. به برنامه مخصوص نماینده دسترسی پیدا کنید👇

اطلاعات زیر را کپی و جایگذاری کنید تا به حساب خود دسترسی پیدا کنید

نام کاربری: {username}
رمز عبور: {password}

🤖 اپلیکیشنی با تمام داده‌های ثبت نام، سپرده‌ها و کمیسیون شما: {partner_app_link}
❤️ برای نمایندگان آیفون: {iphone_link}
        """
    },
    "demo_account_message": {
        "ar": """
🆔 المعرف: {demo_id}
🔐 كلمة المرور: {demo_password}

حساب تجريبي
        """,
        "en": """
🆔 ID: {demo_id}
🔐 Password: {demo_password}

Demo Account
        """,
        "fr": """
🆔 ID : {demo_id}
🔐 Mot de passe : {demo_password}

Compte Démo
        """,
        "fa": """
🆔 شناسه: {demo_id}
🔐 رمز عبور: {demo_password}

حساب دمو
        """
    }
}

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Displays the main menu."""
    keyboard = [
        [
            InlineKeyboardButton("Promo Code Message", callback_data='promo_code'),
            InlineKeyboardButton("Partner's Account Details", callback_data='partner_account')
        ],
        [
            InlineKeyboardButton("Demo", callback_data='demo_account'),
            InlineKeyboardButton("Cancel", callback_data='cancel'),
            InlineKeyboardButton("Return to Menu", callback_data='menu')
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    welcome_text = "Welcome! Please select an option:"
    if update.message:
        await update.message.reply_text(welcome_text, reply_markup=reply_markup)
    elif update.callback_query:
        await update.callback_query.message.edit_text(welcome_text, reply_markup=reply_markup)

async def language_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles language selection for the chosen action."""
    query = update.callback_query
    context.user_data['selection'] = query.data  # Store selection type
    keyboard = [
        [
            InlineKeyboardButton("English", callback_data='lang_en'),
            InlineKeyboardButton("Arabic", callback_data='lang_ar'),
            InlineKeyboardButton("French", callback_data='lang_fr'),
            InlineKeyboardButton("Farsi", callback_data='lang_fa')
        ],
        [
            InlineKeyboardButton("Cancel", callback_data='cancel'),
            InlineKeyboardButton("Return to Menu", callback_data='menu')
        ]
    ]
    await query.message.edit_text("Choose a language:", reply_markup=InlineKeyboardMarkup(keyboard))

async def request_user_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Prompts user input based on the selection and language chosen."""
    query = update.callback_query
    context.user_data['language'] = query.data[-2:]
    selection = context.user_data.get('selection')
    
    if not selection:
        await query.message.reply_text("Error: Please restart the bot by typing /start")
        return

    keyboard = [
        [InlineKeyboardButton("Cancel", callback_data='cancel'), InlineKeyboardButton("Return to Menu", callback_data='menu')]
    ]
    prompt = {
        'promo_code': "Please enter the promo code and links (format: PROMOCODE LINK LINK LINK):",
        'partner_account': "Please enter the username and password (format: username password):",
        'demo_account': "Please enter the ID and password (format: ID Password):"
    }.get(selection, "Invalid selection. Please restart the bot.")
    
    await query.message.edit_text(prompt, reply_markup=InlineKeyboardMarkup(keyboard))

async def send_custom_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Formats and sends a message based on user input and stored selection."""
    user_input = update.message.text
    selection = context.user_data.get('selection')
    language = context.user_data.get('language')

    try:
        if selection == 'promo_code':
            promo_code, *links = user_input.split(" ")
            custom_signup_links = " ".join(links)
            message = translations["promo_code_message"][language].format(
                custom_signup_links=custom_signup_links,
                promo_code=promo_code,
                app_link=app_link
            )
        elif selection == 'partner_account':
            username, password = user_input.split(" ")
            message = translations["partner_account_message"][language].format(
                username=username,
                password=password,
                partner_app_link=partner_app_link,
                iphone_link=iphone_links[language]
            )
        elif selection == 'demo_account':
            demo_id, demo_password = user_input.split(" ")
            message = translations["demo_account_message"][language].format(
                demo_id=demo_id,
                demo_password=demo_password
            )
        else:
            await update.message.reply_text("Invalid selection. Please restart with /start.")
            return
        await update.message.reply_text(message)
    except (ValueError, KeyError):
        await update.message.reply_text("Input format incorrect. Please follow the instructions.")

    # Return to the main menu after message is sent
    await start(update, context)

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles cancel action."""
    await update.callback_query.message.edit_text("Action canceled.")

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles all button presses in the flow."""
    query = update.callback_query
    data = query.data

    if data == 'menu':
        await start(update, context)
    elif data == 'cancel':
        await cancel(update, context)
    elif data in ['promo_code', 'partner_account', 'demo_account']:
        await language_selection(update, context)
    elif data.startswith('lang_'):
        await request_user_input(update, context)

def main() -> None:
    """Sets up and runs the bot."""
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, send_custom_message))

    application.run_polling()

if __name__ == '__main__':
    main()

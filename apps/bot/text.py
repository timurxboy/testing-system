"""User-facing strings for the bot (Uzbek, Latin script).

Keep them in one place so a future locale switch is cheap.
"""

# ---- Registration ----
WELCOME_NEW = (
    "Assalomu alaykum!\n"
    "Davom etish uchun shaxsiy ID raqamingizni yuboring."
)
WELCOME_BACK = "Qaytib kelganingiz bilan, <b>{student_id}</b>!"
ASK_STUDENT_ID = "Iltimos, shaxsiy ID raqamingizni yuboring."
INVALID_STUDENT_ID = "Iltimos, to'g'ri ID kiriting (1-64 belgi)."
STUDENT_ID_TAKEN = "Bu ID boshqa foydalanuvchida ro'yxatdan o'tgan."
REGISTRATION_OK = "Tayyor! Endi menyudan kerakli amalni tanlang."

# ---- Common ----
NOT_REGISTERED = "Avval ro'yxatdan o'ting — /start bosing."
ONLY_FOR_ADMINS = "Bu buyruq faqat adminlar uchun."
SESSION_LOST = "Test sessiyasi yo'qoldi. \"Testlarni bajarish\" tugmasini qayta bosing."
INVALID_OPTION = "Noto'g'ri variant"
TEST_INTERRUPTED = "Test bekor qilindi"

# ---- Menu (reply keyboard) ----
BTN_TAKE_TEST = "📚 Testlarni bajarish"
BTN_STATS = "📊 Statistika"
MENU_PROMPT = "Bosh menyu:"

# ---- Testing ----
CHOOSE_SUBJECT = "Fanni tanlang:"
NO_SUBJECTS = "Hozircha mavjud fanlar yo'q. Keyinroq qayting."
SUBJECT_LABEL = "Fan: <b>{name}</b>"
SUBJECT_INACTIVE = "Bu fan hozir mavjud emas."
SUBJECT_NO_QUESTIONS = "Bu fan bo'yicha hali savollar yo'q."

ATTEMPT_RESUMED = (
    "Tugatilmagan urinishni davom ettiramiz "
    "(urinish #{n}, savol {position}/{total})."
)
ATTEMPT_STARTED = (
    "Yangi urinish boshlandi (#{n}).\n"
    "Bu urinishda {count} ta savol bo'ladi."
)
ATTEMPT_NEW_ROUND = (
    "Siz bu fan bo'yicha barcha savollarni ko'rgansiz — "
    "yangi aylanani boshladik! Savollar yana boshqa tartibda keladi."
)

QUESTION_HEADER = "<b>Savol ({position}/{total})</b>"
OPTION_LINE = "<b>{label})</b> {text}"

CORRECT_VERDICT = "✅ <b>To'g'ri!</b>  ({label})"
WRONG_VERDICT_HEADER = "❌ <b>Noto'g'ri.</b>"
WRONG_YOU_PICKED = "Sizning javobingiz: <b>{label})</b> {text}"
WRONG_CORRECT_IS = "To'g'ri javob: <b>{label})</b> {text}"

TEST_FINISHED_HEADER = "🎉 <b>Urinish yakunlandi!</b>"
TEST_FINISHED_LINE = "To'g'ri javoblar: <b>{correct}</b> / {total}"
TEST_NO_ANSWERS = "Test yakunlandi. Hech qanday savol javoblanmadi."

# ---- Inline buttons ----
BTN_CANCEL_TEST = "❌ Testni bekor qilish"
BTN_PREV = "◀ Orqaga"
BTN_NEXT = "Oldinga ▶"

# ---- Stats ----
STATS_HEADER = "📊 <b>Statistika — {period}</b>"
STATS_SINCE = "{since:%Y-%m-%d %H:%M} UTC dan"
STATS_TOTALS = "Foydalanuvchilar: <b>{users}</b>"
STATS_NO_DATA = "Tanlangan davr uchun ma'lumot yo'q."
STATS_PAGE = "Sahifa {n} / {total}"
PERIOD_WEEK = "Hafta"
PERIOD_MONTH = "Oy"
PERIOD_YEAR = "Yil"

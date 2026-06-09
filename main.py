import asyncio
import os
import time
import random
import sqlite3
import base64
import html

from aiogram import Bot, Dispatcher
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import CommandStart
from dotenv import load_dotenv
from openai import OpenAI
from gtts import gTTS
from aiogram.types import FSInputFile
from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from aiogram.enums import ChatAction
from datetime import datetime, timedelta
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import BufferedInputFile
from aiogram import Bot, Dispatcher, F 
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

client = OpenAI(api_key=OPENAI_API_KEY) 

user_modes = {}

ADMIN_ID = 6511055106

user_languages = {}
selected_languages = {}

user_vocab_pages = {}
user_vocab_index = {} 

user_course = {} 
user_previous_menu = {}

user_conversation_topics = {}

user_spanish_mode = {}

user_requests = {}

daily_requests = {}

def check_limit(user_id):
    now = time.time()

    if user_id in user_requests:
        if now - user_requests[user_id] < 3:
            return False

    user_requests[user_id] = now
    return True

last_word = {}

saved_words = {}
vocabulary_book = {}

shadowing_text = {}

task2_questions = [
    "Some people think university education should be free. To what extent do you agree or disagree?",
    "Many people believe technology has improved our lives. Discuss both views and give your opinion.",
    "Some people think children should learn music at school. Do you agree or disagree?",
    "Many people prefer living in cities. What are the advantages and disadvantages?",
    "Some people believe that online learning is better than classroom learning. Discuss both views.",
    "Governments should spend more money on public transport. To what extent do you agree?",
    "Some people think advertisements influence our choices. Discuss both views.",
    "Many people believe that zoos should be closed. Do you agree or disagree?",
    "Some people think sports play an important role in society. Discuss both views.",
    "Many people believe that international tourism creates problems. To what extent do you agree?"
]

used_task1 = {}
used_task2 = {}

user_book_topic = {}
user_book_level = {}
 
last_meaning = {}

conn = sqlite3.connect(
    "bot.db",
    check_same_thread=False
)

cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS vocabulary_book (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    word TEXT,
    meaning TEXT,
    language TEXT
)
""")

try:
    cursor.execute("""
    ALTER TABLE vocabulary_book
    ADD COLUMN language TEXT
    """)
    conn.commit()
except:
    pass

cursor.execute("""
UPDATE vocabulary_book
SET language='english'
WHERE language IS NULL
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS spanish_stats (
    user_id INTEGER PRIMARY KEY,
    words_learned INTEGER DEFAULT 0,
    exercises_completed INTEGER DEFAULT 0,
    dele_tests INTEGER DEFAULT 0
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS premium_users (
    user_id INTEGER PRIMARY KEY,
    expire_date TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS english_premium (
    user_id INTEGER PRIMARY KEY,
    expire_date TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS spanish_premium (
    user_id INTEGER PRIMARY KEY,
    expire_date TEXT
)
""")

cursor.execute("""
DELETE FROM premium_users
WHERE expire_date < ?
""", (
    datetime.now().strftime("%Y-%m-%d"),
))

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    first_seen TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS activity (
    user_id INTEGER PRIMARY KEY,
    last_active TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS chat_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    role TEXT,
    message TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS saved_words (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    word TEXT
)
""")

conn.commit() 

def is_premium(user_id):

    cursor.execute(
        """
        SELECT expire_date
        FROM premium_users
        WHERE user_id=?
        """,
        (user_id,)
    )

    result = cursor.fetchone()

    if not result:
        return False

    expire_date = datetime.strptime(
        result[0],
        "%Y-%m-%d"
    )

    return datetime.now() <= expire_date

def get_premium_info(user_id):

    cursor.execute(
        """
        SELECT expire_date
        FROM premium_users
        WHERE user_id=?
        """,
        (user_id,)
    )

    return cursor.fetchone()

def is_english_premium(user_id):

    cursor.execute("""
    SELECT expire_date
    FROM english_premium
    WHERE user_id=?
    """, (user_id,))

    result = cursor.fetchone()

    if not result:
        return False

    expire_date = datetime.strptime(
        result[0],
        "%Y-%m-%d"
    )

    return datetime.now() <= expire_date

def is_spanish_premium(user_id):

    cursor.execute("""
    SELECT expire_date
    FROM spanish_premium
    WHERE user_id=?
    """, (user_id,))

    result = cursor.fetchone()

    if not result:
        return False

    expire_date = datetime.strptime(
        result[0],
        "%Y-%m-%d"
    )

    return datetime.now() <= expire_date

grammar_topics = [
    "Present Simple",
    "Present Continuous",
    "Present Perfect",
    "Present Perfect Continuous",
    "Past Simple",
    "Past Continuous",
    "Past Perfect",
    "Past Perfect Continuous",
    "Future Simple",
    "Future Continuous",
    "Future Perfect",
    "Future Perfect Continuous",

    "Conditionals",
    "Passive Voice",
    "Reported Speech",
    "Modal Verbs",

    "Can and Could",
    "May and Might",
    "Must and Have To",
    "Should and Ought To",
    "Need To",
    "Would",

    "Countable Nouns",
    "Uncountable Nouns",
    "Plural Nouns",
    "Possessive Nouns",
    "Collective Nouns",
    "Abstract Nouns",
    "Concrete Nouns",

    "Personal Pronouns",
    "Possessive Pronouns",
    "Reflexive Pronouns",
    "Relative Pronouns",
    "Demonstrative Pronouns",
    "Indefinite Pronouns",
    "Interrogative Pronouns",

    "Prepositions of Time",
    "Prepositions of Place",
    "Prepositions of Movement",
    "Common Prepositions",
    "Prepositional Phrases",

    "Relative Clauses",
    "Question Tags",
    "Gerunds and Infinitives",
    "Phrasal Verbs",
    "Inversion",
    "Subjunctive Mood",

    "Grammar for Writing Task 1",
    "Grammar for Writing Task 2",
    "Complex Sentences",
    "Linking Words",
    "Academic Vocabulary",
    "Formal English",
    "Band 7+ Grammar",
    "Band 8+ Grammar",    
]

LANGUAGES = [
    "Uzbek",
    "Russian",
    "English",
    "Turkish",
    "German",
    "French",
    "Spanish",
    "Italian",
    "Portuguese",
    "Arabic",
    "Chinese",
    "Japanese",
    "Korean",
    "Hindi",
    "Urdu",
    "Persian",
    "Dutch",
    "Polish",
    "Greek",
    "Swedish",
    "Norwegian",
    "Finnish",
    "Thai",
    "Vietnamese",
    "Indonesian",
    "Malay"
]

@dp.message(CommandStart())
async def start(message: Message):

    cursor.execute(
        "INSERT OR IGNORE INTO users (user_id, first_seen) VALUES (?, ?)",
        (
            message.from_user.id,
            datetime.now().strftime("%Y-%m-%d")
        )
    )

    conn.commit()

    cursor.execute(
        "INSERT OR REPLACE INTO activity (user_id, last_active) VALUES (?, ?)",
        (
            message.from_user.id,
            datetime.now().strftime("%Y-%m-%d")
        )
    )

    conn.commit()

    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🇬🇧 English")],
            [KeyboardButton(text="🇪🇸 Spanish")]
        ],
        resize_keyboard=True
    )

    await message.answer(
        "🌍 Which language do you want to learn?",
        reply_markup=keyboard
    )

@dp.message(lambda message: message.voice)
async def voice_message(message: Message):

    mode = user_modes.get(message.from_user.id)
    
    audio_path = None
    voice_path = None

    if mode not in [
        "voice",
        "ielts_speaking_voice",
        "cefr_speaking_voice",
        "teacher",
        "conversation",
        "shadowing",
        "spanish_pronunciation",
        "pronunciation"
    ]:
        return

    try:

        await message.answer(
            "🎤 Processing voice..."
        )

        voice = message.voice

        if voice.file_size > 10 * 1024 * 1024:
            await message.answer(
                "❌ Voice juda katta."
            )
            return

        file = await bot.get_file(
            voice.file_id
        )

        os.makedirs(
            "voices",
            exist_ok=True
        )

        voice_path = (
            f"voices/{message.from_user.id}.ogg"
        )

        await bot.download_file(
            file.file_path,
            destination=voice_path
        )

        with open(
            voice_path,
            "rb"
        ) as audio_file:

            transcript = (
                client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file
                )
            )

        user_text = transcript.text
        
        if mode == "teacher":

            response = await asyncio.to_thread(
                client.responses.create,
                model="gpt-5-nano",
                input=f"""    
        Answer the questions.

        Be helpful.

        Answer in English.

        User:

        {user_text}
        """
            )

            reply_text = response.output_text

            tts = gTTS(
                text=reply_text,
                lang="en"
            )

            audio_path = (
                f"voices/{message.from_user.id}_teacher.mp3"
            )

            tts.save(audio_path)

            await message.answer(
                f"📝 Transcript:\n\n{user_text}"
            )

            await message.answer(
                reply_text[:3500]
            )

            await bot.send_voice(
                chat_id=message.chat.id,
                voice=FSInputFile(audio_path)
            )

            return

        if mode == "shadowing":

            original_text = shadowing_text.get(
                message.from_user.id,
                ""
            )

            response = await asyncio.to_thread(
                client.responses.create,
                model="gpt-5-nano",
                input=f"""
        You are an English pronunciation examiner.

        Original text:

        {original_text}

        Student said:

        {user_text}

        Evaluate:

        1. Score from 0 to 10
        2. Pronunciation
        3. Fluency
        4. Missing words
        5. Incorrect words
        6. Suggestions

        Be strict but fair.

        Use emojis.
        """
            )

            await message.answer(
                f"📝 Your Speech:\n\n{user_text}"
            )

            await message.answer(
                response.output_text[:4000]
            )

            return

        if mode == "conversation":

            response = await asyncio.to_thread(
                client.responses.create,
                model="gpt-5-nano",
                input=f"""
        You are an English conversation partner.

        Talk naturally in English.

        Correct mistakes briefly.

        Ask one follow-up question.

        User:

        {user_text}
        """
            )

            reply_text = response.output_text

            tts = gTTS(
                text=reply_text,
                lang="en"
            )

            audio_path = (
                f"voices/{message.from_user.id}_conversation.mp3"
            )

            tts.save(audio_path)

            await message.answer(
                reply_text[:3500]
            )

            await bot.send_voice(
                chat_id=message.chat.id,
                voice=FSInputFile(audio_path)
            )

            if os.path.exists(audio_path):
                os.remove(audio_path)

            return
         
        if mode == "voice":

            response = await asyncio.to_thread(
            client.responses.create,
            model="gpt-5-nano",
            input=f"""
        Talk naturally in English.

        User:

        {user_text}
        """
            )

            await message.answer(
                response.output_text[:4000]
            )

            return
  
        if mode == "ielts_speaking_voice":

            response = await asyncio.to_thread(
                client.responses.create,
                model="gpt-5-nano",
                input=f"""
        You are an official IELTS Speaking examiner.

        Candidate answer:

        {user_text}

        Evaluate:

        1. Overall Band Score
        2. Fluency and Coherence
        3. Lexical Resource
        4. Grammatical Range and Accuracy
        5. Pronunciation

        Give strengths.
        Give weaknesses.
        Give suggestions for improvement.

        Use IELTS format.
        """
            )

            await message.answer(
                f"📝 Transcript:\n\n{user_text[:1500]}"
            )

            await message.answer(
                response.output_text[:4000]
            )

            return

        if mode == "cefr_speaking_voice":

            response = await asyncio.to_thread(
                client.responses.create,
                model="gpt-5-nano",
                input=f"""
You are a CEFR speaking examiner.

Student answer:

{user_text}

Evaluate:

1. Estimated CEFR Level (A1, A2, B1, B2, C1, C2)
2. Fluency
3. Grammar
4. Vocabulary
5. Pronunciation

Give strengths.
Give weaknesses.
Give suggestions for improvement.

Use CEFR format.
"""
            )

            await message.answer(
                f"📝 Transcript:\n\n{user_text[:1500]}"
            )

            await message.answer(
                response.output_text[:4000]
            )

            return
    
        if mode == "pronunciation":

            response = await asyncio.to_thread(
                client.responses.create,
                model="gpt-5-nano",
                input=f"""
        You are an English pronunciation coach.

        Student said:

        {user_text}

        Give:

        1. Pronunciation score (0-10)
        2. IPA
        3. Stress
        4. Mistakes
        5. Improvement tips

        Keep it short.
        """
            )

            await message.answer(
                f"📝 Transcript:\n\n{user_text}"
            )

            await message.answer(
                response.output_text[:3000]
            )

            return

        if mode == "spanish_pronunciation":

            response = await asyncio.to_thread(
                client.responses.create,
                model="gpt-5-nano",
                input=f"""
                You are a Spanish pronunciation coach.

                Student said:

                {user_text}

                Give:

                1. Pronunciation score (0-10)
                2. Mistakes
                3. Correct pronunciation
                4. Improvement tips

                Answer in Spanish.
                """
            )

            await message.answer(
                f"📝 Transcripción:\n\n{user_text}"
            )

            await message.answer(
                response.output_text[:3000]
            )

            await message.answer(
                f"📝 You said:\n\n{user_text}"
            )

            return
        
    except Exception as e:
        print(e)
        await message.answer(
            "❌ Internal error. Try again later."
        )
 
    finally:

        if voice_path and os.path.exists(voice_path):
            os.remove(voice_path)

        if audio_path and os.path.exists(audio_path):
            os.remove(audio_path)

       
@dp.callback_query()
async def premium_callback(callback):

    if callback.from_user.id != ADMIN_ID:
        await callback.answer(
            "Not allowed",
            show_alert=True
        )
        return

    if callback.data.startswith("approve_"):

        user_id = int(
            callback.data.split("_")[1]
        )

        expire_date = (
            datetime.now() + timedelta(days=30)
        ).strftime("%Y-%m-%d")

        cursor.execute(
            """
            INSERT OR REPLACE INTO spanish_premium
            (user_id, expire_date)
            VALUES (?, ?)
            """,
            (user_id, expire_date)
        )

        conn.commit()

        await bot.send_message(
            user_id,
            f"🎉 Premium activated!\n\nValid until: {expire_date}"
        )

        await callback.message.edit_caption(
            caption=
            callback.message.caption +
            "\n\n✅ APPROVED"
        )

        await callback.answer(
            "Premium activated."
        )

        return

    if callback.data.startswith("reject_"):

        user_id = int(
            callback.data.split("_")[1]
        )

        await bot.send_message(
            user_id,
            "❌ Your payment was rejected.\nPlease contact admin."
        )

        await callback.message.edit_caption(
            caption=
            callback.message.caption +
            "\n\n❌ REJECTED"
        )

        await callback.answer(
            "Request rejected."
        )

@dp.message(lambda message: message.photo)
async def payment_screenshot(message: Message):

    mode = user_modes.get(message.from_user.id)

    if mode == "teacher":

        await message.answer(
            "🖼 Analyzing image..."
        )

        photo = message.photo[-1]

        file = await bot.get_file(
            photo.file_id
        )

        image_path = (
            f"images/{message.from_user.id}.jpg"
        )

        os.makedirs(
            "images",
            exist_ok=True
        )

        await bot.download_file(
            file.file_path,
            destination=image_path
        )

        with open(image_path, "rb") as img:

            image_bytes = img.read()

        base64_image = base64.b64encode(
            image_bytes
        ).decode("utf-8")

        response = client.responses.create(
            model="gpt-5-nano",
            input=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_text",
                            "text": """
        Analyze this image.

        The user may ask:
        - what is this?
        - why does this happen?
        - how to fix it?
        - is it safe?
        - explain it

        Give a helpful answer in English.
        """
                        },
                        {
                            "type": "input_image",
                            "image_url":
                            f"data:image/jpeg;base64,{base64_image}"
                        }
                    ]
                }
            ]
        )

        await message.answer(
            response.output_text[:4000]
        )

        if os.path.exists(image_path):
            os.remove(image_path)

        return

    if mode == "food_analyzer":

        await message.answer(
            "🥗 Analyzing product..."
        )

        os.makedirs("food_images", exist_ok=True)

        photo = message.photo[-1]

        file_info = await bot.get_file(
            photo.file_id
        )

        image_path = (
            f"food_images/{message.from_user.id}.jpg"
        )

        await bot.download_file(
            file_info.file_path,
            destination=image_path
        )

        with open(image_path, "rb") as image_file:
            image_base64 = base64.b64encode(
                image_file.read()
                ).decode("utf-8")

        response = await asyncio.to_thread(
            client.responses.create,
            model="gpt-4.1-mini",
            input=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_text",
                            "text": """
        Analyze this food or product image.

        Tell me:

        1. Product name
        2. Estimated calories
        3. Estimated protein
        4. Estimated carbohydrates
        5. Estimated fats
        6. Benefits
        7. Risks
        8. Health score from 1 to 10
        9. Recommendation

        Important:

        - If exact nutrition is unknown, provide realistic estimates.
        - Clearly state that calories are estimated from the image.
        - Use emojis.
        - Format beautifully.
        """
                        },
                        {
                            "type": "input_image",
                            "image_url":
                            f"data:image/jpeg;base64,{image_base64}"
                        }
                    ]
                }
            ]
        )

        try:

            await message.answer(
                response.output_text[:4000]
            )

        finally:

            if os.path.exists(image_path):
                os.remove(image_path)

        return
    
    if mode != "waiting_payment":
        return

    builder = InlineKeyboardBuilder()

    builder.button(
        text="✅ Approve",
        callback_data=f"approve_{message.from_user.id}"
    )

    builder.button(
        text="❌ Reject",
        callback_data=f"reject_{message.from_user.id}"
    )

    builder.adjust(2)

    await bot.send_photo(
        chat_id=ADMIN_ID,
        photo=message.photo[-1].file_id,
        caption=
        f"💳 New Premium Request\n\n"
        f"User ID: {message.from_user.id}\n"
        f"Name: {message.from_user.full_name}",
        reply_markup=builder.as_markup()
    )
  
    await message.answer(
        "✅ Screenshot sent to admin.\nPlease wait for confirmation."
    )

    user_modes.pop(message.from_user.id, None)

@dp.message(F.text)
async def chat(message: Message):

    async def show_wait_message(message):

        if user_course.get(message.from_user.id) == "spanish":

            await message.answer(
                "⏳ Tu respuesta se está preparando.\n\n"
                "Por favor espera hasta 1 minuto y 30 segundos.\n\n"
                "Gracias por tu paciencia. 😊"
            )

        else:

            await message.answer(
                "⏳ Your answer is being prepared.\n\n"
                "Please wait up to 1 minute 30 seconds.\n\n"
                "Thank you for your patience. 😊"
            )

    global selected_languages
    global user_languages

    user_id = message.from_user.id

    daily_requests[user_id] = (
        daily_requests.get(user_id, 0) + 1
    )

    if daily_requests[user_id] > 100:
        await message.answer(
            "❌ Daily limit reached."
        )
        return 

    text = message.text

    mode = user_modes.get(message.from_user.id)

    if mode == "save_word":

        word = text.strip()

        cursor.execute(
            """
            INSERT INTO vocabulary_book
            (user_id, word, meaning, language)
            VALUES (?, ?, ?, ?)
            """,
            (
                
                message.from_user.id,
                word,
                "-",
                "spanish"
            )
            
        )

        conn.commit()

        await message.answer(
            f"✅ '{word}' guardada."
        )

        user_modes.pop(
            message.from_user.id,
            None
        )

        return

    if mode == "spanish_translator":

        languages = user_languages.get(
            message.from_user.id,
            ["English"]
        )

        await show_wait_message(message)

        response = await asyncio.to_thread(
            client.responses.create,
            model="gpt-5-nano",
            input=f"""
    Translate this Spanish word:

    {text}

    Provide:

    1. Meaning
    2. Translations in:
    {', '.join(languages)}
    3. Example sentence
    4. Example translation

    Answer beautifully.
    """
        )

        await message.answer(
            response.output_text[:4000]
        )

        return

    if (
        text == "🇬🇧 English"
        and user_course.get(message.from_user.id) != "spanish"
    ):
        user_course[message.from_user.id] = "english"

        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="📚 Vocabulary"), KeyboardButton(text="📝 Grammar")],
                [KeyboardButton(text="📖 Reading"), KeyboardButton(text="🎤 Speaking")],
                [KeyboardButton(text="🎯 Writing"), KeyboardButton(text="🤖 AI Teacher")],
                [KeyboardButton(text="📖 My Vocabulary Book"), KeyboardButton(text="⭐ Premium")],
                [KeyboardButton(text="🌐 Languages")]
            ],
            resize_keyboard=True
        )

        await message.answer(
            "🇬🇧 English selected",
            reply_markup=keyboard
        )

        return

    if text == "🇪🇸 Spanish":

        await bot.send_chat_action(
            chat_id=message.chat.id,
            action=ChatAction.TYPING
        )

        cursor.execute("""
        INSERT OR IGNORE INTO spanish_stats
        (user_id)
        VALUES (?)
        """, (message.from_user.id,))

        conn.commit()

        user_course[message.from_user.id] = "spanish"

        selected_languages[
            message.from_user.id
        ] = []

        keyboard = ReplyKeyboardMarkup(
            keyboard=[          
                [KeyboardButton(text="🇬🇧 English"), KeyboardButton(text="🇳🇱 Dutch")],
                [KeyboardButton(text="🇺🇿 Uzbek"), KeyboardButton(text="🇷🇺 Russian")],
                [KeyboardButton(text="🇹🇷 Turkish"), KeyboardButton(text="🇩🇪 German")],
                [KeyboardButton(text="🇫🇷 French"), KeyboardButton(text="🇮🇹 Italian")],
                [KeyboardButton(text="🇵🇹 Portuguese"), KeyboardButton(text="🇸🇦 Arabic")],
                [KeyboardButton(text="🇨🇳 Chinese"), KeyboardButton(text="🇯🇵 Japanese")],
                [KeyboardButton(text="🇰🇷 Korean"), KeyboardButton(text="🇮🇳 Hindi")],
                [KeyboardButton(text="🇵🇱 Polish"), KeyboardButton(text="🇬🇷 Greek")],
                [KeyboardButton(text="🇸🇪 Swedish"), KeyboardButton(text="🇳🇴 Norwegian")],
                [KeyboardButton(text="🇫🇮 Finnish"), KeyboardButton(text="🇻🇳 Vietnamese")],
                [KeyboardButton(text="🇮🇩 Indonesian"), KeyboardButton(text="🇲🇾 Malay")],
                [KeyboardButton(text="✅ Continuar")]
            ],
            resize_keyboard=True
        )

        await message.answer(
            "🌐 Selecciona hasta 3 idiomas para las explicaciones:",
            reply_markup=keyboard
        )

        return
        
    if text in [
        "🌐 Languages",
        "🌐 Idiomas"
    ]:  

        user_course.pop(
            message.from_user.id,
            None
        )

        user_spanish_mode.pop(
            message.from_user.id,
            None
        )
        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="🇬🇧 English")],
                [KeyboardButton(text="🇪🇸 Spanish")]
            ],
            resize_keyboard=True
        )

        await message.answer(
            "🌍 Choose a language:",
            reply_markup=keyboard
        )

        return

    if text in [
        "🇬🇧 English",
        "🇳🇱 Dutch",
        "🇺🇿 Uzbek",
        "🇷🇺 Russian",
        "🇹🇷 Turkish",
        "🇩🇪 German",
        "🇫🇷 French",
        "🇮🇹 Italian",
        "🇵🇹 Portuguese",
        "🇸🇦 Arabic",
        "🇨🇳 Chinese",
        "🇯🇵 Japanese",
        "🇰🇷 Korean",
        "🇮🇳 Hindi",
        "🇵🇱 Polish",
        "🇬🇷 Greek",
        "🇸🇪 Swedish",
        "🇳🇴 Norwegian",
        "🇫🇮 Finnish",
        "🇻🇳 Vietnamese",
        "🇮🇩 Indonesian",
        "🇲🇾 Malay"
    ]:
        user_id = message.from_user.id

        if user_id not in selected_languages:
            selected_languages[user_id] = []

        if text not in selected_languages[user_id]:

            if len(selected_languages[user_id]) < 3:

                selected_languages[user_id].append(
                    text
                )

        await message.answer(
            f"✅ Seleccionados:\n\n"
            + "\n".join(
                selected_languages[user_id]
            )
        )

        return

    if text == "✅ Continuar":

        user_id = message.from_user.id

        if user_id not in selected_languages:

            await message.answer(
                "Selecciona al menos un idioma."
            )

            return

        if len(selected_languages[user_id]) == 0:

            await message.answer(
                "Selecciona al menos un idioma."
            )

            return

        user_languages[user_id] = (
            selected_languages[user_id]
        )

        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="📚 Vocabulario")],
                [KeyboardButton(text="📝 Gramática")],
                [KeyboardButton(text="📖 Lectura")],
                [KeyboardButton(text="🎤 Conversación")],
                [KeyboardButton(text="🤖 Profesor IA")],
                [KeyboardButton(text="⭐ Premium Español")],
                [KeyboardButton(text="🌐 Idiomas")]
            ],
            resize_keyboard=True
        )

        await message.answer(
            "🇪🇸 Menú Español",
            reply_markup=keyboard
        )

        return

    if text == "📚 Vocabulario":

        await bot.send_chat_action(
            chat_id=message.chat.id,
            action=ChatAction.TYPING
        )

        user_spanish_mode[message.from_user.id] = "vocab"

        user_previous_menu[
            message.from_user.id
            ] = "vocabulario"
        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="A1 Palabras")],
                [KeyboardButton(text="A2 Palabras")],
                [KeyboardButton(text="B1 Palabras")],
                [KeyboardButton(text="B2 Palabras")],
                [KeyboardButton(text="🔍 Traductor")],
                [KeyboardButton(text="⬅️ Volver")]
            ],  
            resize_keyboard=True
        )

        await message.answer(
            "📚 Elige tu nivel:",
            reply_markup=keyboard
        )

        return

    if text == "⬅️ Volver":

        print("VOLVER BOSILDI")
        print("PREVIOUS =", user_previous_menu.get(message.from_user.id))
        print("MODE =", user_modes.get(message.from_user.id))

        print(
            "DEBUG PREVIOUS =",
            user_previous_menu.get(
                message.from_user.id
            )
        )

        user_modes.pop(
            message.from_user.id,
            None
        )

        previous = user_previous_menu.get(
            message.from_user.id
        )

        if previous == "premium_functions":

            keyboard = ReplyKeyboardMarkup(
                keyboard=[
                    [KeyboardButton(text="📚 Vocabulario")],
                    [KeyboardButton(text="📝 Gramática")],
                    [KeyboardButton(text="📖 Lectura")],
                    [KeyboardButton(text="🎤 Conversación")],
                    [KeyboardButton(text="🤖 Profesor IA")],
                    [KeyboardButton(text="⭐ Premium Español")],
                    [KeyboardButton(text="🌐 Idiomas")]
                ],
                resize_keyboard=True
            )

            await message.answer(
                "🏠 Menú Español",
                reply_markup=keyboard
            )

            return
  
        if previous == "premium_menu":

            await bot.send_chat_action(
                chat_id=message.chat.id,
                action=ChatAction.TYPING
            )

            keyboard = ReplyKeyboardMarkup(
                keyboard=[
                    [KeyboardButton(text="📚 Vocabulario")],
                    [KeyboardButton(text="📝 Gramática")],
                    [KeyboardButton(text="📖 Lectura")],
                    [KeyboardButton(text="🎤 Conversación")],
                    [KeyboardButton(text="🤖 Profesor IA")],
                    [KeyboardButton(text="⭐ Premium Español")],
                    [KeyboardButton(text="🌐 Idiomas")]
                ],
                resize_keyboard=True
            )

            await message.answer(
                "🏠 Menú Español",
                reply_markup=keyboard
            )

            return

        if previous == "vocabulario":

            keyboard = ReplyKeyboardMarkup(
                keyboard=[
                    [KeyboardButton(text="📚 Vocabulario")],
                    [KeyboardButton(text="📝 Gramática")],
                    [KeyboardButton(text="📖 Lectura")],
                    [KeyboardButton(text="🎤 Conversación")],
                    [KeyboardButton(text="🤖 Profesor IA")],
                    [KeyboardButton(text="⭐ Premium Español")],
                    [KeyboardButton(text="🌐 Idiomas")]
                ],
                resize_keyboard=True
            )

            await message.answer(
                "🏠 Menú Español",
                reply_markup=keyboard
            )

            return

        if previous == "gramatica":

            keyboard = ReplyKeyboardMarkup(
                keyboard=[
                    [KeyboardButton(text="📚 Vocabulario")],
                    [KeyboardButton(text="📝 Gramática")],
                    [KeyboardButton(text="📖 Lectura")],
                    [KeyboardButton(text="🎤 Conversación")],
                    [KeyboardButton(text="🤖 Profesor IA")],
                    [KeyboardButton(text="⭐ Premium Español")],
                    [KeyboardButton(text="🌐 Idiomas")]
                ],
                resize_keyboard=True
            ) 

            await message.answer(
                "🏠 Menú Español",
                reply_markup=keyboard
            )

            return

        if previous == "premium_conversation_menu":

            user_modes.pop(
                message.from_user.id,
                None
            )

            user_previous_menu[
                message.from_user.id
            ] = "premium_functions"

            keyboard = ReplyKeyboardMarkup(
                keyboard=[
                   [KeyboardButton(text="🚀 Funciones Premium")],
                   [KeyboardButton(text="💳 Comprar Premium")],
                   [KeyboardButton(text="⭐ Verificar Estado")],
                   [KeyboardButton(text="📞 Contactar Admin")],
                   [KeyboardButton(text="⬅️ Volver")]
                ],
                resize_keyboard=True
            )

            await message.answer(
                "⭐ Premium Español",
                reply_markup=keyboard
            )

            return

        if previous == "roleplay_menu":

            user_previous_menu[message.from_user.id] = "conversacion"

            keyboard = ReplyKeyboardMarkup(
                keyboard=[
                    [KeyboardButton(text="🟢 Conversación A1")],
                    [KeyboardButton(text="🔵 Conversación A2")],
                    [KeyboardButton(text="🟡 Conversación B1")],
                    [KeyboardButton(text="🟠 Conversación B2")],
                    [KeyboardButton(text="🎭 Roleplay")],
                    [KeyboardButton(text="⬅️ Volver")]
                ],
                resize_keyboard=True
            )

            await message.answer(
                "🎤 Elige una opción:",
                reply_markup=keyboard
            )

            return

        if previous == "conversacion":

            keyboard = ReplyKeyboardMarkup(
                keyboard=[
                    [KeyboardButton(text="📚 Vocabulario")],
                    [KeyboardButton(text="📝 Gramática")],
                    [KeyboardButton(text="📖 Lectura")],
                    [KeyboardButton(text="🎤 Conversación")],
                    [KeyboardButton(text="🤖 Profesor IA")],
                    [KeyboardButton(text="⭐ Premium Español")],
                    [KeyboardButton(text="🌐 Idiomas")]
                ],
                resize_keyboard=True
            )

            await message.answer(
                "🏠 Menú Español",
                reply_markup=keyboard
            )

            return

    if text == "A1 Palabras":

        await bot.send_chat_action(
            chat_id=message.chat.id,
            action=ChatAction.TYPING
        )

        cursor.execute("""
        UPDATE spanish_stats
        SET words_learned = words_learned + 1
        WHERE user_id = ?
        """, (message.from_user.id,))

        conn.commit()

        user_previous_menu[
            message.from_user.id
        ] = "word_page"

        await message.answer(
            "📚 Generando vocabulario..."
        )

        languages = user_languages.get(
            message.from_user.id,
            ["English"]
        ) 

        languages_text = "\n".join(languages)

        await show_wait_message(message)

        response = await asyncio.to_thread(
            client.responses.create,
            model="gpt-5-nano",
            input=f"""
    Generate 20 Spanish A1 vocabulary words.

    For each word provide:

    1. Spanish word

    Translations in:

    {languages_text}

    3. Spanish example sentence

    4. Example translations in:

    {languages_text}

    Make it beautiful.
    """      
        )

        words = response.output_text.split("###")

        user_vocab_pages[
            message.from_user.id
        ] = words

        user_vocab_index[
            message.from_user.id
        ] = 0

        first_page = "\n\n".join(
             words[:5]
        )

        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="⬅️ Volver")]
            ],
            resize_keyboard=True
        )

        await message.answer(
            first_page[:4000],
            reply_markup=keyboard
        )    

        return

    if text == "A2 Palabras":

        await bot.send_chat_action(
            chat_id=message.chat.id,
            action=ChatAction.TYPING
        )

        cursor.execute("""
        UPDATE spanish_stats
        SET words_learned = words_learned + 1
        WHERE user_id = ?
        """, (message.from_user.id,))

        conn.commit()

        user_previous_menu[
            message.from_user.id
        ] = "word_page"

        languages = user_languages.get(
            message.from_user.id,
            ["English"]
        )

        languages_text = "\n".join(languages)

        await show_wait_message(message)

        response = await asyncio.to_thread(
            client.responses.create,
            model="gpt-5-nano",
            input=f"""
    Generate 20 Spanish A2 vocabulary words.

    For each word provide:

    1. Spanish word

    Translations in:

    {languages_text}

    3. Spanish example sentence

    4. Example translations in:

    {languages_text}

    Make it beautiful.
    """        
        )

        await message.answer(
            response.output_text[:4000]
        )

        return

    if text == "B1 Palabras":

        await bot.send_chat_action(
            chat_id=message.chat.id,
            action=ChatAction.TYPING
        )

        cursor.execute("""
        UPDATE spanish_stats
        SET words_learned = words_learned + 1
        WHERE user_id = ?
        """, (message.from_user.id,))

        conn.commit()

        user_previous_menu[
            message.from_user.id
        ] = "word_page"

        languages = user_languages.get(
            message.from_user.id,
            ["English"]
        )

        languages_text = "\n".join(languages)

        await show_wait_message(message)

        response = await asyncio.to_thread(
            client.responses.create,
            model="gpt-5-nano",
            input=f"""
    Generate 20 Spanish B1 vocabulary words.

    For each word provide:

    1. Spanish word

    Translations in:

    {languages_text}

    3. Spanish example sentence

    4. Example translations in:

    {languages_text}

    Make it beautiful.
    """
        )

        await message.answer(
            response.output_text[:4000]
        )

        return

    if text == "B2 Palabras":

        await bot.send_chat_action(
            chat_id=message.chat.id,
            action=ChatAction.TYPING
        )

        cursor.execute("""
        UPDATE spanish_stats
        SET words_learned = words_learned + 1
        WHERE user_id = ?
        """, (message.from_user.id,))

        conn.commit()

        user_previous_menu[
            message.from_user.id
        ] = "word_page"

        languages = user_languages.get(
            message.from_user.id,
            ["English"]
        )

        languages_text = "\n".join(languages)

        await show_wait_message(message)

        response = await asyncio.to_thread(
            client.responses.create,
            model="gpt-5-nano",
            input=f"""
    Generate 20 Spanish B2 vocabulary words.

    For each word provide:

    1. Spanish word

    Translations in:

    {languages_text}

    3. Spanish example sentence

    4. Example translations in:

    {languages_text}

    Make it beautiful.
    """
        )

        await message.answer(
            response.output_text[:4000]
        )

        return 

    if text == "📝 Gramática":

        await bot.send_chat_action(
            chat_id=message.chat.id,
            action=ChatAction.TYPING
        )

        cursor.execute("""
        UPDATE spanish_stats
        SET exercises_completed = exercises_completed + 1
        WHERE user_id = ?
        """, (message.from_user.id,))

        conn.commit()

        user_previous_menu[
            message.from_user.id
            ] = "gramatica"
        grammar_keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="🕒 Tiempos")],
                [KeyboardButton(text="👤 Pronombres")],
                [KeyboardButton(text="📍 Preposiciones")],
                [KeyboardButton(text="📝 Sustantivos")],
                [KeyboardButton(text="🚀 Gramática Avanzada")],
                [KeyboardButton(text="🎓 Gramática DELE")],
                [KeyboardButton(text="⬅️ Volver")]
            ],
            resize_keyboard=True
        )

        await message.answer(
            "📚 Gramática Española\n\nElige una categoría:",
            reply_markup=grammar_keyboard
        )

        return

    if text == "🕒 Tiempos":

        await bot.send_chat_action(
            chat_id=message.chat.id,
            action=ChatAction.TYPING
        )

        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="Presente")],
                [KeyboardButton(text="Pretérito Perfecto")],
                [KeyboardButton(text="Pretérito Indefinido")],
                [KeyboardButton(text="Pretérito Imperfecto")],
                [KeyboardButton(text="Futuro")],
                [KeyboardButton(text="Condicional")],
                [KeyboardButton(text="Subjuntivo")],
                [KeyboardButton(text="⬅️ Volver")]
            ],
            resize_keyboard=True
        )

        await message.answer(
            "🕒 Elige un tiempo verbal:",
            reply_markup=keyboard
        )

        return

    if text == "👤 Pronombres":

        await bot.send_chat_action(
            chat_id=message.chat.id,
            action=ChatAction.TYPING
        ) 

        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="Pronombres Personales")],
                [KeyboardButton(text="Pronombres Reflexivos")],
                [KeyboardButton(text="Pronombres Demostrativos")],
                [KeyboardButton(text="Pronombres Relativos")],
                [KeyboardButton(text="⬅️ Volver")]
            ],
            resize_keyboard=True
        )

        await message.answer(
            "👤 Elige un tema:",
            reply_markup=keyboard
        )

        return

    if text == "📍 Preposiciones":

        await bot.send_chat_action(
            chat_id=message.chat.id,
            action=ChatAction.TYPING
        )

        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="a")],
                [KeyboardButton(text="de")],
                [KeyboardButton(text="en")],
                [KeyboardButton(text="con")],
                [KeyboardButton(text="por")],
                [KeyboardButton(text="para")],
                [KeyboardButton(text="⬅️ Volver")]
            ],
            resize_keyboard=True
        )

        await message.answer(
            "📍 Elige una preposición:",
            reply_markup=keyboard
        )

        return

    if text == "📝 Sustantivos":

        await bot.send_chat_action(
            chat_id=message.chat.id,
            action=ChatAction.TYPING
        )

        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="Género")],
                [KeyboardButton(text="Plural")],
                [KeyboardButton(text="Artículos")],
                [KeyboardButton(text="Sustantivos Comunes")],
                [KeyboardButton(text="⬅️ Volver")]
            ],
            resize_keyboard=True
        )

        await message.answer(
            "📝 Elige un tema:",
            reply_markup=keyboard
        )

        return

    if text == "🚀 Gramática Avanzada":

        await bot.send_chat_action(
            chat_id=message.chat.id,
            action=ChatAction.TYPING
        )

        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="Subjuntivo")],
                [KeyboardButton(text="Voz Pasiva")],
                [KeyboardButton(text="Estilo Indirecto")],
                [KeyboardButton(text="Conectores")],
                [KeyboardButton(text="Oraciones Relativas")],
                [KeyboardButton(text="⬅️ Volver")]
            ],
            resize_keyboard=True
        )

        await message.answer(
            "🚀 Elige un tema avanzado:",
            reply_markup=keyboard
        )

        return

    if text == "🎓 Gramática DELE":

        await bot.send_chat_action(
            chat_id=message.chat.id,
            action=ChatAction.TYPING
        )

        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="📘 DELE B1")],
                [KeyboardButton(text="📙 DELE B2")],
                [KeyboardButton(text="📕 DELE C1")],
                [KeyboardButton(text="📗 DELE C2")],
                [KeyboardButton(text="⬅️ Volver")]
            ],
            resize_keyboard=True
        )

        await message.answer(
            "🎓 Elige tu nivel DELE:",
            reply_markup=keyboard
        )

        return

    if text in [
        "Presente",
        "Pretérito Perfecto",
        "Pretérito Indefinido",
        "Pretérito Imperfecto",
        "Futuro",
        "Condicional",
        "Subjuntivo"
    ]:

        await bot.send_chat_action(
            chat_id=message.chat.id,
            action=ChatAction.TYPING
        )

        languages = user_languages.get(
            message.from_user.id,
            ["English"]
        )

        languages_text = "\n".join(languages)

        await show_wait_message(message)

        response = await asyncio.to_thread(
            client.responses.create,
            model="gpt-5-nano",
            input=f"""
    Eres un profesor profesional de gramática española.

    Explica este tema:

    {text}

    Debes incluir:

    1. Explicación simple
    2. Fórmula
    3. Cuándo se usa
    4. 10 ejemplos
    5. Errores comunes
    6. Mini ejercicio
    7. Respuestas

    Explica en estos idiomas:

    {languages_text}

    El tema siempre es español,
    pero las explicaciones deben estar
    en los idiomas seleccionados.

    Usa emojis y formato bonito.
    """
        )

        await message.answer(
            response.output_text[:4000]
        )

        return

    if text in [
        "Pronombres Personales",
        "Pronombres Reflexivos",
        "Pronombres Demostrativos",
        "Pronombres Relativos"
    ]:

        await bot.send_chat_action(
            chat_id=message.chat.id,
            action=ChatAction.TYPING
        )

        languages = user_languages.get(
            message.from_user.id,
            ["English"]
        )

        languages_text = "\n".join(languages)

        await show_wait_message(message)

        response = await asyncio.to_thread(
            client.responses.create,
            model="gpt-5-nano",
            input=f"""
    Eres un profesor profesional de español.

    Explica:

    {text}

    Incluye:

    1. Definición
    2. Reglas
    3. Ejemplos
    4. Errores comunes
    5. Mini ejercicio
    6. Respuestas

    Explica en:

    {languages_text}

    El tema es español,
    pero las explicaciones deben estar
    en los idiomas seleccionados.
    """
        )

        await message.answer(
            response.output_text[:4000]
        )

        return

    if text in [
        "a",
        "de",
        "en",
        "con",
        "por",
        "para"
    ]:

        await bot.send_chat_action(
            chat_id=message.chat.id,
            action=ChatAction.TYPING
        )

        languages = user_languages.get(
            message.from_user.id,
            ["English"]
        )

        languages_text = "\n".join(languages)

        await show_wait_message(message)

        response = await asyncio.to_thread(
            client.responses.create,
            model="gpt-5-nano",
            input=f"""
    Eres profesor profesional de español.

    Explica la preposición:

    {text}

    Incluye:

    1. Qué significa
    2. Cuándo se usa
    3. Reglas importantes
    4. 15 ejemplos
    5. Errores comunes
    6. Comparaciones si es necesario
    7. Mini ejercicio
    8. Respuestas

    Explica en:

    {languages_text}
    """
        )

        await message.answer(
            response.output_text[:4000]
        )

        return

    if text in [
        "Género",
        "Plural",
        "Artículos",
        "Sustantivos Comunes"
    ]:

        await bot.send_chat_action(
            chat_id=message.chat.id,
            action=ChatAction.TYPING
        )

        languages = user_languages.get(
            message.from_user.id,
            ["English"]
        )

        languages_text = "\n".join(languages)

        await show_wait_message(message)

        response = await asyncio.to_thread(
            client.responses.create,
            model="gpt-5-nano",
            input=f"""
    Eres profesor profesional de gramática española.

    Explica:

    {text}

    Incluye:

    1. Explicación simple
    2. Reglas
    3. Fórmulas
    4. Ejemplos
    5. Errores comunes
    6. Mini ejercicio
    7. Respuestas

    Explica en:

    {languages_text}
    """
        )

        await message.answer(
            response.output_text[:4000]
        )

        return

    if text in [
        "📘 DELE B1",
        "📙 DELE B2",
        "📕 DELE C1",
        "📗 DELE C2"
    ]:

        await bot.send_chat_action(
            chat_id=message.chat.id,
            action=ChatAction.TYPING
        )

        languages = user_languages.get(
            message.from_user.id,
            ["English"]
        )

        languages_text = "\n".join(languages)

        await show_wait_message(message)

        response = await asyncio.to_thread(
            client.responses.create,
            model="gpt-5-nano",
            input=f"""
    Eres preparador oficial del examen DELE.

    Nivel:

    {text}

    Crea una lección completa.

    Incluye:

    1. Explicación
    2. Gramática importante
    3. Vocabulario importante
    4. Ejemplos reales
    5. Errores frecuentes
    6. Estrategias para aprobar DELE
    7. Ejercicio
    8. Respuestas

    Explica todo en:

    {languages_text}

    Nivel adaptado exactamente al examen DELE.
    """
        )

        await message.answer(
            response.output_text[:4000]
        )

        return

    if text == "🎧 Escuchar":

         await message.answer(
             "🚧 Escuchar estará disponible pronto."
         )

         return

    if text in [
        "Subjuntivo",
        "Voz Pasiva",
        "Estilo Indirecto",
        "Conectores",
        "Oraciones Relativas"
    ]:

        await bot.send_chat_action(
            chat_id=message.chat.id,
            action=ChatAction.TYPING
        )

        await show_wait_message(message)

        response = await asyncio.to_thread(
            client.responses.create,
            model="gpt-5-nano",
            input=f"""
    Eres profesor experto de gramática española.

    Explica este tema avanzado:

    {text}

    Incluye:

    1. Explicación completa
    2. Reglas
    3. Fórmulas
    4. Ejemplos reales
    5. Errores comunes
    6. Consejos
    7. Mini test
    8. Respuestas

    Todo en español.

    Nivel B1-C1.
    """
        )

        await message.answer(
            response.output_text[:4000]
        )

        return

    if text == "📖 Lectura":

        await bot.send_chat_action(
            chat_id=message.chat.id,
            action=ChatAction.TYPING
        )

        cursor.execute("""
        UPDATE spanish_stats
        SET exercises_completed = exercises_completed + 1
        WHERE user_id = ?
        """, (message.from_user.id,))

        conn.commit()

        books_keyboard = ReplyKeyboardMarkup(
            keyboard=[
               [KeyboardButton(text="⚔️ Aventuras")],
               [KeyboardButton(text="❤️ Romance")],
               [KeyboardButton(text="🚀 Ciencia Ficción")],
               [KeyboardButton(text="🕵️ Misterio")],
               [KeyboardButton(text="💼 Negocios")],
               [KeyboardButton(text="🏆 Motivación")],
               [KeyboardButton(text="🌍 Viajes")],
               [KeyboardButton(text="👻 Terror")],
               [KeyboardButton(text="⬅️ Volver")]
           ],
           resize_keyboard=True
        )

        await message.answer(
            "📚 Elige un tema:",
            reply_markup=books_keyboard
        )

        return
    
    if text == "🎤 Conversación":

        user_previous_menu[
            message.from_user.id
            ] = "conversacion"

        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="🟢 Conversación A1")],
                [KeyboardButton(text="🔵 Conversación A2")],
                [KeyboardButton(text="🟡 Conversación B1")],
                [KeyboardButton(text="🟠 Conversación B2")],
                [KeyboardButton(text="🎭 Roleplay")],
                [KeyboardButton(text="⬅️ Volver")]
            ],
            resize_keyboard=True
        )

        await message.answer(
            "🎤 Elige una opción:",
            reply_markup=keyboard
        )

        return

    if text in [
        "🟢 Conversación A1",
        "🔵 Conversación A2",
        "🟡 Conversación B1",
        "🟠 Conversación B2"
    ]:

        user_modes[message.from_user.id] = (
            f"conversation_{text}"
        )

        await message.answer(
            "🎤 Conversación iniciada.\n\n"
            "Preséntate en español."
        )

        return

    if text == "🎭 Roleplay":

        user_previous_menu[
            message.from_user.id
        ] = "roleplay_menu"

        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="🍕 Restaurante")],
                [KeyboardButton(text="✈️ Aeropuerto")],
                [KeyboardButton(text="🏨 Hotel")],
                [KeyboardButton(text="💼 Entrevista de Trabajo")],
                [KeyboardButton(text="👥 Nuevo Amigo")],
                [KeyboardButton(text="🛒 Tienda")],
                [KeyboardButton(text="⬅️ Volver")]
            ],
            resize_keyboard=True
        )

        await message.answer(
            "🎭 Elige una situación:",
            reply_markup=keyboard
        )

        return

    if text in [
        "🍕 Restaurante",
        "✈️ Aeropuerto",
        "🏨 Hotel",
        "💼 Entrevista de Trabajo",
        "👥 Nuevo Amigo",
        "🛒 Tienda"
    ]:

        user_previous_menu[
            message.from_user.id
        ] = "roleplay_menu"

        user_modes[
            message.from_user.id
        ] = f"roleplay_{text}"

        user_modes[message.from_user.id] = f"roleplay_{text}"

        await message.answer(
            f"🎭 Roleplay iniciado: {text}\n\n"
            "Responde en español."
        )

        return

    if text == "🤖 Profesor IA":

         user_modes[message.from_user.id] = "spanish_teacher"

         await message.answer(
             "🤖 Profesor IA Activado\n\n"
             "✅ Envía texto\n"
             "✅ Envía mensajes de voz\n"
             "✅ Haz preguntas\n"
             "✅ Practica conversación\n\n"
             "Escribe cualquier mensaje en español."
         )

         return

    if text in [
        "⚔️ Aventuras",
        "❤️ Romance",
        "🚀 Ciencia Ficción",
        "🕵️ Misterio",
        "💼 Negocios",
        "🏆 Motivación",
        "🌍 Viajes",
        "👻 Terror"
    ]:

        user_book_topic[message.from_user.id] = text

        level_keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="🟢 A1")],
                [KeyboardButton(text="🔵 A2")],
                [KeyboardButton(text="🟡 B1")],
                [KeyboardButton(text="🟠 B2")],
                [KeyboardButton(text="🔴 C1")],
                [KeyboardButton(text="⚫ C2")],
                [KeyboardButton(text="⬅️ Volver")]
            ],
            resize_keyboard=True
        )

        await message.answer(
            "📚 Elige tu nivel:",
            reply_markup=level_keyboard
        )  

        return

    if text in [
        "🟢 A1",
        "🔵 A2",
        "🟡 B1",
        "🟠 B2",
        "🔴 C1",
        "⚫ C2"
    ]:

        user_book_level[
            message.from_user.id
        ] = text

        length_keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="📄 Libro Corto")],
                [KeyboardButton(text="📘 Libro Mediano")],
                [KeyboardButton(text="📚 Libro Largo")],
                [KeyboardButton(text="⬅️ Volver")]
            ],
            resize_keyboard=True
        )

        await message.answer(
            "📚 Elige la longitud del libro:",
            reply_markup=length_keyboard
        )

        return

    if text in [
        "📄 Libro Corto",
        "📘 Libro Mediano",
        "📚 Libro Largo"
    ]:

        user_id = message.from_user.id

        if user_id not in user_book_topic:
            return

        if user_id not in user_book_level:
            return

        topic = user_book_topic[user_id]
        level = user_book_level[user_id]

        if text == "📄 Libro Corto":
          chapters = 5

        elif text == "📘 Libro Mediano":
            chapters = 10

        else:
            chapters = 20

        await message.answer(
            "📚 Creando tu libro...\n\n⏳ Espera un momento."
        )

        await show_wait_message(message)

        response = await asyncio.to_thread(
            client.responses.create,
            model="gpt-5-nano",
            input=f"""
    Crea un libro completamente en español.

    Tema: {topic}

    Nivel: {level}

    Número de capítulos: {chapters}

    Requisitos:

    - Todo en español
    - Historia interesante
    - Diálogos naturales
    - Adecuado para el nivel
    - Añadir resumen final
    - Añadir vocabulario importante
    - Añadir preguntas de comprensión
    """
        )

        book_text = response.output_text

        os.makedirs(
            "books",
            exist_ok=True
        )

        pdf_name = f"books/spanish_book_{user_id}.pdf"

        doc = SimpleDocTemplate(pdf_name)

        styles = getSampleStyleSheet()

        safe_text = html.escape(response.output_text)
        
        formatted_text = safe_text.replace("\n", "<br/>")

        story = [
            Paragraph(
                formatted_text,
                styles["BodyText"]
            )
        ]

        doc.build(story)

        await message.answer_document(
            FSInputFile(pdf_name),
            caption="📚 Tu libro está listo."
        )

        os.remove(pdf_name)

        return
 
    if text == "🔍 Traductor":

        user_modes[
            message.from_user.id
        ] = "spanish_translator"

        await message.answer(
            "🔍 Escribe cualquier palabra."
        )

        return

    if text == "📖 Mi Libro de Vocabulario":

        cursor.execute(
            """
            SELECT word, meaning
            FROM vocabulary_book
            WHERE user_id=?
            AND language='spanish'
            ORDER BY id DESC
            """,
            (message.from_user.id,)
        )

        words = cursor.fetchall()

        if not words:

            await message.answer(
                "📖 Tu libro de vocabulario está vacío."
            )

            return

        result = "📖 Mi Libro de Vocabulario\n\n"

        for i, (word, meaning) in enumerate(words, start=1):

            result += (
                f"{i}. {word}\n"
                f"➡️ {meaning}\n\n"
            )

        await message.answer(
            result[:4000]
        )

        return

    if text == "➕ Guardar Palabra":

        user_modes[message.from_user.id] = "save_word"

        await message.answer(
            "✍️ Envía la palabra que deseas guardar."
        )

        return

    if text == "🗣 Pronunciación":

        user_modes[
            message.from_user.id
        ] = "spanish_pronunciation"

        await message.answer(
            "🎤 Envía un mensaje de voz en español."
        )

        return

    if text == "⭐ Premium Español":

        user_previous_menu[
            message.from_user.id
        ] = "premium_menu"

        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="🚀 Funciones Premium")],
                [KeyboardButton(text="💳 Comprar Premium")],
                [KeyboardButton(text="⭐ Verificar Estado")],
                [KeyboardButton(text="📞 Contactar Admin")],
                [KeyboardButton(text="⬅️ Volver")]
            ],
            resize_keyboard=True
        )

        await message.answer(
            "⭐ Premium Español",
            reply_markup=keyboard
        )

        return

    if text == "🚀 Funciones Premium":

        user_previous_menu[
            message.from_user.id
        ] = "premium_functions"

        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="✍️ Writing Coach")],
                [KeyboardButton(text="🧠 Profesor Personal")],
                [KeyboardButton(text="🗣 Conversación Premium")],
                [KeyboardButton(text="🎯 Simulador DELE")],
                [KeyboardButton(text="📈 Mi Progreso")],
                [KeyboardButton(text="⬅️ Volver")]
            ],
            resize_keyboard=True
        )

        await message.answer(
            "⭐ Funciones Premium",
            reply_markup=keyboard
        )

        return
 
    if text == "🎯 Simulador DELE":

        await bot.send_chat_action(
            chat_id=message.chat.id,
            action=ChatAction.TYPING
        )

        if not is_spanish_premium(message.from_user.id):

            await message.answer(
                "⭐ Esta función requiere Premium Español."
            )

            return

        cursor.execute("""
        UPDATE spanish_stats
        SET dele_tests = dele_tests + 1
        WHERE user_id = ?
        """, (message.from_user.id,))

        conn.commit()

        await message.answer(
            "🎯 Elige tu nivel:\n\n"
            "A1\n"
            "A2\n"
            "B1\n"
            "B2"
        )

        return

    if text in ["A1", "A2", "B1", "B2"]:

        await message.answer(
            f"🎯 Simulador DELE {text}\n\n"
            "1. Lee el texto.\n"
            "2. Responde las preguntas.\n"
            "3. Escribe una respuesta corta.\n"
            "4. Practica conversación."
        )

        return

    if text == "📈 Mi Progreso":

        await bot.send_chat_action(
            chat_id=message.chat.id,
            action=ChatAction.TYPING
        )

        if not is_spanish_premium(message.from_user.id):

            await message.answer(
                "⭐ Esta función requiere Premium Español."
            )

            return

        cursor.execute("""
        SELECT
            words_learned,
            exercises_completed,
            dele_tests
        FROM spanish_stats
        WHERE user_id = ?
        """, (message.from_user.id,))

        data = cursor.fetchone()

        words = data[0]
        exercises = data[1]
        tests = data[2]

        await message.answer(
            f"📈 Tus estadísticas\n\n"
            f"📚 Palabras aprendidas: {words}\n"
            f"📝 Ejercicios completados: {exercises}\n"
            f"🎯 Exámenes DELE: {tests}"
        )

        return

    if text == "✍️ Writing Coach":

        if not is_spanish_premium(message.from_user.id):

            await message.answer(
                "⭐ Esta función requiere Premium Español."
            )

            return

        user_modes[
            message.from_user.id
        ] = "premium_writing"

        await message.answer(
            "✍️ Escribe cualquier texto en español."
        )

        return

    if text == "🧠 Profesor Personal":

        await bot.send_chat_action(
            chat_id=message.chat.id,
            action=ChatAction.TYPING
        )

        if not is_spanish_premium(message.from_user.id):

            await message.answer(
                "⭐ Esta función requiere Premium Español."
            )

            return

        user_modes[
            message.from_user.id
        ] = "premium_teacher"

        await message.answer(
            "🎯 ¿Cuál es tu objetivo?\n\n"
            "✈️ Viajar\n"
            "💼 Trabajo\n"
            "🎓 DELE\n"
            "🗣 Conversación\n"
            "📚 Desde cero"
        )

        return

    if text == "🗣 Conversación Premium":

        await bot.send_chat_action(
            chat_id=message.chat.id,
            action=ChatAction.TYPING
        )

        if not is_spanish_premium(message.from_user.id):

            await message.answer(
                "⭐ Esta función requiere Premium Español."
            )

            return

        user_previous_menu[
            message.from_user.id
        ] = "premium_conversation_menu"

        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="✈️ Aeropuerto")],
                [KeyboardButton(text="🏨 Hotel")],
                [KeyboardButton(text="🍽 Restaurante")],
                [KeyboardButton(text="💼 Entrevista de Trabajo")],
                [KeyboardButton(text="❤️ Citas")],
                [KeyboardButton(text="🛒 Compras")],
                [KeyboardButton(text="⬅️ Volver")]
            ],
            resize_keyboard=True
        )

        await message.answer(
            "🗣 Elige una situación:",
            reply_markup=keyboard
        )
  
        return

    if text in [
        "✈️ Aeropuerto",
        "🏨 Hotel",
        "🍽 Restaurante",
        "💼 Entrevista de Trabajo",
        "❤️ Citas",
        "🛒 Compras"
    ]:

        user_previous_menu[
            message.from_user.id
        ] = "premium_conversation_menu"

        user_modes[
            message.from_user.id
        ] = "premium_conversation"

        user_conversation_topics[
            message.from_user.id
        ] = text

        await message.answer(
            f"🗣 Conversación iniciada: {text}\n\n"
            "Escribe tu primer mensaje."
        )

        return

    if text == "⭐ Save Word":

        user_id = message.from_user.id

        if user_id not in last_word:

            await message.answer(
                "❌ No word found."
            )

            return

        cursor.execute(
            """
            INSERT INTO vocabulary_book
            (
                user_id,
                word,
                meaning
            )
            VALUES (?, ?, ?)
            """,
            (
                user_id,
                last_word[user_id],
                last_meaning[user_id]
            )
        )

        conn.commit()

        await message.answer(
            "✅ Word saved successfully."
        )

        return
 
    mode = user_modes.get(message.from_user.id)

    if mode == "premium_writing":

        await bot.send_chat_action(
            chat_id=message.chat.id,
            action=ChatAction.TYPING
        )

        languages = user_languages.get(
            message.from_user.id,
            ["English"]
        )

        await show_wait_message(message)

        response = await asyncio.to_thread(
            client.responses.create,
            model="gpt-5-nano",
            input=f"""
    You are a Spanish Writing Coach.

    Student languages:
    {", ".join(languages)}

    Correct this Spanish text:

    {text}

    Give:

    1. Correct version
    2. Mistakes
    3. Explanation in student's languages
    4. CEFR level

    """
        )

        await message.answer(
            response.output_text[:4000]
        )

        return

    if mode == "premium_teacher":

        await bot.send_chat_action(
            chat_id=message.chat.id,
            action=ChatAction.TYPING
        )

        languages = user_languages.get(
            message.from_user.id,
            ["English"]
        )

        await show_wait_message(message)

        response = await asyncio.to_thread(
            client.responses.create,
            model="gpt-5-nano",
            input=f"""
    You are a Spanish Personal Teacher.

    Student goal:

    {text}

    Student languages:
    {", ".join(languages)}

    Create:

    1. Current level estimation
    2. 30 day study plan
    3. Daily tasks
    4. Vocabulary goals
    5. Grammar goals

    Explain in the student's languages.
    """
        )

        await message.answer(
            response.output_text[:4000]
        )

        user_modes.pop(
            message.from_user.id,
            None
        )

        return

    if mode == "premium_conversation":

        topic = user_conversation_topics.get(
            message.from_user.id,
            "General"
        )

        languages = user_languages.get(
            message.from_user.id,
            ["English"]
        )
       
        response = await asyncio.to_thread(
            client.responses.create,
            model="gpt-5-nano",
            input=f"""
    You are a Spanish conversation partner.

    Scenario:
    {topic}

    Student languages:
    {", ".join(languages)}

    Rules:

    1. Continue the roleplay.
    2. Speak naturally in Spanish.
    3. Correct important mistakes.
    4. Explain corrections in student's languages.
    5. Keep the conversation going.

    Student:

    {text}
    """
        )

        await message.answer(
            response.output_text[:4000]
        )

        return

    if mode == "spanish_teacher":

        await bot.send_chat_action(
            chat_id=message.chat.id,
            action=ChatAction.TYPING
        )

        await show_wait_message(message)

        response = await asyncio.to_thread(
            client.responses.create,
            model="gpt-5-nano",
            input=f"""
    Eres profesor de español.

    Alumno:

    {text}

    Corrige errores.
    Explica gramática.
    Responde en español.
    """
        )

        await message.answer(
            response.output_text[:4000]
        )

        return

    course = user_course.get(
        message.from_user.id
    )

    if mode in [
        "ielts_speaking_voice",
        "cefr_speaking_voice"
    ] and text not in [

        "Back",

        "⭐ Premium",

        "🚀 Premium Features",

        "🎙 Voice Chat",

        "🥗 Food Analyzer",

        "📚 Vocabulary",

        "📝 Grammar",

        "📖 Reading",

        "🎤 Speaking",

        "🎯 IELTS",

        "🤖 AI Teacher",

        "📖 My Vocabulary Book",

        "IELTS Speaking",

        "CEFR Speaking"
    ]:

        await message.answer(
            "❌ Please answer using voice messages only."
        )

        return

    cursor.execute(
        """
        INSERT INTO chat_history
        (user_id, role, message)
        VALUES (?, ?, ?)
        """,
        (
            message.from_user.id,
            "USER",
            text
        )
    )

    conn.commit()

    cursor.execute(
        "INSERT OR REPLACE INTO activity (user_id, last_active) VALUES (?, ?)",
        (
            message.from_user.id,
            datetime.now().strftime("%Y-%m-%d")
        )
    )

    conn.commit()

    if text == "/stats":

        if message.from_user.id != ADMIN_ID:
            return

        cursor.execute(
            "SELECT COUNT(*) FROM users"
        )

        total_users = cursor.fetchone()[0]

        cursor.execute(
            "SELECT COUNT(*) FROM premium_users"
        )

        premium_users = cursor.fetchone()[0]

        today = datetime.now().strftime("%Y-%m-%d")

        cursor.execute(
            "SELECT COUNT(*) FROM activity WHERE last_active=?",
            (today,)
        )
 
        active_today = cursor.fetchone()[0]

        await message.answer(
            f"📊 Bot Statistics\n\n"
            f"👥 Total Users: {total_users}\n"
            f"⭐ Premium Users: {premium_users}\n"
            f"🔥 Active Today: {active_today}"
        )

        return

    if text.startswith("/addpremium"):

        if message.from_user.id != ADMIN_ID:
            return

        try:
            user_id = int(text.split()[1])

            expire_date = (
                datetime.now() + timedelta(days=30)
            ).strftime("%Y-%m-%d")

            cursor.execute(
                """
                INSERT OR REPLACE INTO premium_users
                (user_id, expire_date)
                VALUES (?, ?)
                """,
                (user_id, expire_date)
            )

            conn.commit()

            await message.answer(
                f"✅ Premium added!\n\n"
                f"👤 User: {user_id}\n"
                f"📅 Expires: {expire_date}"
            )

        except:
            await message.answer(
                "Usage:\n/addpremium USER_ID"
            )

        return
           
    if text.startswith("/removepremium"):

        if message.from_user.id != ADMIN_ID:
            return

        try:
            user_id = int(text.split()[1])

            cursor.execute(
                "DELETE FROM premium_users WHERE user_id=?",
                (user_id,)
            )

            conn.commit()

            await message.answer(
                f"❌ Premium removed:\n{user_id}"
            )

        except:
            await message.answer(
                "Usage:\n/removepremium USER_ID"
            )

        return

    if text == "/listpremium":

        if message.from_user.id != ADMIN_ID:
            return

        cursor.execute(
            "SELECT user_id FROM premium_users"
        )

        users = cursor.fetchall()

        if not users:
            await message.answer(
                "No premium users."
            )
            return

        result = "⭐ Premium Users:\n\n"

        for user in users:
            result += f"{user[0]}\n"

        await message.answer(result)

        return
    
    if text == "📤 Send Payment Screenshot":

        user_modes[message.from_user.id] = "waiting_payment"

        await message.answer(
            "📸 After completing the payment, please send your payment screenshot here."

        )
      
        return

    if text == "🎙 Voice Chat":

        await bot.send_chat_action(
            chat_id=message.chat.id,
            action=ChatAction.TYPING
        )

        if not is_english_premium(message.from_user.id):

            await message.answer(
                "⭐ This feature is available only for Premium users."
            )
 
            return

        user_modes[message.from_user.id] = "voice"

        await message.answer(
            "🎙 Voice Chat activated.\n\nSend a voice message."
        )

        return
        
    if text == "🤖 AI Teacher":

        await bot.send_chat_action(
            chat_id=message.chat.id,
            action=ChatAction.TYPING
        )

        user_modes[message.from_user.id] = "teacher"

        await message.answer(
            "🤖 AI Teacher Activated\n\n"
            "✅ Send text\n"
            "✅ Send voice messages\n"
            "✅ Send photos\n\n"
            "Ask an question in English."
        )

        return

    if text == "📚 Vocabulary":

        user_modes[message.from_user.id] = "choose_languages"

        user_languages[message.from_user.id] = []

        language_keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="🔍 Search Language")],
                [KeyboardButton(text="🌐 Show Languages")],
                [KeyboardButton(text="✅ Done")],
                [KeyboardButton(text="Back")]
            ],
            resize_keyboard=True
        )

        await message.answer(
            "🌍 Vocabulary Translator\n\nChoose up to 5 languages.",
            reply_markup=language_keyboard
        )

        return
     
    if text == "🌐 Show Languages":

        result = "🌍 Available Languages\n\n"

        for lang in LANGUAGES:
            result += f"• {lang}\n"

        result += "\nChoose a language by typing its name."

        await message.answer(result[:4000])

        return 

    if text == "Back":

        user_modes.pop(
            message.from_user.id,
            None
        )

        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="📚 Vocabulary"), KeyboardButton(text="📝 Grammar")],
                [KeyboardButton(text="📖 Reading"), KeyboardButton(text="🎤 Speaking")],
                [KeyboardButton(text="🎯 Writing"), KeyboardButton(text="🤖 AI Teacher")],
                [KeyboardButton(text="📖 My Vocabulary Book"), KeyboardButton(text="⭐ Premium")],
                [KeyboardButton(text="🌐 Languages")]
            ],
            resize_keyboard=True
        )

        await message.answer(
            "🏠 Main Menu",
            reply_markup=keyboard
        )

        return

    if text == "✅ Done":

        await bot.send_chat_action(
            chat_id=message.chat.id,
            action=ChatAction.TYPING
        )

        selected = user_languages.get(
            message.from_user.id,
            []
        )

        if not selected:

            await message.answer(
                "❌ Select at least 1 language."
            )

            return

        user_modes[
            message.from_user.id
        ] = "vocabulary"

        await message.answer(
            f"✅ Languages selected:\n\n"
            f"{', '.join(selected)}\n\n"
            f"Now send any English word."
        )

        return

    if (
        user_modes.get(message.from_user.id)
        == "choose_languages"
    ):

        selected = user_languages.get(
            message.from_user.id,
            []
        )

        if text in selected:

            await message.answer(
                "❌ Language already selected."
            )

            return

        if len(selected) >= 5:

            await message.answer(
                "❌ Maximum 5 languages allowed."
            )

            return

        selected.append(text)

        user_languages[
            message.from_user.id
        ] = selected

        await message.answer(
            f"✅ Added: {text}\n\n"
            f"Selected: {len(selected)}/5"
        )

        return

    if text == "📝 Grammar":

        user_modes.pop(
            message.from_user.id,
            None
        )
     
        grammar_keyboard = ReplyKeyboardMarkup(
            keyboard=[
               [KeyboardButton(text="🕒 Tenses")],
               [KeyboardButton(text="⚡ Modal Verbs")],
               [KeyboardButton(text="📚 Nouns")],
               [KeyboardButton(text="📝 Pronouns")],
               [KeyboardButton(text="🔗 Prepositions")],
               [KeyboardButton(text="🚀 Advanced Grammar")],
               [KeyboardButton(text="🎯 IELTS Grammar")],
               [KeyboardButton(text="Back")]
            ],
            resize_keyboard=True
        )

        await message.answer(
            "📚 Choose Grammar Category:",
            reply_markup=grammar_keyboard
        )

        return
    
    if text == "🕒 Tenses":

        await bot.send_chat_action(
            chat_id=message.chat.id,
            action=ChatAction.TYPING
        ) 

        tenses_keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="Present Simple")],
                [KeyboardButton(text="Present Continuous")],
                [KeyboardButton(text="Present Perfect")],
                [KeyboardButton(text="Present Perfect Continuous")],

                [KeyboardButton(text="Past Simple")],
                [KeyboardButton(text="Past Continuous")],
                [KeyboardButton(text="Past Perfect")],
                [KeyboardButton(text="Past Perfect Continuous")],

                [KeyboardButton(text="Future Simple")],
                [KeyboardButton(text="Future Continuous")],
                [KeyboardButton(text="Future Perfect")],
                [KeyboardButton(text="Future Perfect Continuous")],

                [KeyboardButton(text="Back")]
            ],
            resize_keyboard=True
        )

        await message.answer(
            "🕒 Choose a Tense:",
            reply_markup=tenses_keyboard
        )
   
        return
    
    if text == "⚡ Modal Verbs":

        await bot.send_chat_action(
            chat_id=message.chat.id,
            action=ChatAction.TYPING
        )

        modal_keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="Can and Could")],
                [KeyboardButton(text="May and Might")],
                [KeyboardButton(text="Must and Have To")],
                [KeyboardButton(text="Should and Ought To")],
                [KeyboardButton(text="Need To")],
                [KeyboardButton(text="Would")],
                [KeyboardButton(text="Back")]
            ],
            resize_keyboard=True
        )

        await message.answer(
            "⚡ Choose a Modal Verb Topic:",
            reply_markup=modal_keyboard
        )

        return

    if text == "📚 Nouns":

        await bot.send_chat_action(
            chat_id=message.chat.id,
            action=ChatAction.TYPING
        ) 

        nouns_keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="Countable Nouns")],
                [KeyboardButton(text="Uncountable Nouns")],
                [KeyboardButton(text="Plural Nouns")],
                [KeyboardButton(text="Possessive Nouns")],
                [KeyboardButton(text="Collective Nouns")],
                [KeyboardButton(text="Abstract Nouns")],
                [KeyboardButton(text="Concrete Nouns")],

                [KeyboardButton(text="Back")]
            ],
            resize_keyboard=True
        )   

        await message.answer(
            "📚 Choose a Noun Topic:",
            reply_markup=nouns_keyboard
        )

        return

    if text == "📝 Pronouns":

        await bot.send_chat_action(
            chat_id=message.chat.id,
            action=ChatAction.TYPING
        )

        pronouns_keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="Personal Pronouns")],
                [KeyboardButton(text="Possessive Pronouns")],
                [KeyboardButton(text="Reflexive Pronouns")],
                [KeyboardButton(text="Relative Pronouns")],
                [KeyboardButton(text="Demonstrative Pronouns")],
                [KeyboardButton(text="Indefinite Pronouns")],
                [KeyboardButton(text="Interrogative Pronouns")],

                [KeyboardButton(text="Back")]
            ],
            resize_keyboard=True
        )

        await message.answer(
             "📝 Choose a Pronoun Topic:",
             reply_markup=pronouns_keyboard
        )

        return
             
    if text == "🔗 Prepositions":

        await bot.send_chat_action(
            chat_id=message.chat.id,
            action=ChatAction.TYPING
        )

        prep_keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="Prepositions of Time")],
                [KeyboardButton(text="Prepositions of Place")],
                [KeyboardButton(text="Prepositions of Movement")],
                [KeyboardButton(text="Common Prepositions")],
                [KeyboardButton(text="Prepositional Phrases")],

                [KeyboardButton(text="Back")]
            ],
            resize_keyboard=True
        )

        await message.answer(
            "🔗 Choose a Preposition Topic:",
            reply_markup=prep_keyboard
        )

        return

    if text == "🚀 Advanced Grammar":

        await bot.send_chat_action(
            chat_id=message.chat.id,
            action=ChatAction.TYPING
        )

        advanced_keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="Conditionals")],
                [KeyboardButton(text="Passive Voice")],
                [KeyboardButton(text="Reported Speech")],
                [KeyboardButton(text="Relative Clauses")],
                [KeyboardButton(text="Question Tags")],
                [KeyboardButton(text="Gerunds and Infinitives")],
                [KeyboardButton(text="Phrasal Verbs")],
                [KeyboardButton(text="Inversion")],
                [KeyboardButton(text="Subjunctive Mood")],

                [KeyboardButton(text="Back")]
            ],
            resize_keyboard=True
        )

        await message.answer(
            "🚀 Choose an Advanced Grammar Topic:",
            reply_markup=advanced_keyboard
        )

        return

    if text == "🎯 IELTS Grammar":

        await bot.send_chat_action(
            chat_id=message.chat.id,
            action=ChatAction.TYPING
        )

        ielts_grammar_keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="Grammar for Writing Task 1")],
                [KeyboardButton(text="Grammar for Writing Task 2")],
                [KeyboardButton(text="Complex Sentences")],
                [KeyboardButton(text="Linking Words")],
                [KeyboardButton(text="Academic Vocabulary")],
                [KeyboardButton(text="Formal English")],
                [KeyboardButton(text="Band 7+ Grammar")],
                [KeyboardButton(text="Band 8+ Grammar")],

                [KeyboardButton(text="Back")]
            ],
            resize_keyboard=True
        )

        await message.answer(
            "🎯 Choose an IELTS Grammar Topic:",
            reply_markup=ielts_grammar_keyboard
        )

        return

    if text == "📖 Reading":

        await bot.send_chat_action(
            chat_id=message.chat.id,
            action=ChatAction.TYPING
        )

        await show_wait_message(message)

        response = await asyncio.to_thread(
            client.responses.create,
            model="gpt-5-nano",
            input=f"""
        Create a realistic IELTS Academic Reading test.

        Requirements:
        - 300-500 words
        - Academic topic
        - IELTS style
        - Include title
        - Include 5 multiple choice questions
        - Include 5 True/False/Not Given questions
        - Do NOT show answers immediately
        """
        )

        await message.answer(response.output_text[:4000])
            
        return
   
    if text == "🎤 Speaking":

        speaking_keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="IELTS Speaking")],
                [KeyboardButton(text="CEFR Speaking")],
                [KeyboardButton(text="Back")]
            ],
            resize_keyboard=True
        )

        await message.answer(
            "Choose Speaking type:",
            reply_markup=speaking_keyboard
        )

        return
        
    if text == "IELTS Speaking":

        await bot.send_chat_action(
            chat_id=message.chat.id,
            action=ChatAction.TYPING
        )

        user_modes[message.from_user.id] = "ielts_speaking_voice"

        await show_wait_message(message)

        response = await asyncio.to_thread(
            client.responses.create,
            model="gpt-5-nano",
            input=f"""
        You are an IELTS examiner.

        Generate:

        - IELTS Speaking Part 1 (5 questions)
        - IELTS Speaking Part 2 (1 cue card)
        - IELTS Speaking Part 3 (5 questions)

        Do not provide answers.
        """
        )

        await message.answer(response.output_text[:4000])

        return   

    if text == "CEFR Speaking":

        await bot.send_chat_action(
            chat_id=message.chat.id,
            action=ChatAction.TYPING
        )

        user_modes[message.from_user.id] = "cefr_speaking_voice"

        await show_wait_message(message)

        response = await asyncio.to_thread(
            client.responses.create,
            model="gpt-5-nano",
            input=f"""
    Create a CEFR Speaking practice test.

    Include:

    - B1 level speaking questions
    - B2 level speaking questions
    - C1 level speaking questions

    10 questions total.

    Do not provide answers.
    """
        )

        await message.answer(response.output_text[:4000])

        return

    if text == "🎯 Writing":

        ielts_keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="📊 IELTS Writing Task 1")],
                [KeyboardButton(text="✍️ IELTS Writing Task 2")],
                [KeyboardButton(text="Back")]
            ],
            resize_keyboard=True
        )

        await message.answer(
            "Choose IELTS section:",
            reply_markup=ielts_keyboard
        )

        return

    if text == "IELTS Writing":

        if not is_premium(message.from_user.id):
            await message.answer(
                "🔒 This feature is Premium."
            )
            return

        await message.answer(
            "IELTS Writing Task 2:\n\nSome people think online learning is better than traditional learning. Discuss both views and give your opinion."
        )

        return

    if text == "📊 IELTS Writing Task 1":

        user_modes[message.from_user.id] = (
            "ielts_writing_task1"
        )

        images = [
            file
            for file in os.listdir("graphs")
            if file.endswith((".jpg", ".jpeg", ".png"))
        ]

        image_name = random.choice(images)

        image_path = os.path.join(
            "graphs",
            image_name
        )

        await bot.send_photo(
            chat_id=message.chat.id,
            photo=FSInputFile(
                image_path
            ),
            caption=
            "📊 IELTS Writing Task 1\n\n"
            "Write your Task 1 essay based on this graph.\n\n"
            "📝 Write at least 150 words.\n"
            "⏱ Recommended time: 20 minutes.\n"
            "📈 Summarize the main features and make comparisons where relevant."
)
        
        return

    if text == "✍️ IELTS Writing Task 2":

        await bot.send_chat_action(
            chat_id=message.chat.id,
            action=ChatAction.TYPING
        )

        user_id = message.from_user.id

        if user_id not in used_task2:
            used_task2[user_id] = []

        available = [
            q
            for q in task2_questions
            if q not in used_task2[user_id]
        ]

        if not available:
            used_task2[user_id] = []
            available = task2_questions.copy()

        question = random.choice(available)

        used_task2[user_id].append(question)

        user_modes[user_id] = "ielts_writing_task2"

        await message.answer(
            f"✍️ IELTS Writing Task 2\n\n"
            f"{question}\n\n"
            f"📝 Write at least 250 words.\n"
            f"⏱ Recommended time: 40 minutes.\n"
            f"📌 Support your ideas with reasons and examples."
        )

        return

    if text == "Band Score Checker":

       await message.answer(
           "Send me your IELTS Speaking or Writing answer and I will estimate your band score."
       )

       return

    if text == "⭐ Premium":

         await bot.send_chat_action(
             chat_id=message.chat.id,
             action=ChatAction.TYPING
         )

         premium_keyboard = ReplyKeyboardMarkup(
             keyboard=[
                 [KeyboardButton(text="🚀 Premium Features")],
                 [KeyboardButton(text="💳 Buy Premium")],
                 [KeyboardButton(text="📤 Send Payment Screenshot")],
                 [KeyboardButton(text="⭐ Check Status")],
                 [KeyboardButton(text="📞 Contact Admin")],
                 [KeyboardButton(text="Back")]
             ],
             resize_keyboard=True
         )

         await message.answer(
             "⭐ Premium Menu",
             reply_markup=premium_keyboard
         )

         return

    if text == "🎵 Shadowing":

        await bot.send_chat_action(
            chat_id=message.chat.id,
            action=ChatAction.TYPING
        )

        shadowing_keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="🟢 Beginner A1")],
                [KeyboardButton(text="🔵 Elementary A2")],
                [KeyboardButton(text="🟡 Intermediate B1")],
                [KeyboardButton(text="🟠 Upper Intermediate B2")],
                [KeyboardButton(text="🔴 Advanced C1")],
                [KeyboardButton(text="⚫ Pro C2")],
                [KeyboardButton(text="Back")]
            ],
            resize_keyboard=True
        )

        await message.answer(
            "🎵 Choose your level:",
            reply_markup=shadowing_keyboard
        )

        return
        
    if text == "🟢 Beginner A1":
         
        await bot.send_chat_action(
            chat_id=message.chat.id,
            action=ChatAction.TYPING
        )

        folder = "shadowing"

        audio_files = [
            file
            for file in os.listdir(folder)
            if file.endswith(".mp3")
        ]

        if not audio_files:

            await message.answer(
                "❌ No A1 dialogues found."
            )

            return

        selected_audio = random.choice(
            audio_files
        )

        audio_path = os.path.join(
            folder,
            selected_audio
        )

        with open(
            audio_path,
            "rb"
        ) as audio_file:

            transcript = (
                client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file
                )
            )

        original_text = transcript.text

        shadowing_text[
            message.from_user.id
        ] = original_text

        await bot.send_audio(
            chat_id=message.chat.id,
            audio=FSInputFile(audio_path)
        )

        await message.answer(
            f"📄 Transcript:\n\n{original_text}"
        )

        await message.answer(
            "🎙 Listen and repeat.\n\nSend a voice message after practicing."
        )

        user_modes[
            message.from_user.id
        ] = "shadowing"

        return

    if text == "🔵 Elementary A2":

        await bot.send_chat_action(
            chat_id=message.chat.id,
            action=ChatAction.TYPING
        )

        folder = "shadowing"

        audio_files = [
            file
            for file in os.listdir(folder)
            if file.endswith(".mp3")
        ]

        if not audio_files:

            await message.answer(
                "❌ No A2 dialogues found."
            )

            return

        selected_audio = random.choice(
            audio_files
        )

        audio_path = os.path.join(
            folder,
            selected_audio
        )

        with open(audio_path, "rb") as audio_file:

            transcript = (
                client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file
                )
            )

        original_text = transcript.text

        shadowing_text[
            message.from_user.id
        ] = original_text

        await bot.send_audio(
            chat_id=message.chat.id,
            audio=FSInputFile(audio_path)
        )

        await message.answer(
            f"📄 Transcript:\n\n{original_text}"
        )

        await message.answer(
            "🎙 Listen and repeat.\n\nSend a voice message after practicing."
        )

        user_modes[
            message.from_user.id
        ] = "shadowing"

        return

    if text == "🟡 Intermediate B1":

        await bot.send_chat_action(
            chat_id=message.chat.id,
            action=ChatAction.TYPING
        )

        folder = "shadowing"

        audio_files = [
            file
            for file in os.listdir(folder)
            if file.endswith(".mp3")
        ]

        if not audio_files:
            await message.answer("❌ No B1 dialogues found.")
            return

        selected_audio = random.choice(audio_files)

        audio_path = os.path.join(
            folder,
            selected_audio
        )

        with open(audio_path, "rb") as audio_file:

            transcript = (
                client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file
                )
            )

        original_text = transcript.text

        shadowing_text[
            message.from_user.id
        ] = original_text

        await bot.send_audio(
            chat_id=message.chat.id,
            audio=FSInputFile(audio_path)
        )

        await message.answer(
            f"📄 Transcript:\n\n{original_text}"
        )

        await message.answer(
            "🎙 Listen and repeat.\n\nSend a voice message after practicing."
        )

        user_modes[
            message.from_user.id
        ] = "shadowing"

        return

    if text == "🟠 Upper Intermediate B2":

        await bot.send_chat_action(
            chat_id=message.chat.id,
            action=ChatAction.TYPING
        )

        folder = "shadowing"

        audio_files = [
            file
            for file in os.listdir(folder)
            if file.endswith(".mp3")
        ]

        if not audio_files:

            await message.answer(
                "❌ No B2 dialogues found."
            )

            return

        selected_audio = random.choice(
            audio_files
        )

        audio_path = os.path.join(
            folder,
            selected_audio
        )

        with open(audio_path, "rb") as audio_file:

            transcript = (
                client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file
                )
            )

        original_text = transcript.text

        shadowing_text[
            message.from_user.id
        ] = original_text

        await bot.send_audio(
            chat_id=message.chat.id,
            audio=FSInputFile(audio_path)
        )

        await message.answer(
            f"📄 Transcript:\n\n{original_text}"
        )

        await message.answer(
            "🎙 Listen and repeat.\n\nSend a voice message after practicing."
        )

        user_modes[
            message.from_user.id
        ] = "shadowing"

        return

    if text == "🔴 Advanced C1":

        await bot.send_chat_action(
            chat_id=message.chat.id,
            action=ChatAction.TYPING
        )

        folder = "shadowing"

        audio_files = [
            file
            for file in os.listdir(folder)
            if file.endswith(".mp3")
        ]

        if not audio_files:

            await message.answer(
                "❌ No C1 dialogues found."
            )

            return

        selected_audio = random.choice(
            audio_files
        )

        audio_path = os.path.join(
            folder,
            selected_audio
        )

        with open(audio_path, "rb") as audio_file:

            transcript = (
                client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file
                )
            )

        original_text = transcript.text

        shadowing_text[
            message.from_user.id
        ] = original_text

        await bot.send_audio(
            chat_id=message.chat.id,
            audio=FSInputFile(audio_path)
        )

        await message.answer(
            f"📄 Transcript:\n\n{original_text}"
        )

        await message.answer(
            "🎙 Listen and repeat.\n\nSend a voice message after practicing."
        )

        user_modes[
            message.from_user.id
        ] = "shadowing"

        return

    if text == "⚫ Pro C2":

        await bot.send_chat_action(
            chat_id=message.chat.id,
            action=ChatAction.TYPING
        )

        folder = "shadowing"

        audio_files = [
            file
            for file in os.listdir(folder)
            if file.endswith(".mp3")
        ]

        if not audio_files:

            await message.answer(
                "❌ No C2 dialogues found."
            )

            return

        selected_audio = random.choice(
            audio_files
        )

        audio_path = os.path.join(
            folder,
            selected_audio
        )

        with open(audio_path, "rb") as audio_file:

            transcript = (
                client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file
                )
            )

        original_text = transcript.text

        shadowing_text[
            message.from_user.id
        ] = original_text

        await bot.send_audio(
            chat_id=message.chat.id,
            audio=FSInputFile(audio_path)
        )

        await message.answer(
            f"📄 Transcript:\n\n{original_text}"
        )

        await message.answer(
            "🎙 Listen and repeat.\n\nSend a voice message after practicing."
        )

        user_modes[
            message.from_user.id
        ] = "shadowing"

        return 

    if text == "🚀 Premium Features":

        await bot.send_chat_action(
            chat_id=message.chat.id,
            action=ChatAction.TYPING
        )

        if not is_premium(message.from_user.id):
            await message.answer(
                "🔒 Premium required."
            )
            return

        premium_features_keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="🤖 AI Conversation Partner")],
                [KeyboardButton(text="📚 Read Books")],
                [KeyboardButton(text="🔊 Pronunciation Trainer")],
                [KeyboardButton(text="📊 CEFR Level Test")],
                [KeyboardButton(text="📜 Chat History")],
                [KeyboardButton(text="🥗 Food Analyzer")],
                [KeyboardButton(text="🎙 Voice Chat")],
                [KeyboardButton(text="🎵 Shadowing")],                
                [KeyboardButton(text="Back")]
            ],
            resize_keyboard=True
        )

        await message.answer(
            "🚀 Premium Features",
            reply_markup=premium_features_keyboard
        )

        return

    if text == "⭐ Check Status":

        await bot.send_chat_action(
            chat_id=message.chat.id,
            action=ChatAction.TYPING
        )

        if is_premium(message.from_user.id):

            info = get_premium_info(
                message.from_user.id
            )

            expire_date = datetime.strptime(
                info[0],
                "%Y-%m-%d"
            )

            days_left = (
                expire_date - datetime.now()
            ).days

            await message.answer(
                f"✅ Premium Active\n\n"
                f"📅 Expires: {info[0]}\n"
                f"⏳ Days Left: {days_left}"
            )

        else:

            await message.answer(
                "❌ You do not have Premium."
            )

        return
    
    if text == "📚 Add to Vocabulary Book":

        await bot.send_chat_action(
            chat_id=message.chat.id,
            action=ChatAction.TYPING
        )

        user_id = message.from_user.id

        word = last_word.get(user_id)

        if not word:

            await message.answer(
                "❌ No word found."
            )

            return

        cursor.execute(
            """
            INSERT INTO saved_words
            (user_id, word)
            VALUES (?, ?)
            """,
            (user_id, word)
        )

        conn.commit()

        await message.answer(
            f"📚 Added to Vocabulary Book:\n\n{word}"
        )

        return

    if text == "📖 My Vocabulary Book":

        await bot.send_chat_action(
            chat_id=message.chat.id,
            action=ChatAction.TYPING
        )

        user_id = message.from_user.id

        cursor.execute(
            """
            SELECT word
            FROM saved_words
            WHERE user_id=?
            """,
            (user_id,)
        )

        rows = cursor.fetchall()

        words = [row[0] for row in rows]

        if not words:

            await message.answer(
                "📚 Vocabulary Book is empty."
            )

            return

        book_text = "\n".join(words)

        await message.answer(
            f"📚 My Vocabulary Book:\n\n{book_text}"
        )

        return

    if text == "💳 Buy Premium":

        await message.answer(

            "⭐ PREMIUM MEMBERSHIP\n\n"

            "🔥 Premium Features:\n\n"

            "✅ AI Conversation Partner\n"
            "✅ Voice Chat\n"
            "✅ Pronunciation Trainer\n"
            "✅ Shadowing Practice\n"
            "✅ IELTS Writing Band Score Checker\n"
            "✅ IELTS Speaking Band Score Checker\n"
            "✅ CEFR Level Test\n"
            "✅ Food Analyzer\n"
            "✅ AI Book Generator\n"
            "✅ Personal Vocabulary Book\n"
            "✅ Chat History\n"
            "✅ Priority Support\n\n"

            "💰 Price: 65 000 UZS / Month\n\n"
            "💰 Price: 5$ USD / Month\n\n"

            "💳 Card Number:\n\n"

            "UZCARD: 5614683512720285\n\n"
            "VISA: 4413597600226672\n\n"

            "👤 Card Holder:\n"
            "Alimov S.\n\n"

            "After payment:\n"
            "📤 Send Payment Screenshot"
        ) 

        user_modes[message.from_user.id] = "waiting_payment"

        return
    
    if text == "💳 Buy Premium":

        user_modes[message.from_user.id] = "waiting_payment"

        await message.answer(
            "💳 Premium price: 20 000 UZS\n\n"
            "Card:\n"
            "5614683512720285\n\n"
            "4413597600226672\n\n"
            "Send payment screenshot."
        )

        return

    if text == "💳 Comprar Premium":

        user_modes[message.from_user.id] = "waiting_payment"

        await message.answer(
            "⭐ PREMIUM ESPAÑOL ⭐\n\n"
            "🚀 Funciones Premium:\n"
            "• ✍️ Writing Coach\n"
            "• 🧠 Profesor Personal IA\n"
            "• 🗣️ Conversación Premium\n"
            "• 🎯 Simulador DELE\n"
            "• 📈 Mi Progreso\n"
            "• 🔥 Plan Diario Personalizado\n\n"
            "💳 Precio: 55,000 UZS / mes\n"
            "💳 Precio: 5$ USD / mes\n\n"
            "🏦 Método de pago:\n\n"
            "Tarjeta: 5614683512720285\n"
            "Tarjeta: 4413597600226672\n\n"
            "Nombre: Alimov S. \n\n"
            "📸 Después del pago, envía una captura de pantalla.\n"
            "El administrador verificará tu pago y activará Premium.\n\n"
            "⚠️ Envía solamente capturas de pagos completados."
        )

        return

    if text == "📞 Contactar Admin":

        await message.answer(
            "👨‍💻 Administrador\n\n"
            "Si tienes preguntas sobre Premium o pagos, contáctanos:\n\n"
            "Saohell"
        )

        return

    if text == "⭐ Verificar Estado":

        await bot.send_chat_action(
            chat_id=message.chat.id,
            action=ChatAction.TYPING
        )

        info = get_premium_info(
            message.from_user.id
        )

        if not info:

            await message.answer(
                "❌ No tienes Premium activo."
            )

            return

        await message.answer(
            f"✅ Premium activo\n\n"
            f"📅 Válido hasta: {info[0]}"
        )

        return

    if text == "🏆 IELTS Band Score":

        await bot.send_chat_action(
            chat_id=message.chat.id,
            action=ChatAction.TYPING
        )

        if not is_english_premium(message.from_user.id):
            await message.answer("🔒 Premium feature.")
            return

        user_modes[message.from_user.id] = "band_score"

        await message.answer(
            "Send your IELTS Writing Task 1 or Task 2 answer."
        )

        return
      
    if text == "🎤 IELTS Speaking Score":

        await bot.send_chat_action(
            chat_id=message.chat.id,
            action=ChatAction.TYPING
        ) 

        if not is_english_premium(message.from_user.id):
            await message.answer(
                "🔒 Premium feature."
            )
            return

        user_modes[message.from_user.id] = "speaking_score"

        await message.answer(
            "🎤 Send your IELTS Speaking answer."
        )

        return

    if text == "📅 Word of the Day":

        await show_wait_message(message)

        response = await asyncio.to_thread(
            client.responses.create,
            model="gpt-5-nano",
            input="Give one useful English word with meaning, Uzbek translation, Russian translation and examples."
        )
        await message.answer(response.output_text[:4000])
        return

    if text == "🤖 AI Conversation Partner":

        await bot.send_chat_action(
            chat_id=message.chat.id,
            action=ChatAction.TYPING
        )

        user_modes[message.from_user.id] = "conversation"
        await message.answer("Let's talk in English.")
        return
    
    if text == "🔊 Pronunciation Trainer":

        await bot.send_chat_action(
            chat_id=message.chat.id,
            action=ChatAction.TYPING
        )

        user_modes[message.from_user.id] = "pronunciation"

        await message.answer(
            "🎤 Send a voice message in English."
        )
    
    if text == "🔊 Pronunciation":

        await bot.send_chat_action(
            chat_id=message.chat.id,
            action=ChatAction.TYPING
        )

        word = last_word.get(
            message.from_user.id
        )

        if not word:

            await message.answer(
                "❌ No word selected."
            )

            return

        response = await asyncio.to_thread(
            client.responses.create,
            model="gpt-5-nano",
            input=f"""
    Word: {word}

    Provide:

    1. IPA pronunciation
    2. Syllables
    3. Word stress
    4. One pronunciation tip

    Keep it short and clean.
    """
        )

        await message.answer(
            response.output_text[:1500]
        ) 
      
        tts = gTTS(
            text=word,
            lang="en"
        )

        audio_path = (
            f"voices/{message.from_user.id}_word.mp3"
        ) 
 
        tts.save(audio_path)

        voice_file = FSInputFile(
            audio_path
        )

        await bot.send_voice(
            chat_id=message.chat.id,
            voice=voice_file
        )

        if os.path.exists(audio_path):
            os.remove(audio_path)

        return

    if text == "📖 My Vocabulary Book":

        await bot.send_chat_action(
            chat_id=message.chat.id,
            action=ChatAction.TYPING
        )

        cursor.execute(
            """
            SELECT word
            FROM saved_words
            WHERE user_id=?
            """,
            (message.from_user.id,)
        )

        words = cursor.fetchall()

        if not words:

            await message.answer(
                "❌ No saved words."
            )

            return

        await message.answer(
            "📚 Creating your Vocabulary Book..."
        )

        text_content = (
            "My Vocabulary Book\n\n"
        )
 
        for i, word in enumerate(words, start=1):

            text_content += (
                f"{i}. {word[0]}\n"
            )

        os.makedirs(
            "books",
            exist_ok=True
        )

        pdf_name = (
            f"books/vocab_{message.from_user.id}.pdf"
        )
 
        doc = SimpleDocTemplate(
            pdf_name
        )

        styles = getSampleStyleSheet()

        story = [
            Paragraph(
                text_content.replace(
                    "\n",
                    "<br/>"
                ),
                styles["BodyText"]
            )
        ]

        doc.build(story)

        await message.answer_document(
            FSInputFile(pdf_name),
            caption="📚 Your Vocabulary Book"
        )

        os.remove(pdf_name)

        return 

    if text == "🥗 Food Analyzer":

        await bot.send_chat_action(
            chat_id=message.chat.id,
            action=ChatAction.TYPING
        )

        user_modes[message.from_user.id] = "food_analyzer"

        await message.answer(
            "📸 Send a photo of any food, drink or product."
        )

        return

    if text == "📊 CEFR Level Test":

        await bot.send_chat_action(
            chat_id=message.chat.id,
            action=ChatAction.TYPING
        )

        user_modes[message.from_user.id] = "cefr_test"
        await message.answer("Write 150-200 words in English.")
        return
 
    if text == "📜 Chat History":

        await bot.send_chat_action(
            chat_id=message.chat.id,
            action=ChatAction.TYPING
        )

        cursor.execute(
            """
            SELECT role, message
            FROM chat_history
            WHERE user_id=?
            ORDER BY id DESC
            LIMIT 20
            """,
            (message.from_user.id,)
        )

        rows = cursor.fetchall()

        if not rows:
            await message.answer(
                "📜 No chat history found."
            )
            return

        result = "📜 Your Last Messages\n\n"

        for role, msg in reversed(rows):
            result += f"{role}: {msg[:100]}\n\n"

        await message.answer(result[:4000])

        return

    if text == "📚 Read Books":

        await bot.send_chat_action(
            chat_id=message.chat.id,
            action=ChatAction.TYPING
        )

        books_keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="📖 Adventure")],
                [KeyboardButton(text="❤️ Romance")],
                [KeyboardButton(text="🚀 Science Fiction")],
                [KeyboardButton(text="🕵️ Mystery")],
                [KeyboardButton(text="💼 Business")],
                [KeyboardButton(text="🏆 Motivation")],
                [KeyboardButton(text="🌍 Travel")],
                [KeyboardButton(text="👻 Horror")],
                [KeyboardButton(text="Back")]
            ],
            resize_keyboard=True
        )

        await message.answer(
            "📚 Choose a book topic:",
            reply_markup=books_keyboard
        )

        return


    if text in [
        "📖 Adventure",
        "❤️ Romance",
        "🚀 Science Fiction",
        "🕵️ Mystery",
        "💼 Business",
        "🏆 Motivation",
        "🌍 Travel",
        "👻 Horror"
    ]:

        user_book_topic[message.from_user.id] = text

        level_keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="🟢 Beginner A1")],
                [KeyboardButton(text="🔵 Elementary A2")],
                [KeyboardButton(text="🟡 Pre-Intermediate B1")],
                [KeyboardButton(text="🟠 Intermediate B2")],
                [KeyboardButton(text="🔴 Upper Intermediate C1")],
                [KeyboardButton(text="⚫ Pro Reader C2")],
                [KeyboardButton(text="Back")]
            ],
            resize_keyboard=True
        )

        await message.answer(
            "📚 Choose your level:",
            reply_markup=level_keyboard
        )

        return
    
    if text in [
        "🟢 Beginner A1",
        "🔵 Elementary A2",
        "🟡 Pre-Intermediate B1",
        "🟠 Intermediate B2",
        "🔴 Upper Intermediate C1",
        "⚫ Pro Reader C2"
    ]:

        if message.from_user.id not in user_book_topic:
            await message.answer("Choose a topic first.")
            return

        topic = user_book_topic[message.from_user.id]

        await message.answer(
            "📚 Creating your book...\n\nPlease wait 20-60 seconds."
        )

        await bot.send_chat_action(
            chat_id=message.chat.id,
            action=ChatAction.TYPING
        )

        await show_wait_message(message)

        response = await asyncio.to_thread(
            client.responses.create,
            model="gpt-5-nano",
            input=f"""
    Create an English reading book.

    Topic: {topic}
    Level: {text}

    Requirements:
    - Create a complete story
    - 15 chapters
    - At least 250 sentences
    - Easy reading format
    - Interesting story
    - Suitable for the selected level
    """
        )

        book_text = response.output_text

        os.makedirs("books", exist_ok=True)

        pdf_name = f"books/vocabulary_{message.from_user.id}.pdf"

        doc = SimpleDocTemplate(pdf_name)
        styles = getSampleStyleSheet()

        story = [
            Paragraph(
                book_text.replace("\n", "<br/>"),
                styles["BodyText"]
            )
        ]

        doc.build(story)

        await message.answer_document(
            FSInputFile(pdf_name),
            caption="📚 Your book is ready!"
        )

        os.remove(pdf_name)

        return

    if text == "Back":

        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="📚 Vocabulary"), KeyboardButton(text="📝 Grammar")],
                [KeyboardButton(text="📖 Reading"), KeyboardButton(text="🎤 Speaking")],
                [KeyboardButton(text="🎯 Writing"), KeyboardButton(text="🤖 AI Teacher")],
                [KeyboardButton(text="📖 My Vocabulary Book"), KeyboardButton(text="⭐ Premium")],
                [KeyboardButton(text="🌐 Languages")]
            ],
            resize_keyboard=True
        )

        user_modes.pop(
            message.from_user.id,
            None
        )

        await message.answer(
            "Main Menu",
            reply_markup=keyboard        
        )

        return

    if text in grammar_topics:

        print("GRAMMAR CLICK:", text)
        
        await show_wait_message(message)

        response = await asyncio.to_thread(
            client.responses.create,
            model="gpt-5-nano",
            input=f"""
You are an English grammar teacher.

Teach this grammar topic:

{text}

Requirements:
- Simple explanation
- Uzbek explanation
- Russian explanation
- Formula
- 10 examples
- Common mistakes
- Mini exercise with answers
"""
    )

        await message.answer(response.output_text[:4000])

        return


    mode = user_modes.get(message.from_user.id)

    if mode == "speaking_score":

        await bot.send_chat_action(
            chat_id=message.chat.id,
            action=ChatAction.TYPING
        )

        await show_wait_message(message)

        response = await asyncio.to_thread(
            client.responses.create,
            model="gpt-5-nano",
            input=f"""
    You are an IELTS examiner.

    Evaluate this IELTS Speaking answer:

    {text}

    Give:

    Overall Band Score

    Fluency and Coherence

    Lexical Resource

    Grammar Range and Accuracy

    Pronunciation

    Suggestions for improvement
    """
        )

        await message.answer(
            response.output_text[:4000]
        )

        return

    if mode == "pronunciation":

        await bot.send_chat_action(
            chat_id=message.chat.id,
            action=ChatAction.TYPING
        )

        response = await asyncio.to_thread(
            client.responses.create,
            model="gpt-5-nano",
            input=f"""
    You are an English pronunciation coach.

    Analyze:

    {text}

    Give:

    IPA pronunciation

    Syllables

    Stress

    Common mistakes

    Pronunciation tips
    """
        )

        await message.answer(
            response.output_text[:4000]
        )

        return

    if mode == "vocabulary":

        await bot.send_chat_action(
            chat_id=message.chat.id,
            action=ChatAction.TYPING
        )

        selected_languages = user_languages.get(
            message.from_user.id,
            ["Uzbek"]
        )

        languages_text = "\n".join(
            selected_languages
        )

        last_word[
            message.from_user.id
        ] = text

        await show_wait_message(message)

        response = await asyncio.to_thread(
            client.responses.create,
            model="gpt-5-nano",
            input=f"""
    English word:

    {text}

    Translate this word into:

    {languages_text}

    Also provide:

    1. Meaning
    2. Example sentence
    3. IELTS level
    4. Synonyms
    5. When to use
    Use emojis and beautiful formatting.
    """
        )

        last_meaning[
            message.from_user.id
        ] = response.output_text

        vocab_keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="🔊 Pronunciation")],
                [KeyboardButton(text="⭐ Save Word")],
                [KeyboardButton(text="📚 Add to Vocabulary Book")],
                [KeyboardButton(text="Back")]
            ],
            resize_keyboard=True
        )

        await message.answer(
            response.output_text[:4000],
            reply_markup=vocab_keyboard
        )

        return
    
    if mode == "ielts_writing_task1":

        await bot.send_chat_action(
            chat_id=message.chat.id,
            action=ChatAction.TYPING
        )

        await show_wait_message(message)

        response = await asyncio.to_thread(
            client.responses.create,
            model="gpt-5-nano",
            input=f"""
    You are an official IELTS Writing Task 1 examiner.

    Student essay:

    {text}

    Evaluate:

    1. Overall Band Score
    2. Task Achievement
    3. Coherence and Cohesion
    4. Lexical Resource
    5. Grammatical Range and Accuracy

    Give strengths.
    Give weaknesses.
    List mistakes.
    Give suggestions.

    Finally write an improved Band 8-9 version.

    Use IELTS format.
    """
        )

        await message.answer(
            response.output_text[:4000]
        )

        return
    
    if mode == "ielts_writing_task2":

        await bot.send_chat_action(
            chat_id=message.chat.id,
            action=ChatAction.TYPING
        ) 

        await show_wait_message(message)

        response = await asyncio.to_thread(
            client.responses.create,
            model="gpt-5-nano",
            input=f"""
    You are an official IELTS Writing Task 2 examiner.

    Student essay:

    {text}

    Evaluate:

    1. Overall Band Score
    2. Task Response
    3. Coherence and Cohesion
    4. Lexical Resource
    5. Grammatical Range and Accuracy

    Give strengths.
    Give weaknesses.
    List mistakes.
    Give suggestions.

    Finally write an improved Band 8-9 version.

    Use IELTS format.
    """
        )

        await message.answer(
            response.output_text[:4000]
        ) 

        return
    
    if mode == "band_score":

        await bot.send_chat_action(
            chat_id=message.chat.id,
            action=ChatAction.TYPING
        )

        await show_wait_message(message)

        response = await asyncio.to_thread(
            client.responses.create,
            model="gpt-5-nano",
            input=f"""

    You are an IELTS examiner.

    Evaluate this IELTS Writing answer.

    {text}

    Give:

    Overall Band Score
    Task Response
    Coherence and Cohesion
    Lexical Resource
    Grammar Range and Accuracy

    Show mistakes and improvements.
    """
        )

        await message.answer(
           response.output_text[:4000]
        )

        return
    
    if mode == "conversation":

        await bot.send_chat_action(
            chat_id=message.chat.id,
            action=ChatAction.TYPING
        )

        response = await asyncio.to_thread(
            client.responses.create,
            model="gpt-5-nano",
            input=f"""
    You are an English conversation partner.

    Rules:

    - Talk naturally in English.
    - Correct mistakes briefly.
    - Ask one follow-up question.
    - Be friendly and helpful.

    Safety:

    - Never help with violence.
    - Never help with threats.
    - Never help with self-harm.
    - Never help with illegal activities.
    - Never help with hacking.
    - Never help with dangerous instructions.

    If the user asks for harmful, illegal or dangerous content:

    Politely refuse and suggest a safe alternative.

    User:

    {text}
    """
        )

        await message.answer(
            response.output_text[:4000]
        )

        return
   
    if mode == "teacher":
 
        await bot.send_chat_action(
            chat_id=message.chat.id,
            action=ChatAction.TYPING
        )
     
        response = await asyncio.to_thread(
            client.responses.create,
            model="gpt-5-nano",
            input=f"""
You are Elvora Spanish Teacher.

The student is learning Spanish.

Rules:

1. Detect the language used by the student.

2. Always answer in the SAME language
   used by the student.

Examples:

- English question ->  English answer
- Russian question ->  Russian answer
- German question ->  German answer
- Uzbek question ->  Uzbek answer
- Dutch question ->  Dutch answer

3. Correct mistakes when useful.

4. Give examples in Spanish.

5. Be friendly and professional.

Student:

{text}
""" 
)

        cursor.execute(
            """
            INSERT INTO chat_history
            (user_id, role, message)
            VALUES (?, ?, ?)
            """,
            (
                message.from_user.id,
                "BOT",
                response.output_text[:4000]
            )
        )

        conn.commit()

        await message.answer(
            response.output_text[:4000]
        )
 
        return
    
    if mode == "spanish_teacher":

        await bot.send_chat_action(
            chat_id=message.chat.id,
            action=ChatAction.TYPING
        )
 
        response = await asyncio.to_thread(
            client.responses.create,
            model="gpt-5-nano",
            input=f"""
    You are Elvora Profesor IA.

    You help users learn Spanish.

    Your tasks:

    - Answer in Spanish
    - Teach grammar
    - Correct mistakes
    - Practice conversations
    - Explain vocabulary
    - Help with pronunciation
    - Be friendly and encouraging

    Rules:

    Rules:

    Rules:

    1. Answer any legal question.

    2. If the user writes in English:
       first correct mistakes.
       then explain them.
       then answer naturally.

    3. If the user writes in Dutch:
       first correct mistakes.
       then explain them.
       then answer in Dutch.

    4. If there are grammar mistakes:
       briefly correct them.

    5. If the user asks about coding:
       explain clearly.

    6. Be friendly and helpful.

    7. Keep answers clear and practical.

    8. Keep answers practical and educational.

    User:

    {text}
    """
        )

        await message.answer(
            response.output_text[:4000]
        )

        return

    if str(mode).startswith("conversation_"):

        await bot.send_chat_action(
            chat_id=message.chat.id,
            action=ChatAction.TYPING
        )

        await show_wait_message(message)

        response = await asyncio.to_thread(
            client.responses.create,
            model="gpt-5-nano",
            input=f"""
    Eres un profesor de conversación española.

    Nivel del estudiante:

    {mode}

    Reglas:

    - Habla solo en español.
    - Mantén conversaciones naturales.
    - Corrige errores brevemente.
    - Haz preguntas.
    - Motiva al estudiante.
    - No cambies al inglés.

    Mensaje del estudiante:

    {text}
    """
        )

        await message.answer(
            response.output_text[:4000]
        )

        return

    if str(mode).startswith("roleplay_"):

        await bot.send_chat_action(
            chat_id=message.chat.id,
            action=ChatAction.TYPING
        )

        await show_wait_message(message)

        response = await asyncio.to_thread(
            client.responses.create,
            model="gpt-5-nano",
            input=f"""
    Eres un personaje de este roleplay:

    {mode}

    Reglas:

    - Habla solamente en español.
    - Mantén la situación.
    - Corrige errores brevemente.
    - Haz preguntas.
    - No salgas del personaje.

    Mensaje del estudiante:

    {text}
    """
        )

        await message.answer(
            response.output_text[:4000]
        )

        return

    if mode == "vocabulary_book":

        await message.answer(
            "📚 Creating your vocabulary book..."
        )

        await show_wait_message(message)

        response = await asyncio.to_thread(
            client.responses.create,
            model="gpt-5-nano",
            input=f"""
    Create a vocabulary book.

    Words:

    {text}

    For each word provide:

    1. Word
    2. Meaning
    3. Uzbek translation
    4. Russian translation
    5. Example sentence
    """
        )

        os.makedirs(
            "books",
            exist_ok=True
        )

        pdf_name = f"vocabulary_{message.from_user.id}.pdf"

        doc = SimpleDocTemplate(pdf_name)

        styles = getSampleStyleSheet()

        story = [
            Paragraph(
                response.output_text.replace(
                    "\n",
                    "<br/>"
                ),
                styles["BodyText"]
            )
        ]

        doc.build(story)

        await message.answer_document(
            FSInputFile(pdf_name),
            caption="📚 Your Vocabulary Book is ready!"
        )

        os.remove(pdf_name)

        return
    
    if mode == "cefr_test":

        await show_wait_message(message)

        response = await asyncio.to_thread(
            client.responses.create,
            model="gpt-5-nano",
            input=f"Estimate CEFR level and explain: {text}"
        )
        await message.answer(response.output_text[:4000])
        return

async def main():
    print("Bot started...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
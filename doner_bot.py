import telebot
from groq import Groq
from datetime import datetime
import requests
import random
import io
import os
import time
from PIL import Image, ImageDraw, ImageFont

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "8994193838:AAEw732kO6FXp-RvXAY_C_VwqlWSTZCl0gw")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "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")

bot = telebot.TeleBot(TELEGRAM_TOKEN)
client = Groq(api_key=GROQ_API_KEY)

SYSTEM_PROMPT = """Ты — профессиональный SMM-менеджер кафе "Top Doner" в Уральске, Казахстан.

ИНФОРМАЦИЯ О КАФЕ:
- Название: Top Doner (@top_doner_url)
- Город: Уральск (Орал), Казахстан
- Адреса: Остановка Байтерек 6мкр | 10мкр Самал 89
- Заказ WhatsApp: wa.me/77759471561 | Яндекс Еда
- Время работы: 11:00 — 05:00 ночи (почти круглосуточно — это УТП!)
- Халяль: ДА
- Подписчики: 10.2K в Instagram

МЕНЮ И ЦЕНЫ:
- Донер Мини — 690 тг
- Донер Сырный Мини — 790 тг
- Алматинский Донер — 1200 тг + Кола в подарок (главный хит!)

СТИЛЬ КОНТЕНТА:
- Молодёжный, дерзкий, живой, с огнём
- Много эмодзи, капслок для акцентов
- Иногда вставляй казахские фразы: Дәмді! Тәтті! Кел жей!
- FOMO эффект — только сегодня, осталось мало, не упусти
- Всегда упоминай работу до 5 утра
- Призыв всегда: WhatsApp или Яндекс Еда"""

PACKAGING_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "packaging.jpg")
POLLINATIONS_BASE = "https://image.pollinations.ai/prompt/{prompt}?width=1080&height=1920&nologo=true&seed={seed}"


def ask_ai(prompt):
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": prompt}],
        max_tokens=2000,
    )
    return response.choices[0].message.content


def _fetch_image(prompt, seed):
    suffix = "формат истории Instagram, вертикальный, фотография еды, профессиональное освещение, 4k"
    url = POLLINATIONS_BASE.format(
        prompt=requests.utils.quote(f"{prompt}, {suffix}"),
        seed=seed,
    )
    try:
        resp = requests.get(url, timeout=60)
        if resp.status_code == 200 and resp.headers.get("content-type", "").startswith("image/"):
            return Image.open(io.BytesIO(resp.content)).convert("RGBA")
    except Exception:
        pass
    return None


def generate_photo(prompt, seed_offset=0):
    seed = random.randint(1, 999999) + seed_offset
    img = _fetch_image(prompt, seed)
    if img is None:
        time.sleep(2)
        img = _fetch_image(prompt, seed + 1)
    return img


def _get_font(size):
    for path in [
        "/System/Library/Fonts/Helvetica.ttc",
        "/System/Library/Fonts/Arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    ]:
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    return ImageFont.load_default()


def _wrap(draw, text, font, max_w):
    words = text.split()
    lines, line = [], ""
    for word in words:
        test = (line + " " + word).strip()
        if draw.textlength(test, font=font) > max_w and line:
            lines.append(line)
            line = word
        else:
            line = test
    if line:
        lines.append(line)
    return lines


def _load_packaging(size=260):
    if not os.path.exists(PACKAGING_PATH):
        return None
    try:
        pkg = Image.open(PACKAGING_PATH).convert("RGBA")
        pkg.thumbnail((size, size), Image.LANCZOS)
        return pkg
    except Exception:
        return None


def to_bytes(image):
    buf = io.BytesIO()
    image.save(buf, format="JPEG", quality=92)
    buf.seek(0)
    return buf


def design_fire(base, text, packaging):
    img = base.copy().convert("RGBA")
    ov = Image.new("RGBA", img.size, (255, 255, 255, 0))
    draw = ImageDraw.Draw(ov)
    f_main = _get_font(66)
    f_logo = _get_font(72)
    for i in range(440):
        a = int(205 * (1 - i / 440))
        draw.line([(0, i), (img.width, i)], fill=(0, 0, 0, a))
    for i in range(320):
        a = int(190 * (i / 320))
        draw.line([(0, img.height - 320 + i), (img.width, img.height - 320 + i)], fill=(185, 20, 20, a))
    lines = _wrap(draw, text, f_main, img.width - 80)
    y = 55
    for ln in lines[:4]:
        draw.text((40, y), ln, font=f_main, fill=(255, 255, 255, 248))
        y += 82
    draw.rectangle([0, img.height - 118, img.width, img.height], fill=(210, 28, 28, 235))
    lw = draw.textlength("Top Doner", font=f_logo)
    draw.text(((img.width - lw) // 2, img.height - 105), "Top Doner", font=f_logo, fill=(255, 255, 255, 255))
    result = Image.alpha_composite(img, ov).convert("RGBA")
    if packaging:
        px, py = 28, img.height - 118 - packaging.height - 18
        result.paste(packaging, (px, py), packaging)
    return result.convert("RGB")


def design_clean(base, text, packaging):
    img = base.copy().convert("RGBA")
    ov = Image.new("RGBA", img.size, (255, 255, 255, 0))
    draw = ImageDraw.Draw(ov)
    f_main = _get_font(60)
    f_addr = _get_font(36)
    f_logo = _get_font(68)
    panel_h = 400
    for i in range(panel_h):
        a = int(230 * (i / panel_h))
        draw.line([(0, img.height - panel_h + i), (img.width, img.height - panel_h + i)], fill=(255, 255, 255, a))
    lines = _wrap(draw, text, f_main, img.width - 100)
    y = img.height - panel_h + 50
    for ln in lines[:3]:
        tw = draw.textlength(ln, font=f_main)
        draw.text(((img.width - tw) // 2, y), ln, font=f_main, fill=(25, 25, 25, 245))
        y += 75
    addr = "Байтерек 6мкр  •  Самал 89"
    aw = draw.textlength(addr, font=f_addr)
    draw.text(((img.width - aw) // 2, y + 12), addr, font=f_addr, fill=(140, 140, 140, 210))
    draw.rectangle([0, img.height - 105, img.width, img.height], fill=(28, 28, 28, 238))
    lw = draw.textlength("Top Doner", font=f_logo)
    draw.text(((img.width - lw) // 2, img.height - 92), "Top Doner", font=f_logo, fill=(255, 215, 0, 255))
    result = Image.alpha_composite(img, ov).convert("RGBA")
    if packaging:
        px = img.width - packaging.width - 28
        py = img.height - 105 - packaging.height - 18
        result.paste(packaging, (px, py), packaging)
    return result.convert("RGB")


def add_watermark(image, text="Top Doner"):
    img = image.copy().convert("RGBA")
    ov = Image.new("RGBA", img.size, (255, 255, 255, 0))
    draw = ImageDraw.Draw(ov)
    font = _get_font(60)
    bbox = draw.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    x, y = img.width - tw - 40, img.height - th - 40
    draw.rectangle([x - 16, y - 10, x + tw + 16, y + th + 10], fill=(0, 0, 0, 130))
    draw.text((x, y), text, font=font, fill=(255, 255, 255, 225))
    return Image.alpha_composite(img, ov).convert("RGB")


@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id,
        "🔥 Привет! Я SMM-агент Top Doner!\n\n"
        "📅 /plan — план на 7 дней\n"
        "📆 /today — контент на сегодня\n"
        "✍️ /stories — 3 сториса\n"
        "💡 /idea — вирусная идея\n"
        "🌯 /doner — текст про донер\n"
        "🍔 /burger — текст про бургер\n"
        "📣 /promo — акция\n"
        "⭐️ /reviews — 2 отзыва клиентов\n"
        "🎨 /banners — баннеры для Canva\n"
        "🆚 /vs — почему мы лучше\n"
        "📸 /photo [блюдо] — фото с водяным знаком\n"
        "🎬 /story — 2 баннера с дизайном\n\n"
        "📦 Отправь фото упаковки — она появится на баннерах!"
    )


@bot.message_handler(commands=['today'])
def today(message):
    bot.send_message(message.chat.id, "📆 Генерирую контент на сегодня...")
    today_date = datetime.now().strftime("%d %B, %A")
    result = ask_ai(
        f"Сгенерируй полный контент на сегодня {today_date} для Top Doner Уральск:\n"
        "1. Утренний сторис\n2. Дневной сторис\n3. Вечерний сторис\n"
        "4. Два реалистичных отзыва от молодёжи\n"
        "5. Описание двух баннеров для Canva"
    )
    bot.send_message(message.chat.id, f"📆 *Контент на сегодня:*\n\n{result}", parse_mode="Markdown")


@bot.message_handler(commands=['plan'])
def plan(message):
    bot.send_message(message.chat.id, "📅 Составляю план на неделю...")
    result = ask_ai("Составь детальный сторис-план на 7 дней для Top Doner Уральск. Для каждого дня: тема, 3 сториса, отзыв, идея баннера.")
    bot.send_message(message.chat.id, f"📅 *План на 7 дней:*\n\n{result}", parse_mode="Markdown")


@bot.message_handler(commands=['stories'])
def stories(message):
    bot.send_message(message.chat.id, "✍️ Пишу сторисы...")
    result = ask_ai("Напиши 3 огненных сториса для Top Doner Уральск: утренний, дневной, вечерний. Молодёжный стиль, эмодзи, Алматинский донер, работа до 5 утра.")
    bot.send_message(message.chat.id, f"✍️ *Сторисы:*\n\n{result}", parse_mode="Markdown")


@bot.message_handler(commands=['idea'])
def idea(message):
    result = ask_ai("Придумай вирусную идею для сториса Top Doner Уральск — мемную или очень аппетитную.")
    bot.send_message(message.chat.id, f"💡 *Вирусная идея:*\n\n{result}", parse_mode="Markdown")


@bot.message_handler(commands=['doner'])
def doner(message):
    result = ask_ai("Напиши огненный сторис про Алматинский донер 1200тг + Кола в подарок, Top Doner Уральск, до 5 утра!")
    bot.send_message(message.chat.id, f"🌯 *Алматинский донер:*\n\n{result}", parse_mode="Markdown")


@bot.message_handler(commands=['burger'])
def burger(message):
    result = ask_ai("Напиши аппетитный сторис про бургер от Top Doner Уральск. Халяль, заказ через WhatsApp.")
    bot.send_message(message.chat.id, f"🍔 *Бургер:*\n\n{result}", parse_mode="Markdown")


@bot.message_handler(commands=['promo'])
def promo(message):
    result = ask_ai("Придумай акцию и напиши сторис для Top Doner Уральск. FOMO, срочно, заказ через WhatsApp.")
    bot.send_message(message.chat.id, f"📣 *Акция:*\n\n{result}", parse_mode="Markdown")


@bot.message_handler(commands=['reviews'])
def reviews(message):
    result = ask_ai("Напиши 2 реалистичных отзыва от молодых клиентов Top Doner Уральск. Один про Алматинский донер, один про бургер.")
    bot.send_message(message.chat.id, f"⭐️ *Отзывы:*\n\n{result}", parse_mode="Markdown")


@bot.message_handler(commands=['banners'])
def banners(message):
    result = ask_ai("Опиши 2 баннера для Canva для Top Doner Уральск, размер 1080x1920. Один про Алматинский донер, один брендовый.")
    bot.send_message(message.chat.id, f"🎨 *Баннеры для Canva:*\n\n{result}", parse_mode="Markdown")


@bot.message_handler(commands=['vs'])
def vs(message):
    result = ask_ai("Напиши сторис почему Top Doner лучше других донерных в Уральске. Не называй конкурентов. Акцент: до 5 утра, Алматинский донер, халяль, два адреса.")
    bot.send_message(message.chat.id, f"🆚 *Наши преимущества:*\n\n{result}", parse_mode="Markdown")


@bot.message_handler(commands=['photo'])
def photo_cmd(message):
    dish = message.text.replace('/photo', '').strip()
    if not dish:
        dish = "алматинский донер кебаб, красивая подача"
    msg = bot.send_message(message.chat.id, "📸 Генерирую фото... (~30–60 сек) ⏳")
    image = generate_photo(dish)
    if image is None:
        bot.edit_message_text("❌ Попробуй ещё раз через минуту!", message.chat.id, msg.message_id)
        return
    result = add_watermark(image.convert("RGB"))
    bot.delete_message(message.chat.id, msg.message_id)
    bot.send_photo(message.chat.id, to_bytes(result), caption=f"📸 {dish}\n\nTop Doner Уральск 🌯")


@bot.message_handler(commands=['story'])
def story_cmd(message):
    has_pkg = os.path.exists(PACKAGING_PATH)
    pkg_note = " + упаковка" if has_pkg else ""
    msg = bot.send_message(message.chat.id, f"🎨 Генерирую 2 баннера{pkg_note}... (~60–90 сек) ⏳")
    story_text = ask_ai(
        "Напиши одну яркую фразу (до 7 слов) для баннера Top Doner — про донер или бургер. Без эмодзи, только русский текст."
    ).strip()[:100]
    packaging = _load_packaging()
    prompt = "аппетитный донер кебаб или смэш-бургер, красивая подача, яркие цвета, Top Doner Уральск"
    img1 = generate_photo(prompt, seed_offset=0)
    img2 = generate_photo(prompt, seed_offset=500)
    if img1 is None and img2 is None:
        bot.edit_message_text("❌ Не удалось сгенерировать фото. Попробуй позже.", message.chat.id, msg.message_id)
        return
    bot.delete_message(message.chat.id, msg.message_id)
    if img1:
        bot.send_photo(message.chat.id, to_bytes(design_fire(img1, story_text, packaging)),
                       caption=f"🔥 Дизайн 1 — Огонь\n«{story_text}»")
    if img2:
        bot.send_photo(message.chat.id, to_bytes(design_clean(img2, story_text, packaging)),
                       caption=f"✨ Дизайн 2 — Чистый\n«{story_text}»")


@bot.message_handler(content_types=['photo'])
def save_packaging(message):
    file_id = message.photo[-1].file_id
    file_info = bot.get_file(file_id)
    data = bot.download_file(file_info.file_path)
    with open(PACKAGING_PATH, "wb") as f:
        f.write(data)
    bot.send_message(message.chat.id,
        "📦 Фото упаковки сохранено! Теперь она появляется на всех баннерах /story\n"
        "Чтобы заменить — отправь новое фото.")


@bot.message_handler(func=lambda m: True)
def echo(message):
    bot.send_message(message.chat.id, ask_ai(message.text))


print("🍔 Top Doner бот запущен v4!")
bot.infinity_polling()

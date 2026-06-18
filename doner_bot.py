import telebot
from groq import Groq
import requests
import io
import os
import time
from PIL import Image, ImageDraw, ImageFont

TELEGRAM_TOKEN = "8994193838:AAEw732kO6FXp-RvXAY_C_VwqlWSTZCl0gw"
GROQ_API_KEY = "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"

bot = telebot.TeleBot(TELEGRAM_TOKEN)
client = Groq(api_key=GROQ_API_KEY)

SYSTEM_PROMPT = """Ты контент-менеджер кафе Top Doner в Уральске. Пишешь сторисы и посты на русском языке. Стиль: аппетитный, молодёжный, с эмодзи."""
PACKAGING_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "packaging.jpg")
STORY_W, STORY_H = 1080, 1920
POLLINATIONS_BASE = "https://image.pollinations.ai/prompt/{prompt}?width=1080&height=1920&nologo=true&seed={seed}"


# ─── AI ───────────────────────────────────────────────────────────────────────

def ask_ai(prompt):
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": prompt}],
        max_tokens=1500,
    )
    return response.choices[0].message.content


# ─── Фото-генерация ───────────────────────────────────────────────────────────

def _fetch_image(prompt: str, seed: int) -> Image.Image | None:
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


def generate_photo(prompt: str, seed_offset: int = 0) -> Image.Image | None:
    seed = int(time.time()) + seed_offset
    img = _fetch_image(prompt, seed)
    if img is None:
        time.sleep(2)
        img = _fetch_image(prompt, seed + 1)
    return img


# ─── Шрифты и вспомогательные ────────────────────────────────────────────────

def _get_font(size: int) -> ImageFont.FreeTypeFont:
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


def _wrap(draw: ImageDraw.ImageDraw, text: str, font, max_w: int) -> list[str]:
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


def _load_packaging(size: int = 260) -> Image.Image | None:
    if not os.path.exists(PACKAGING_PATH):
        return None
    try:
        pkg = Image.open(PACKAGING_PATH).convert("RGBA")
        pkg.thumbnail((size, size), Image.LANCZOS)
        return pkg
    except Exception:
        return None


def to_bytes(image: Image.Image) -> io.BytesIO:
    buf = io.BytesIO()
    image.save(buf, format="JPEG", quality=92)
    buf.seek(0)
    return buf


# ─── Дизайн 1: Огонь (красно-тёмный) ────────────────────────────────────────

def design_fire(base: Image.Image, text: str, packaging: Image.Image | None) -> Image.Image:
    img = base.copy().convert("RGBA")
    ov = Image.new("RGBA", img.size, (255, 255, 255, 0))
    draw = ImageDraw.Draw(ov)

    f_main = _get_font(66)
    f_logo = _get_font(72)

    # Тёмный градиент сверху
    for i in range(440):
        a = int(205 * (1 - i / 440))
        draw.line([(0, i), (img.width, i)], fill=(0, 0, 0, a))

    # Красный градиент снизу
    for i in range(320):
        a = int(190 * (i / 320))
        draw.line([(0, img.height - 320 + i), (img.width, img.height - 320 + i)], fill=(185, 20, 20, a))

    # Текст сверху
    lines = _wrap(draw, text, f_main, img.width - 80)
    y = 55
    for ln in lines[:4]:
        draw.text((40, y), ln, font=f_main, fill=(255, 255, 255, 248))
        y += 82

    # Логотип снизу
    draw.rectangle([0, img.height - 118, img.width, img.height], fill=(210, 28, 28, 235))
    lw = draw.textlength("Top Doner", font=f_logo)
    draw.text(((img.width - lw) // 2, img.height - 105), "Top Doner", font=f_logo, fill=(255, 255, 255, 255))

    result = Image.alpha_composite(img, ov).convert("RGBA")

    # Упаковка — нижний левый угол над логотипом
    if packaging:
        px, py = 28, img.height - 118 - packaging.height - 18
        result.paste(packaging, (px, py), packaging)

    return result.convert("RGB")


# ─── Дизайн 2: Белая панель (чистый) ─────────────────────────────────────────

def design_clean(base: Image.Image, text: str, packaging: Image.Image | None) -> Image.Image:
    img = base.copy().convert("RGBA")
    ov = Image.new("RGBA", img.size, (255, 255, 255, 0))
    draw = ImageDraw.Draw(ov)

    f_main = _get_font(60)
    f_addr = _get_font(36)
    f_logo = _get_font(68)

    panel_h = 400
    # Белая полупрозрачная панель снизу
    for i in range(panel_h):
        a = int(230 * (i / panel_h))
        draw.line([(0, img.height - panel_h + i), (img.width, img.height - panel_h + i)], fill=(255, 255, 255, a))

    # Текст по центру панели
    lines = _wrap(draw, text, f_main, img.width - 100)
    y = img.height - panel_h + 50
    for ln in lines[:3]:
        tw = draw.textlength(ln, font=f_main)
        draw.text(((img.width - tw) // 2, y), ln, font=f_main, fill=(25, 25, 25, 245))
        y += 75

    # Адрес
    addr = "Байтерек 6мкр  •  Самал 89"
    aw = draw.textlength(addr, font=f_addr)
    draw.text(((img.width - aw) // 2, y + 12), addr, font=f_addr, fill=(140, 140, 140, 210))

    # Тёмная плашка логотипа
    draw.rectangle([0, img.height - 105, img.width, img.height], fill=(28, 28, 28, 238))
    lw = draw.textlength("Top Doner", font=f_logo)
    draw.text(((img.width - lw) // 2, img.height - 92), "Top Doner", font=f_logo, fill=(255, 215, 0, 255))

    result = Image.alpha_composite(img, ov).convert("RGBA")

    # Упаковка — нижний правый угол над логотипом
    if packaging:
        px = img.width - packaging.width - 28
        py = img.height - 105 - packaging.height - 18
        result.paste(packaging, (px, py), packaging)

    return result.convert("RGB")


# ─── Водяной знак для /photo ──────────────────────────────────────────────────

def add_watermark(image: Image.Image, text: str = "Top Doner") -> Image.Image:
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


# ─── Команды ──────────────────────────────────────────────────────────────────

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(
        message.chat.id,
        "🔥 Привет! Я бот Top Doner!\n\n"
        "📅 /plan — план на неделю\n"
        "✍️ /stories — сторисы на сегодня\n"
        "💡 /idea — идея для поста\n"
        "🌯 /doner — текст про донер\n"
        "🍔 /burger — текст про бургер\n"
        "📣 /promo — акция\n"
        "📸 /photo — фото блюда с водяным знаком\n"
        "🎨 /story — 2 баннера с дизайном\n\n"
        "📦 Чтобы добавить упаковку в баннеры — просто отправь её фото боту!",
    )


@bot.message_handler(commands=['plan'])
def plan(message):
    bot.send_message(message.chat.id, "📅 Составляю план...")
    bot.send_message(message.chat.id, ask_ai("Составь сторис-план на 7 дней для кафе Top Doner в Уральске. Донеры и бургеры. С эмодзи."))


@bot.message_handler(commands=['stories'])
def stories(message):
    bot.send_message(message.chat.id, "✍️ Пишу сторисы...")
    bot.send_message(message.chat.id, ask_ai("Напиши 3 готовых сториса для Top Doner Уральск: утренний, дневной, вечерний. С эмодзи."))


@bot.message_handler(commands=['idea'])
def idea(message):
    bot.send_message(message.chat.id, ask_ai("Придумай вирусную идею для сториса кафе с донерами и бургерами в Уральске."))


@bot.message_handler(commands=['doner'])
def doner(message):
    bot.send_message(message.chat.id, ask_ai("Напиши аппетитный сторис про донер кебаб Top Doner Уральск. Адрес: Байтерек 6мкр и Самал 89."))


@bot.message_handler(commands=['burger'])
def burger(message):
    bot.send_message(message.chat.id, ask_ai("Напиши аппетитный сторис про бургер Top Doner Уральск. Адрес: Байтерек 6мкр и Самал 89."))


@bot.message_handler(commands=['promo'])
def promo(message):
    bot.send_message(message.chat.id, ask_ai("Придумай акцию и напиши сторис для Top Doner Уральск. Срочно, выгодно, с призывом."))


@bot.message_handler(commands=['photo'])
def photo_cmd(message):
    msg = bot.send_message(message.chat.id, "📸 Генерирую фото... (~30–60 сек)")
    prompt = "аппетитный донер кебаб или бургер, красивая подача, кафе Top Doner Уральск"
    image = generate_photo(prompt)
    if image is None:
        bot.edit_message_text("❌ Не удалось сгенерировать фото. Попробуйте позже.", message.chat.id, msg.message_id)
        return
    result = add_watermark(image.convert("RGB"))
    bot.delete_message(message.chat.id, msg.message_id)
    bot.send_photo(message.chat.id, to_bytes(result), caption="📸 Top Doner | 1080×1920")


@bot.message_handler(commands=['story'])
def story_cmd(message):
    has_pkg = os.path.exists(PACKAGING_PATH)
    pkg_note = " + упаковка" if has_pkg else ""
    msg = bot.send_message(message.chat.id, f"🎨 Генерирую 2 баннера{pkg_note}... (~60–90 сек)")

    # Текст для баннера
    story_text = ask_ai(
        "Напиши одну яркую фразу (до 7 слов) для баннера кафе Top Doner — про донер или бургер. "
        "Без эмодзи, только текст на русском."
    ).strip()[:100]

    packaging = _load_packaging()
    prompt = "аппетитный донер кебаб или смэш-бургер, красивая подача, яркие цвета, Top Doner Уральск"

    # Генерируем 2 разных фото
    img1 = generate_photo(prompt, seed_offset=0)
    img2 = generate_photo(prompt, seed_offset=100)

    if img1 is None and img2 is None:
        bot.edit_message_text("❌ Не удалось сгенерировать фото. Попробуйте позже.", message.chat.id, msg.message_id)
        return

    bot.delete_message(message.chat.id, msg.message_id)

    if img1:
        banner1 = design_fire(img1, story_text, packaging)
        bot.send_photo(
            message.chat.id,
            to_bytes(banner1),
            caption=f"🔥 Дизайн 1 — Огонь\n«{story_text}»",
        )

    if img2:
        banner2 = design_clean(img2, story_text, packaging)
        bot.send_photo(
            message.chat.id,
            to_bytes(banner2),
            caption=f"✨ Дизайн 2 — Чистый\n«{story_text}»",
        )


# ─── Сохранение фото упаковки ─────────────────────────────────────────────────

@bot.message_handler(content_types=['photo'])
def save_packaging(message):
    file_id = message.photo[-1].file_id
    file_info = bot.get_file(file_id)
    data = bot.download_file(file_info.file_path)
    with open(PACKAGING_PATH, "wb") as f:
        f.write(data)
    bot.send_message(
        message.chat.id,
        "📦 Фото упаковки сохранено! Теперь она будет появляться на всех баннерах /story ✅\n"
        "Чтобы заменить — просто отправь новое фото.",
    )


@bot.message_handler(func=lambda m: True)
def echo(message):
    bot.send_message(message.chat.id, ask_ai(message.text))


print("🍔 Top Doner бот запущен!")
bot.infinity_polling()

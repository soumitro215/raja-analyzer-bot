import os
import logging
import base64
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎯 *Raja Game Analyzer Bot*\n\n"
        "Mujhe Raja Game ki *1-minute history screenshot* bhejo!\n\n"
        "Main turant *Big/Small prediction* dunga! ⚡",
        parse_mode="Markdown"
    )

async def analyze_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("⏳ Screenshot analyze ho raha hai...")

    try:
        photo = update.message.photo[-1]
        file = await context.bot.get_file(photo.file_id)
        file_url = file.file_path

        img_response = requests.get(file_url)
        img_base64 = base64.b64encode(img_response.content).decode("utf-8")

        prompt = """You are a colour trading game pattern analyzer for Raja Game 1-minute rounds.

Analyze this game history screenshot carefully.
Each result is BIG (numbers 5-9) or SMALL (numbers 0-4).

Respond ONLY in this exact JSON format, nothing else:
{
  "big_probability": <number 0-100>,
  "small_probability": <number 0-100>,
  "prediction": "BIG or SMALL",
  "confidence": <number 0-100>,
  "analysis": "<2-3 sentences in Hinglish explaining the pattern>",
  "patterns": ["pattern1", "pattern2", "pattern3"]
}"""

        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "meta-llama/llama-4-scout-17b-16e-instruct",
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{img_base64}"
                                }
                            },
                            {
                                "type": "text",
                                "text": prompt
                            }
                        ]
                    }
                ],
                "max_tokens": 500,
                "temperature": 0.1
            }
        )

        result_text = response.json()["choices"][0]["message"]["content"]
        
        import json
        clean = result_text.strip().replace("```json", "").replace("```", "").strip()
        data = json.loads(clean)

        prediction = data.get("prediction", "?")
        big_pct = data.get("big_probability", 50)
        small_pct = data.get("small_probability", 50)
        confidence = data.get("confidence", 50)
        analysis = data.get("analysis", "")
        patterns = data.get("patterns", [])

        emoji = "🟢" if prediction == "BIG" else "🔴"
        
        msg = f"""🎯 *RAJA GAME ANALYSIS*
━━━━━━━━━━━━━━━━

{emoji} *Next Round: {prediction}*

📊 *Probability:*
🟢 BIG: {big_pct}%
🔴 SMALL: {small_pct}%

💪 *Confidence: {confidence}%*

📈 *Pattern Analysis:*
{analysis}

🔍 *Patterns Found:*
{chr(10).join(['• ' + p for p in patterns])}

━━━━━━━━━━━━━━━━
⚠️ Sirf pattern analysis hai, guarantee nahi!"""

        await update.message.reply_text(msg, parse_mode="Markdown")

    except Exception as e:
        logger.error(f"Error: {e}")
        await update.message.reply_text(
            "❌ Screenshot analyze nahi ho saka.\n"
            "Kripya *Raja Game ki history* ka clear screenshot bhejein!",
            parse_mode="Markdown"
        )

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📸 Mujhe *Raja Game history screenshot* bhejo!\n"
        "Text nahi, sirf image chahiye! 😊",
        parse_mode="Markdown"
    )

def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.PHOTO, analyze_image))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    logger.info("Bot starting...")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()

# -*- coding: utf-8 -*-
# DailyRisk Router-Bot + Diagnose: erst Ziel wählen, dann Vorlage posten.
# Außerdem: /where zeigt die echte chat_id; /testpost testet beide Ziele.
# Abhängigkeit: python-telegram-bot==13.15

import logging, sys, traceback
from collections import defaultdict
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (Updater, CommandHandler, CallbackQueryHandler,
                          CallbackContext)

BOT_TOKEN = "8268332063:AAECBER8DyoSgmqgcXyS5KD8j47CUiPYZCA"

# >>>> TRAGE HIER ZUNÄCHST DEINE VERMUTETEN IDs EIN (wir verifizieren sie gleich mit /where)
FREE_CHAT_ID    = "@DailyRisk"     # wenn das eine private Gruppe/Channel ist: später durch -100... ersetzen
PREMIUM_CHAT_ID = -1002812279417 # mit -100 Präfix (so klappt es sicher in Supergruppen/Kanälen)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s", stream=sys.stdout)
log = logging.getLogger("DailyRisk")

TEMPLATES = {
    "buy":  ("Buy Gold",  "🔔Trade-Idee: 🔔\n\nXAUUSD BUY 🔼\n\n⚠️ Hinweis/Disclaimer:\nDies ist nur zu Bildungszwecken und keine Finanzberatung. Handel immer auf eigenes Risiko. DYOR.\n⚠️ Disclaimer: Educational purpose only. Not financial advice. Trade at your own risk. DYOR."),
    "sell": ("Sell Gold", "🔔Trade-Idee: 🔔\n\nXAUUSD SELL 🔽\n\n⚠️ Hinweis/Disclaimer:\nDies ist nur zu Bildungszwecken und keine Finanzberatung. Handel immer auf eigenes Risiko. DYOR.\n⚠️ Disclaimer: Educational purpose only. Not financial advice. Trade at your own risk. DYOR."),
    "be":   ("SL auf BE", "Ich setze den SL auf BE, um den Trade abzusichern. 🔐\n(Du kannst natürlich auch schon deine Gewinne mitnehmen.)"),
    "risk": ("High Risk", "Sei vorsichtig, erhöhtes Risiko! ⚠️\nBestenfalls Gewinne schnell mitnehmen!"),
}
user_target = defaultdict(lambda: None)  # None / "both" / "premium"

def kb_dest():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📣 Free + Premium", callback_data="dest:both")],
        [InlineKeyboardButton("💎 nur Premium",    callback_data="dest:premium")],
    ])
def kb_tpl():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Buy Gold",  callback_data="tpl:buy"),
         InlineKeyboardButton("Sell Gold", callback_data="tpl:sell")],
        [InlineKeyboardButton("SL auf BE", callback_data="tpl:be"),
         InlineKeyboardButton("High Risk", callback_data="tpl:risk")],
        [InlineKeyboardButton("⏪ Ziel ändern",     callback_data="back:dest")],
    ])

def start(update: Update, _: CallbackContext):
    update.message.reply_text("✅ DailyRisk Router-Bot aktiv.\nSende mir **/post** privat.")

def post(update: Update, _: CallbackContext):
    if update.effective_chat.type != "private":
        update.message.reply_text("Bitte **privat** öffnen und /post senden.")
        return
    user_target[update.effective_user.id] = None
    update.message.reply_text("Wohin möchtest du posten?", reply_markup=kb_dest())

def where(update: Update, _: CallbackContext):
    """GIBT DIR DIE ECHTE chat_id AUS – in der Gruppe/Kanal ausführen!"""
    cid = update.effective_chat.id
    ctp = update.effective_chat.type
    update.message.reply_text(f"chat_id: {cid}\nchat_type: {ctp}")

def testpost(update: Update, context: CallbackContext):
    """Test: versucht in beide Ziele zu posten und gibt den exakten Fehler zurück."""
    msg = "Testpost vom Bot."
    out = []
    for name, cid in [("FREE_CHAT_ID", FREE_CHAT_ID), ("PREMIUM_CHAT_ID", PREMIUM_CHAT_ID)]:
        try:
            context.bot.send_message(chat_id=cid, text=msg)
            out.append(f"{name}: ✅ OK")
        except Exception as e:
            out.append(f"{name}: ❌ {e}")
    update.message.reply_text("\n".join(out))

def on_cb(update: Update, context: CallbackContext):
    q = update.callback_query
    uid = q.from_user.id
    data = q.data or ""
    q.answer()

    try:
        if data.startswith("dest:"):
            user_target[uid] = "both" if data.endswith("both") else "premium"
            q.edit_message_text(
                text=f"Ziel: {'Free + Premium' if user_target[uid]=='both' else 'nur Premium'}\nBitte Vorlage wählen:",
                reply_markup=kb_tpl()
            ); return

        if data == "back:dest":
            user_target[uid] = None
            q.edit_message_text("Wohin möchtest du posten?", reply_markup=kb_dest()); return

        if data.startswith("tpl:"):
            key = data.split(":", 1)[1]
            text = TEMPLATES[key][1]
            sent = []
            if user_target[uid] == "both":
                if FREE_CHAT_ID:
                    context.bot.send_message(chat_id=FREE_CHAT_ID, text=text); sent.append("Free")
                if PREMIUM_CHAT_ID:
                    context.bot.send_message(chat_id=PREMIUM_CHAT_ID, text=text); sent.append("Premium")
            elif user_target[uid] == "premium":
                context.bot.send_message(chat_id=PREMIUM_CHAT_ID, text=text); sent.append("Premium")
            else:
                q.answer("Bitte erst ein Ziel wählen.", show_alert=True); return
            q.answer("✅ Gesendet: " + ", ".join(sent))
            return

    except Exception as e:
        log.error("Fehler: %s", e)
        log.error("Traceback:\n%s", traceback.format_exc())
        try: context.bot.send_message(chat_id=uid, text=f"❌ Fehler: {e}")
        except: pass

def main():
    up = Updater(BOT_TOKEN, use_context=True)
    me = up.bot.get_me()
    log.info("Bot gestartet als @%s (id=%s)", me.username, me.id)

    dp = up.dispatcher
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("post",  post))
    dp.add_handler(CommandHandler("where", where))      # <- chat_id ermitteln
    dp.add_handler(CommandHandler("testpost", testpost))# <- beide Ziele testen
    dp.add_handler(CallbackQueryHandler(on_cb))

    log.info("Bereit. Sende mir **/post** privat. In Gruppen/Kanal: /where für ID, /testpost zum Prüfen.")
    up.start_polling(); up.idle()

if __name__ == "__main__":
    main()

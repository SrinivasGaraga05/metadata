import os
import re
import asyncio
import threading
from http.server import SimpleHTTPRequestHandler, HTTPServer
from pyrogram import Client, filters
from pyrogram.types import Message
from mutagen.mp4 import MP4
from config import API_ID, API_HASH, BOT_TOKEN

# Initialize bot
app = Client("FileRenameBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Dictionary to store user thumbnails
user_thumbnails = {}

# Function to process filename
def process_filename(original_name):
    pattern = r"(.+?)\s*[Ee]?(\d{1,3})?\s*[\U0001F466\U0001F466]?(1080p|720p|480p|360p)[\U0001F466\U0001F466]?\s*(Dual Audio|Subbed|Dubbed)?"
    match = re.search(pattern, original_name, re.IGNORECASE)
    if match:
        title = match.group(1).strip()
        episode = f" E{match.group(2)}" if match.group(2) else ""
        quality = match.group(3) if match.group(3) else ""
        audio = match.group(4) if match.group(4) else ""
        new_name = f"@Animes2u {title}{episode} {quality} {audio}".strip() + ".mp4"
        return new_name
    return "@Animes2u " + original_name

# Function to update metadata
def update_metadata(file_path):
    try:
        video = MP4(file_path)
        video["\xa9nam"] = "@Animes2u"
        video["\xa9ART"] = "@Animes2u"
        video["\xa9alb"] = "@Animes2u"
        video["\xa9cmt"] = "@Animes2u"
        video["\xa9too"] = "@Animes2u"
        video.save()
    except Exception as e:
        print(f"❌ Error updating metadata: {e}")

# Start command
@app.on_message(filters.command("start"))
async def start(client, message: Message):
    await message.reply("👋 Hello! Send me multiple *video files*, and I'll rename them with **@Animes2u**, update metadata, and apply your custom thumbnail!")

# Handle multiple video file uploads
@app.on_message(filters.video)
async def rename_files(client, message: Message):
    media_group = message.media_group_id
    files = [message]
    
    if media_group:
        await asyncio.sleep(2)  # Wait to collect all messages in the group
        files = [msg async for msg in client.get_chat_history(message.chat.id, limit=10) if msg.media_group_id == media_group]
    
    tasks = [process_file(client, msg) for msg in files]
    await asyncio.gather(*tasks)

async def process_file(client, message: Message):
    try:
        print(f"📥 Processing file from {message.from_user.id}...")

        progress_msg = await message.reply("📥 Downloading...")

        file = await message.download(progress=progress_callback, progress_args=(client, progress_msg, "Downloading"))
        print("✅ Download complete:", file)

        await progress_msg.edit_text("⚡ Processing file...")

        new_filename = process_filename(file)
        os.rename(file, new_filename)
        print("✅ File renamed to:", new_filename)

        # Update metadata
        print("ℹ️ Updating metadata for:", new_filename)
        update_metadata(new_filename)

        # Get user thumbnail
        thumb = user_thumbnails.get(message.from_user.id)

        # Send renamed file
        print("📤 Sending back:", new_filename)
        await message.reply_video(new_filename, thumb=thumb, caption=f"✅ Renamed: {new_filename}")

        # Cleanup
        os.remove(new_filename)
        await progress_msg.delete()

    except Exception as e:
        print("❌ Error:", e)
        await message.reply(f"⚠️ An error occurred: {e}")

# Progress callback for file operations
async def progress_callback(client, message: Message, current, total, status: str):
    percent = (current / total) * 100
    try:
        await message.edit_text(f"{status}: {percent:.2f}%")
    except:
        pass

# Set user thumbnail
@app.on_message(filters.command("setthumb") & filters.photo)
async def set_thumbnail(client, message: Message):
    thumb_path = await message.download()
    user_thumbnails[message.from_user.id] = thumb_path
    await message.reply("✅ Thumbnail saved!")

# Delete user thumbnail
@app.on_message(filters.command("delthumb"))
async def delete_thumbnail(client, message: Message):
    if message.from_user.id in user_thumbnails:
        os.remove(user_thumbnails.pop(message.from_user.id))
        await message.reply("🗑 Thumbnail deleted!")
    else:
        await message.reply("⚠ No thumbnail found.")

# Dummy web server for Render deployment
def run_dummy_server():
    server = HTTPServer(("0.0.0.0", 8080), SimpleHTTPRequestHandler)
    server.serve_forever()

threading.Thread(target=run_dummy_server, daemon=True).start()

# Run the bot
app.run()

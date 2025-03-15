import os
import re
from pyrogram import Client, filters
from pyrogram.types import Message
from mutagen.mp4 import MP4

# Import API details from config.py
from config import API_ID, API_HASH, BOT_TOKEN

# Initialize bot
app = Client("FileRenameBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Dictionary to store user thumbnails
user_thumbnails = {}

# Function to process filename
def process_filename(original_name):
    pattern = r"(.+?)\s*[Ee]?(\d{1,3})?\s*[👦👦]?(1080p|720p|480p|360p)[👦👦]?\s*(Dual Audio|Subbed|Dubbed)?"
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
    video = MP4(file_path)
    video["\xa9nam"] = "@Animes2u"  # Title
    video["\xa9ART"] = "@Animes2u"  # Artist
    video["\xa9alb"] = "@Animes2u"  # Album
    video["\xa9cmt"] = "@Animes2u"  # Comment
    video["\xa9too"] = "@Animes2u"  # Encoded by
    video.save()

# Start command
@app.on_message(filters.command("start"))
async def start(client, message: Message):
    await message.reply("👋 Hello! Send me a *video file, and I'll rename it with **@Animes2u*, update metadata, and apply your custom thumbnail!")

# Handle video file uploads
@app.on_message(filters.video)
async def rename_file(client, message: Message):
    file = await message.download()
    new_filename = process_filename(file)
    os.rename(file, new_filename)

    # Update metadata
    update_metadata(new_filename)

    # Get user thumbnail (if set)
    thumb = user_thumbnails.get(message.from_user.id)

    # Send renamed file
    await message.reply_video(new_filename, thumb=thumb, caption=f"✅ Renamed: {new_filename}")
    
    # Cleanup
    os.remove(new_filename)

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

# Run the bot
app.run()

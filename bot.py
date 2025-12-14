import os
import subprocess
import time
import asyncio
from pyrogram import Client, filters
from pyrogram.errors import FloodWait
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# --- V37: CONFIGURATION (FETCHED FROM ENVIRONMENT) ---
# Render par ye values Environment Variables se aayengi
try:
    API_ID = int(os.environ.get("API_ID"))
    API_HASH = os.environ.get("API_HASH")
    BOT_TOKEN = os.environ.get("BOT_TOKEN")
    
    # AUTH_USERS ko comma-separated string se load karo
    AUTH_USERS_STR = os.environ.get("AUTH_USERS", "")
    AUTH_USERS = [int(u.strip()) for u in AUTH_USERS_STR.split(',') if u.strip().isdigit()]
    
except Exception as e:
    print("FATAL ERROR: Environment variables are missing or invalid.")
    print("Please set API_ID, API_HASH, BOT_TOKEN, and AUTH_USERS on Render.")
    exit(1)

# --- V37: CONFIGURATION CONSTANTS ---
SPLIT_CHUNK_SECONDS = 600  # 10 minutes * 60 seconds (Each video part)
MAX_RECORD_SECONDS = 7200  # Max 2 hours (120 minutes)
MAIN_ADMIN_ID = AUTH_USERS[0] if AUTH_USERS else None # List ka pehla user main admin

# --- CHANNEL LIST (Same as before) ---
CHANNELS = {
    "cartoon_network": "http://103.182.170.32:8888/play/a04o",
    "cartoon_network_hd_plus": "http://103.182.170.32:8888/play/a035", 
    "discovery_kids": "http://103.182.170.32:8888/play/a02o",
    "disney_channel": "http://103.182.170.32:8888/play/a04g",
    "disney_int_hd": "http://103.182.170.32:8888/play/a01y",
    "disney_junior": "http://103.182.170.32:8888/play/a03q",
    "etv_bal_bharat": "http://103.182.170.32:8888/play/a022",
    "hungama": "http://103.182.170.32:8888/play/a04b",
    "nick": "http://103.182.170.32:8888/play/a04q",
    "nick_jr": "http://103.182.170.32:8888/play/a02q",
    "pogo": "http://103.182.170.32:8888/play/a02p",
    "sony_yay": "http://103.182.170.32:8888/play/a04m",
    "sonic": "http://103.182.170.32:8888/play/a02s",
    "test_hls": "http://content.uplynk.com/channel/32d0df09b4394c8b87d81a94e824e4d5.m3u8", 
}
REFERRERS = {} 

# --- BOT CLIENT INITIALIZATION (Render uses Bot Token) ---
app = Client(
    "recorder_bot", 
    api_id=API_ID, 
    api_hash=API_HASH, 
    bot_token=BOT_TOKEN
)

# --- HELPER FUNCTIONS ---
def get_channel_keyboard():
    keyboard = []
    channels_list = list(CHANNELS.keys())
    if "test_hls" in channels_list: channels_list.remove("test_hls")
    for i in range(0, len(channels_list), 2):
        row = []
        channel1 = channels_list[i]
        row.append(InlineKeyboardButton(text=channel1.upper().replace('_', ' '), callback_data=f'/record {channel1} 10m'))
        if i + 1 < len(channels_list):
            channel2 = channels_list[i+1]
            row.append(InlineKeyboardButton(text=channel2.upper().replace('_', ' '), callback_data=f'/record {channel2} 10m'))
        keyboard.append(row)
    return InlineKeyboardMarkup(keyboard)

# --- ADMIN COMMANDS & BROADCAST (Same as V35) ---

@app.on_message(filters.command("add_admin") & filters.user(MAIN_ADMIN_ID))
async def add_admin(client, message):
    try:
        user_id = int(message.text.split()[1])
        if user_id not in AUTH_USERS:
            AUTH_USERS.append(user_id)
            await message.reply(f"✅ User `{user_id}` added to Admin list. Total Admins: {len(AUTH_USERS)}")
        else:
            await message.reply(f"⚠️ User `{user_id}` is already an Admin.")
    except (IndexError, ValueError):
        await message.reply("❌ Usage: `/add_admin <user_id>` (User ID hona chahiye)")

@app.on_message(filters.command("rem_admin") & filters.user(MAIN_ADMIN_ID))
async def rem_admin(client, message):
    try:
        user_id = int(message.text.split()[1])
        if user_id in AUTH_USERS:
            if user_id == MAIN_ADMIN_ID:
                return await message.reply("❌ Cannot remove the main Admin.")
            AUTH_USERS.remove(user_id)
            await message.reply(f"✅ User `{user_id}` removed from Admin list. Total Admins: {len(AUTH_USERS)}")
        else:
            await message.reply(f"⚠️ User `{user_id}` is not an Admin.")
    except (IndexError, ValueError):
        await message.reply("❌ Usage: `/rem_admin <user_id>` (User ID hona chahiye)")

@app.on_message(filters.command("admins") & filters.user(MAIN_ADMIN_ID))
async def list_admins(client, message):
    admin_list = "\n".join([f"- `{uid}` (Main Admin)" if uid == MAIN_ADMIN_ID else f"- `{uid}`" for uid in AUTH_USERS])
    await message.reply(f"🛡️ **Current Admins ({len(AUTH_USERS)})**:\n{admin_list}")

@app.on_message(filters.command("broadcast") & filters.user(MAIN_ADMIN_ID))
async def broadcast_message(client, message):
    if len(message.text.split()) < 2:
        return await message.reply("❌ Usage: `/broadcast <Your Message Here>`")

    text = message.text.split(' ', 1)[1]
    success_count = 0
    
    await message.reply(f"📢 Starting broadcast to {len(AUTH_USERS)} users...")
    
    for user_id in AUTH_USERS:
        try:
            await client.send_message(user_id, f"📢 **ADMIN BROADCAST**\n\n{text}")
            success_count += 1
            await asyncio.sleep(0.5) 
        except FloodWait as e:
            await asyncio.sleep(e.value)
        except Exception as e:
            print(f"Failed to send to {user_id}: {e}")
            
    await message.reply(f"✅ Broadcast finished. Sent to {success_count}/{len(AUTH_USERS)} users.")

# --- CORE RECORDING LOGIC (V37: TS Format + Hungama Fix) ---

@app.on_message(filters.command("start"))
async def start(client, message):
    if message.from_user.id not in AUTH_USERS: return
    await message.reply(
        f"🤖 **Ripping Bot (V37 - Render Ready)**\n"
        f"🛡️ **Status:** Render deployment successful. Max stability achieved.\n"
        f"⚡ **Max Time:** {MAX_RECORD_SECONDS // 60} Minutes\n"
        f"✂️ **Split Size:** {SPLIT_CHUNK_SECONDS // 60} Minutes\n\n"
        f"**Test:** `/record disney_channel 15s`\n"
        f"**Movie Test:** `/record pogo 30m`",
        reply_markup=get_channel_keyboard()
    )


@app.on_message(filters.command("record") & filters.private)
async def record(client, message):
    if message.from_user.id not in AUTH_USERS: return 

    args = message.text.split()
    if len(args) < 3: return await message.reply("❌ Usage: `/record <channel> <time>` (e.g., 20m)", reply_markup=get_channel_keyboard())

    channel_name = args[1].lower()
    duration_str = args[2]

    try:
        if duration_str.endswith('m'): seconds = int(duration_str[:-1]) * 60
        elif duration_str.endswith('s'): seconds = int(duration_str[:-1])
        else: return await message.reply("❌ Format: '30s' or '10m'.")
    except ValueError: return await message.reply("❌ Error in time format.")

    if seconds < 10 or seconds > MAX_RECORD_SECONDS: 
        return await message.reply(f"⚠️ Time: 10s to {MAX_RECORD_SECONDS // 60}m only.")
    
    if channel_name not in CHANNELS: return await message.reply(f"❌ Channel not found!", reply_markup=get_channel_keyboard())

    url = CHANNELS[channel_name]

    # --- Auto-Split Logic ---
    chunk_size = seconds if seconds <= SPLIT_CHUNK_SECONDS else SPLIT_CHUNK_SECONDS
    total_chunks = (seconds + chunk_size - 1) // chunk_size
    remaining_seconds = seconds
    
    main_msg = await message.reply(
        f"🎬 **{channel_name.upper()}**\n\n**TOTAL TIME:** {seconds // 60}m {seconds % 60}s\n"
        f"**CHUNKS:** {total_chunks} x {chunk_size // 60}m\n\n"
        f"**Starting Split Recording...**"
    )

    chunk_num = 1
    
    while remaining_seconds > 0:
        chunk_duration = min(remaining_seconds, chunk_size)
        output_file = f"{channel_name}_{int(time.time())}_{chunk_num}.ts" 
        
        await main_msg.edit_text(
            f"🎬 **{channel_name.upper()}** (Chunk {chunk_num} of {total_chunks})\n"
            f"⏳ Recording {chunk_duration // 60}m {chunk_duration % 60}s...\n"
            f"🚀 **Render is working**"
        )

        # --- FFmpeg Command (TS Format + Hungama Fix) ---
        cmd = [
            'ffmpeg', 
            '-timeout', '10000000',
            '-user_agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36',
        ]
        if channel_name in REFERRERS: cmd.extend(['-headers', f'Referer: {REFERRERS[channel_name]}\r\n'])

        cmd.extend([
            # Hungama Fix
            '-probesize', '10M',         
            '-analyzeduration', '10M',   
            
            '-fflags', '+genpts', 
            '-avioflags', 'direct',  
            '-i', url, 
            '-vsync', 'vfr',      
            '-t', str(chunk_duration), 
            '-c', 'copy', 
            '-flush_packets', '1',
            output_file, 
            '-y'
        ])
        
        process = None
        crashed = False
        
        try:
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            start_time = time.time()
            
            # Progress Loop 
            while True:
                await asyncio.sleep(5) 
                elapsed = int(time.time() - start_time)
                
                if elapsed >= chunk_duration: break
                if process.poll() is not None: break
                    
                try:
                    await main_msg.edit_text(f"🎬 **{channel_name.upper()}** (Chunk {chunk_num} of {total_chunks})\n⏱ {elapsed}s / {chunk_duration}s")
                except: pass

            process.wait(timeout=10) 

            if process.returncode != 0: crashed = True
        except subprocess.TimeoutExpired:
            crashed = True
            if process: process.terminate()
            
        except Exception as e:
            crashed = True
            print(f"Recording Error: {e}")

        # --- UPLOAD & CLEANUP SECTION ---
        if os.path.exists(output_file) and os.path.getsize(output_file) > 100000: 
            final_size = round(os.path.getsize(output_file) / (1024 * 1024), 2)
            
            status_text = "✅ Chunk Success"
            if crashed: status_text = "⚠️ **Partial Record (Killed)**"
            
            await message.reply(f"🎬 **{channel_name.upper()}** | Part {chunk_num}/{total_chunks}\n{status_text}\n💾 Size: {final_size} MB\n🚀 Uploading...")
            
            try:
                await client.send_document(
                    chat_id=message.chat.id,
                    document=output_file, 
                    caption=f"🎬 **{channel_name.upper()}** | Part {chunk_num}/{total_chunks}\n{status_text}\n💾 Size: {final_size} MB"
                )
            except Exception as e:
                await message.reply(f"❌ Upload Failed for Part {chunk_num}: {e}")
                
        else:
            await message.reply(f"❌ Recording Failed completely for Part {chunk_num}. No file created.")

        # --- CLEANUP (Guaranteed) ---
        try:
            if os.path.exists(output_file): 
                os.remove(output_file)
                print(f"File {output_file} cleaned up successfully.")
        except Exception as cleanup_e:
            print(f"CRITICAL: Failed to delete file {output_file}. Error: {cleanup_e}")
        
        # --- Loop Update ---
        remaining_seconds -= chunk_duration
        chunk_num += 1
        await asyncio.sleep(5) 

    await main_msg.edit_text(f"✅ **TOTAL RECORDING COMPLETE**\n🎬 **{channel_name.upper()}** ({total_chunks} parts sent.)")


print("Bot V37 (Render Ready) Running...")
app.run()

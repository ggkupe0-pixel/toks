import discord
import os
import asyncio
import subprocess
import sys
import logging

def install_requirements():
    try:
        import nacl
    except ImportError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "PyNaCl"])

install_requirements()

TARGET_VC_ID = os.getenv('VC_ID') 

# Dynamically read variables USER_TOKEN_1 up to USER_TOKEN_3
TOKENS = []
for i in range(1, 4):  
    token = os.getenv(f'USER_TOKEN_{i}')
    if token and token.strip():
        TOKENS.append(token.strip())

# Clean up logging levels so we can track exact network drops if they happen
logging.basicConfig(level=logging.INFO)
logging.getLogger('discord').setLevel(logging.WARNING)

class SafePermanentAnchor(discord.Client):
    def __init__(self, vc_id, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.target_vc_id = int(vc_id) if vc_id else None
        self.is_connecting = False

    async def on_ready(self):
        print(f"LOGGED IN: {self.user} (ID: {self.user.id})")
        # Initialize the background guardian loop
        self.loop.create_task(self.maintain_connection())

    async def maintain_connection(self):
        await self.wait_until_ready()
        while not self.is_closed():
            if self.target_vc_id:
                await self.ensure_vc()
            # Send a confirmation heartbeat pulse to Discord every 30 seconds
            await asyncio.sleep(30)

    async def ensure_vc(self):
        if self.is_connecting:
            return

        self.is_connecting = True
        try:
            # Resolve the channel and the parent guild object
            channel = self.get_channel(self.target_vc_id) or await self.fetch_channel(self.target_vc_id)
            guild = channel.guild
            
            # STABLE GATEWAY PAYLOAD: Tells the network to lock you in the VC without audio data streams
            await guild.change_voice_state(channel=channel, self_mute=True, self_deaf=False)
            print(f"[{self.user}] Permanent anchor pulse sent to: {channel.name}")
        except Exception as e:
            print(f"[{self.user}] Connection anchor anomaly: {e}")
        finally:
            self.is_connecting = False

async def start_bots():
    if not TARGET_VC_ID or not TOKENS:
        print("ERROR: Missing VC_ID or valid USER_TOKEN variables in Railway.")
        return

    print(f"Launching {len(TOKENS)} account(s)...")

    # Grant maximum gateway permission tracking for user clients
    intents = discord.Intents.all()

    for token in TOKENS:
        try:
            client = SafePermanentAnchor(
                vc_id=TARGET_VC_ID,
                intents=intents,
                heartbeat_timeout=60.0
            )
            asyncio.create_task(client.start(token))
            await asyncio.sleep(3.0)  # Safe delay between account logins
        except Exception as e:
            print(f"Initialization failed for token: {e}")

    # Keep background workers spinning permanently
    while True:
        await asyncio.sleep(3600)

if __name__ == "__main__":
    try:
        asyncio.run(start_bots())
    except KeyboardInterrupt:
        print("Process stopped manually.")
    except Exception as e:
        print(f"FATAL SYSTEM ERROR: {e}")







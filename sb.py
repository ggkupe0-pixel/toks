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
for i in range(1, 4):  # Loops exactly 3 times (1, 2, 3)
    token = os.getenv(f'USER_TOKEN_{i}')
    if token and token.strip():
        TOKENS.append(token.strip())

logging.getLogger('discord').setLevel(logging.CRITICAL)

class SafePermanentAnchor(discord.Client):
    def __init__(self, vc_id, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.target_vc_id = int(vc_id) if vc_id else None
        self.is_reconnecting = False

    async def on_ready(self):
        print(f"LOGGED IN: {self.user} (ID: {self.user.id})")
        await asyncio.sleep(2)
        await self.join_vc()

    async def join_vc(self):
        if self.is_reconnecting or not self.target_vc_id:
            return

        # Check if we are already comfortably connected to the target channel
        if self.voice_clients:
            for vc in self.voice_clients:
                if vc.channel.id == self.target_vc_id and vc.is_connected():
                    return  # Do absolutely nothing if already inside

        self.is_reconnecting = True
        try:
            channel = await self.fetch_channel(self.target_vc_id)

            # Clean up lingering or stuck voice states strictly
            if self.voice_clients:
                for vc in self.voice_clients:
                    try:
                        await vc.disconnect(force=True)
                    except Exception:
                        pass
                await asyncio.sleep(1)

            print(f"[{self.user}] Joining {channel.name}...")
            await channel.connect(self_deaf=False, self_mute=True, reconnect=True)
            print(f"[{self.user}] SESSION LOCKED")
        except Exception as e:
            print(f"[{self.user}] Join failed: {e}")
            await asyncio.sleep(20) 
        finally:
            self.is_reconnecting = False

    async def on_voice_state_update(self, member, before, after):
        # Only trigger reconnection logic if it is strictly THIS specific account being disconnected
        if member.id == self.user.id:
            if after.channel is None or after.channel.id != self.target_vc_id:
                if not self.is_reconnecting:
                    print(f"[{self.user}] Left target channel. Reconnecting in 5s...")
                    await asyncio.sleep(5) 
                    await self.join_vc()

async def start_bots():
    if not TARGET_VC_ID or not TOKENS:
        print("ERROR: Missing VC_ID or valid USER_TOKEN variables in Railway.")
        return

    print(f"Launching {len(TOKENS)} account(s)...")

    # Connect sequentially with a 3-second gap so they don't break each other's gateway connections
    for token in TOKENS:
        try:
            client = SafePermanentAnchor(
                vc_id=TARGET_VC_ID,
                heartbeat_timeout=60.0
            )
            asyncio.create_task(client.start(token))
            await asyncio.sleep(3.0)  
        except Exception as e:
            print(f"Initialization failed for token: {e}")

    # Keep background tasks alive
    while True:
        await asyncio.sleep(3600)

if __name__ == "__main__":
    try:
        asyncio.run(start_bots())
    except KeyboardInterrupt:
        print("Process stopped.")
    except Exception as e:
        print(f"FATAL ERROR: {e}")




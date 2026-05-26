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

# Dynamically read USER_TOKEN_1 through USER_TOKEN_8 from Railway variables
TOKENS = []
for i in range(1, 9):
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

        self.is_reconnecting = True
        try:
            channel = await self.fetch_channel(self.target_vc_id)

            if self.voice_clients:
                for vc in self.voice_clients:
                    if vc.channel.id == self.target_vc_id:
                        print(f"[{self.user}] Already in target channel.")
                        self.is_reconnecting = False
                        return
                    await vc.disconnect()

            print(f"[{self.user}] Joining {channel.name}...")
            await channel.connect(self_deaf=False, self_mute=True, reconnect=True)
            print(f"[{self.user}] SESSION LOCKED")
        except Exception as e:
            print(f"[{self.user}] Join failed: {e}")
            await asyncio.sleep(30) 
        finally:
            self.is_reconnecting = False

    async def on_voice_state_update(self, member, before, after):
        if member.id == self.user.id and after.channel is None:
            if not self.is_reconnecting:
                print(f"[{self.user}] Disconnected. Reconnecting in 10s...")
                await asyncio.sleep(10) 
                await self.join_vc()

async def start_bots():
    if not TARGET_VC_ID or not TOKENS:
        print("ERROR: Missing VC_ID or valid USER_TOKEN variables in Railway.")
        return

    print(f"Launching {len(TOKENS)} account(s)...")

    # Sequential startup with a 1.5s delay to prevent gateway rate limits
    for token in TOKENS:
        try:
            client = SafePermanentAnchor(
                vc_id=TARGET_VC_ID,
                heartbeat_timeout=60.0
            )
            # CRITICAL FIX: Explicitly pass bot=False for self-bot authentication
            asyncio.create_task(client.start(token, bot=False))
            await asyncio.sleep(1.5)  
        except Exception as e:
            print(f"Failed to initialize a token: {e}")

    # Keep the master runtime loop alive
    while True:
        await asyncio.sleep(3600)

if __name__ == "__main__":
    try:
        asyncio.run(start_bots())
    except KeyboardInterrupt:
        print("Process stopped.")
    except Exception as e:
        print(f"FATAL ERROR: {e}")



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

# Collect exactly 3 tokens
TOKENS = []
for i in range(1, 4):  
    token = os.getenv(f'USER_TOKEN_{i}')
    if token and token.strip():
        TOKENS.append(token.strip())

logging.getLogger('discord').setLevel(logging.CRITICAL)

class SafePermanentAnchor(discord.Client):
    def __init__(self, vc_id, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.target_vc_id = int(vc_id) if vc_id else None
        self.is_connecting = False

    async def on_ready(self):
        print(f"LOGGED IN: {self.user} (ID: {self.user.id})")
        # Start a permanent background guardian task for this account
        self.loop.create_task(self.lock_into_vc())

    async def lock_into_vc(self):
        await self.wait_until_ready()
        while not self.is_closed():
            if self.target_vc_id:
                await self.ensure_connection()
            # Strict 5-second verification pulse to make leaving impossible
            await asyncio.sleep(5)

    async def ensure_connection(self):
        if self.is_connecting:
            return

        # Check if already connected perfectly
        for vc in self.voice_clients:
            if vc.channel and vc.channel.id == self.target_vc_id and vc.is_connected():
                return  # Stay put, do nothing

        self.is_connecting = True
        try:
            channel = await self.fetch_channel(self.target_vc_id)
            
            # Wipe any broken or ghost sessions cleanly before forcing entry
            for vc in self.voice_clients:
                await vc.disconnect(force=True)
                
            print(f"[{self.user}] Locking session into {channel.name}...")
            await channel.connect(self_deaf=False, self_mute=True, reconnect=True)
            print(f"[{self.user}] PERMANENTLY ANCHORED")
        except Exception:
            pass
        finally:
            self.is_connecting = False

async def start_bots():
    if not TARGET_VC_ID or not TOKENS:
        print("ERROR: Missing VC_ID or valid USER_TOKEN variables.")
        return

    print(f"Spinning up {len(TOKENS)} connection workers...")

    clients = []
    for token in TOKENS:
        client = SafePermanentAnchor(
            vc_id=TARGET_VC_ID,
            heartbeat_timeout=60.0
        )
        clients.append(client)

    # SIMULTANEOUS LAUNCH: Fires all 3 client connections at the exact same millisecond
    await asyncio.gather(*[client.start(token) for client, token in zip(clients, TOKENS)])

if __name__ == "__main__":
    try:
        asyncio.run(start_bots())
    except KeyboardInterrupt:
        print("Process stopped.")
    except Exception as e:
        print(f"FATAL ERROR: {e}")






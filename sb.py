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

logging.getLogger('discord').setLevel(logging.CRITICAL)

class SafePermanentAnchor(discord.Client):
    def __init__(self, vc_id, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.target_vc_id = int(vc_id) if vc_id else None
        self.is_connecting = False

    async def on_ready(self):
        print(f"LOGGED IN: {self.user} (ID: {self.user.id})")
        # Start the background watchdog to ensure they NEVER leave
        self.loop.create_task(self.maintain_connection())

    async def maintain_connection(self):
        await self.wait_until_ready()
        while not self.is_closed():
            if self.target_vc_id:
                await self.ensure_vc()
            # Check connection status every 10 seconds permanently
            await asyncio.sleep(10)

    async def ensure_vc(self):
        if self.is_connecting:
            return

        # If perfectly connected, do absolutely nothing
        for vc in self.voice_clients:
            if vc.channel and vc.channel.id == self.target_vc_id and vc.is_connected():
                return

        self.is_connecting = True
        try:
            channel = await self.fetch_channel(self.target_vc_id)
            
            # Nuke any ghost connections before joining
            for vc in self.voice_clients:
                await vc.disconnect(force=True)
                
            print(f"[{self.user}] Anchoring to {channel.name}...")
            await channel.connect(self_deaf=False, self_mute=True, reconnect=True)
            print(f"[{self.user}] ANCHOR SECURED")
        except Exception:
            pass # Silently fail and let the 10-second watchdog retry
        finally:
            self.is_connecting = False

    async def on_voice_state_update(self, member, before, after):
        # If kicked or moved, immediately trigger the anchor check
        if member.id == self.user.id:
            if after.channel is None or after.channel.id != self.target_vc_id:
                if not self.is_connecting:
                    await asyncio.sleep(1)
                    await self.ensure_vc()

async def start_bots():
    if not TARGET_VC_ID or not TOKENS:
        print("ERROR: Missing VC_ID or valid USER_TOKEN variables in Railway.")
        return

    print(f"Launching {len(TOKENS)} account(s)...")

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

    while True:
        await asyncio.sleep(3600)

if __name__ == "__main__":
    try:
        asyncio.run(start_bots())
    except KeyboardInterrupt:
        print("Process stopped.")
    except Exception:
        pass





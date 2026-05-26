import discord
import os
import asyncio
import logging

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

    async def on_ready(self):
        print(f"LOGGED IN: {self.user} (ID: {self.user.id})")
        # Starts the permanent gateway pulse
        self.loop.create_task(self.maintain_connection())

    async def maintain_connection(self):
        await self.wait_until_ready()
        
        while not self.is_closed():
            if self.target_vc_id:
                try:
                    # Fetch the channel to get the Guild ID
                    channel = self.get_channel(self.target_vc_id) or await self.fetch_channel(self.target_vc_id)
                    guild_id = channel.guild.id if hasattr(channel, 'guild') else None
                    
                    # RAW PAYLOAD BYPASS: Tells Discord you are in the VC without starting a blocked audio stream
                    await self.ws.voice_state(guild_id, self.target_vc_id, self_mute=True, self_deaf=False)
                except Exception as e:
                    pass # Fails completely silently so it never crashes
            
            # Send the pulse every 60 seconds. 
            # If they are already in the VC, Discord ignores it. If they got disconnected, it instantly puts them back.
            await asyncio.sleep(60)

async def start_bots():
    if not TARGET_VC_ID or not TOKENS:
        print("ERROR: Missing VC_ID or valid USER_TOKEN variables in Railway.")
        return

    print(f"Launching {len(TOKENS)} account(s)...")

    for token in TOKENS:
        try:
            client = SafePermanentAnchor()
            asyncio.create_task(client.start(token))
            await asyncio.sleep(2.0)  
        except Exception as e:
            print(f"Initialization failed for token: {e}")

    # Master loop keeps the script alive forever
    while True:
        await asyncio.sleep(3600)

if __name__ == "__main__":
    try:
        asyncio.run(start_bots())
    except KeyboardInterrupt:
        print("Process stopped.")
    except Exception:
        pass






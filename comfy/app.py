import os
import discord
from dotenv import load_dotenv
from pathlib import Path
from comfy.lit_gpt_helpers.download import download_from_hub
from comfy.lit_gpt_helpers.generate import generate_comfy
from comfy.lit_gpt_helpers.convert_hf_checkpoint import convert_hf_checkpoint
from lit_gpt import Tokenizer

load_dotenv()

GUILD_ID_STR = os.getenv("GUILD_ID")
if GUILD_ID_STR is None:
    raise ValueError("GUILD_ID environment variable is not set")
GUILD_ID = int(GUILD_ID_STR)
MAX_DISCORD_MESSAGE_LENGTH_CHAR = 2000


class Message:
    def __init__(self, author, content):
        self.author = author
        self.content = content
        self.len_tokens = len(Tokenizer.encode(str(self)))

    def __str__(self):
        return f"{self.author}: {self.content}"


class MyClient(discord.Client):
    def __init__(self, *args, checkpoint_path, **kwargs):
        self.checkpoint_path = checkpoint_path
        super().__init__(*args, **kwargs)

    async def on_ready(self):
        print(f'Logged on as {self.user}!')

    async def on_guild_join(self, guild):
        if guild.id != GUILD_ID:
            await guild.leave()

    async def on_message(self, message: discord.Message):
        if not self.user or message.author == self.user:
            # Ignore messages from self
            return
        if not message.channel.type \
                or message.channel.type.name not in ["text", "forum", "public_thread"]:
            # Ignore messages from non-text channels
            return
        if self.user not in message.mentions:
            return

        print("message", message.content)

        async with message.channel.typing():
            try:
                answer = generate_comfy(
                    adapter_path=Path(os.path.abspath(os.path.join(os.path.dirname(
                        os.path.abspath(__file__)), "..", "iter-015999-ckpt.pth"))),
                    checkpoint_dir=self.checkpoint_path,
                    prompt=message.content
                )
            except Exception as err:
                print("Error ocured", err)
                answer = (
                    "I'm sorry, I'm having trouble understanding you right now."
                    " Could you please rephrase your question?"
                )
            await message.channel.send(answer, reference=message)
            print(answer)


def main():
    checkpoint_path = Path(os.path.abspath(os.path.join(os.path.dirname(
        os.path.abspath(__file__)), "..", "checkpoints", "tiiuae", "falcon-7b")))
    if not os.path.exists(checkpoint_path):
        download_from_hub("tiiuae/falcon-7b")
        convert_hf_checkpoint(checkpoint_dir=checkpoint_path)

    intents = discord.Intents.default()
    intents.message_content = True

    client = MyClient(intents=intents, checkpoint_path=checkpoint_path)
    discord_token = os.getenv("DISCORD_TOKEN")
    if not discord_token:
        raise ValueError("DISCORD_TOKEN environment variable is not set")
    client.run(discord_token)


if __name__ == "__main__":
    main()

import discord
import secret as sc
import config as cfg
from classes.Bot import Bot


def run_discord_bot():
    intents = discord.Intents.none()
    intents.guilds = True
    intents.messages = True
    intents.message_content = True
    intents.members = True

    client = discord.Client(intents=intents)

    bot = Bot(cfg.name, client, cfg.prefix, cfg.dft_color, sc.TOKEN)

    @client.event
    async def on_guild_join(guild):
        try:
            await bot.initialize_guilds()
        except Exception as e:
            print("[ERROR] initialize_guilds on join failed:", e)

    @client.event
    async def on_ready():
        print("READY as", client.user)
        try:
            await bot.initialize_guilds()
        except Exception as e:
            print("[ERROR] initialize_guilds failed:", e)

        # Optional: permissions dump for welcome channel(s)
        if getattr(cfg, "debug", True):
            for g in client.guilds:
                for ch in g.text_channels:
                    if ch.name == cfg.welcome_channel:
                        p = ch.permissions_for(g.me)
                        print("Guild:", g.name, g.id)
                        print("#welcome perms:", {
                            "view": p.view_channel,
                            "read_history": p.read_message_history,
                            "send": p.send_messages,
                            "embed": p.embed_links,
                            "add_reactions": p.add_reactions,
                            "manage_roles": p.manage_roles,
                        })

    @client.event
    async def on_message(msg: discord.Message):
        if msg.author == client.user:
            return

        # Optional: log EVERY message the bot receives (noisy!)
        if getattr(cfg, "debug_messages", False):
            try:
                print(
                    f"[Discord] msg guild='{getattr(msg.guild,'name',None)}' "
                    f"ch='#{getattr(msg.channel,'name',None)}' "
                    f"author='{msg.author}' content='{(msg.content or '').strip()}'"
                )
            except Exception:
                pass

        # 1) Live #welcome handling (per-guild)
        try:
            handled = await bot.process_single_welcome_message(msg)
            if handled:
                return
        except Exception as e:
            print("[welcome-live] error:", e)

        # 2) Commands
        content = (msg.content or "").strip()
        if not content.startswith(bot.prefix):
            return

        try:
            embed = await bot.handle_msg(msg)
            async with msg.channel.typing():
                await msg.reply(embed=embed)
        except Exception as e:
            print(f"[on_message] error: {e}")
            try:
                await msg.reply(f"Oops—error: `{e}`")
            except Exception:
                pass

    client.run(bot.token)

import discord
import secret as sc
import config as cfg
from classes.Bot import Bot

def run_discord_bot():
    # --- Intents ---
    intents = discord.Intents.none()
    intents.guilds = True
    intents.messages = True
    intents.message_content = True
    intents.members = True
    # (you can keep reactions=True if you plan to use them; not required otherwise)

    client = discord.Client(intents=intents)

    # --- Config ---
    name      = cfg.name
    prefix    = cfg.prefix
    dft_color = cfg.dft_color
    token     = sc.TOKEN

    bot = Bot(name, client, prefix, dft_color, token)

    # Re-init when the bot joins a new guild
    @client.event
    async def on_guild_join(guild):
        try:
            await bot.initialize_guilds()
        except Exception as e:
            print("[ERROR] initialize_guilds on join failed:", e)

    # SINGLE on_ready: initialize + perms dump
    @client.event
    async def on_ready():
        print("READY as", client.user)
        try:
            await bot.initialize_guilds()
            if bot.current_semester is None:
                print("[WARN] No active semester selected; check Semester.is_current_semester().")
            else:
                sem = bot.current_semester
                print(f"[INFO] Current semester set on guild: {sem.guild.name}")
                w = getattr(sem, "welcome_channel_obj", None)
                l = getattr(sem, "log_channel_obj", None)
                print("#welcome:", getattr(w, "name", None), " #bot-log:", getattr(l, "name", None))
        except Exception as e:
            print("[ERROR] initialize_guilds failed:", e)

        # (Optional) permissions dump for the welcome channel in each guild
        for g in client.guilds:
            print("Guild:", g.name, g.id)
            for ch in g.text_channels:
                if ch.name == cfg.welcome_channel:
                    p = ch.permissions_for(g.me)
                    print("#welcome perms:", {
                        "view": p.view_channel,
                        "read_history": p.read_message_history,
                        "send": p.send_messages,
                        "embed": p.embed_links,
                        "add_reactions": p.add_reactions,
                        "manage_roles": p.manage_roles,
                    })

    # Message handler (prefix commands)
    # @client.event
    # async def on_message(msg: discord.Message):
        # # ignore ourselves
        # if msg.author == client.user:
            # return

        # content = (msg.content or "").strip()
        # if not content.startswith(bot.prefix):
            # return

        # try:
            # embed = await bot.handle_msg(msg)
            # async with msg.channel.typing():
                # await msg.reply(embed=embed)
        # except Exception as e:
            # print(f"[on_message] error: {e}")
            # try:
                # await msg.reply(f"Oops—error: `{e}`")
            # except Exception:
                # pass
    @client.event
    async def on_message(msg: discord.Message):
        # ignore ourselves
        if msg.author == client.user:
            return

        # 1) LIVE: if the message is in #welcome, try to process it immediately
        try:
            handled = await bot.process_single_welcome_message(msg)
            if handled:
                return  # we already replied / assigned or reported 'not found'
        except Exception as e:
            print("[welcome-live] error:", e)

        # 2) PREFIX COMMANDS (existing behavior)
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


    # Run
    client.run(bot.token)

import os
import psycopg2
import psycopg2.extras
from dotenv import load_dotenv

import discord
from discord.ext import commands

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
DATABASE_URL = os.environ["DATABASE_URL"]

conn = None
cursor = None

COMMAND_PREFIX = "/tb"
COMMANDS_DICT = {
    "coords": f"`{COMMAND_PREFIX} coords <world_name> <coords_tag (optional)>`",
    "add": f"`{COMMAND_PREFIX} record <world_name> <coords_tag> <x> <y> <z> <description (optional)>`",
    "editc": f"`{COMMAND_PREFIX} editc <world_name> <coords_tag> x/y/z <value>`"
}

bot = commands.Bot(command_prefix=COMMAND_PREFIX + " ")


async def connect_db(ctx):
    global conn
    global cursor
    try:
        conn = psycopg2.connect(DATABASE_URL, sslmode="require")
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
        raise commands.CommandError("Sorry! Something went wrong connecting to the server :(")


async def disconnect_db(ctx):
    global conn
    global cursor
    if cursor is not None:
        conn.commit()
        cursor.close()
        conn.close()


@bot.event
async def on_ready():
    print(f"{bot.user} has connected to Discord!")


@bot.listen("on_message")
async def sendCommandsList(message):
    if message.content.startswith(COMMAND_PREFIX) and len(message.content.split()) <= 1:
        reply = "Hello! I help save useful Minecraft coordinates! I am a work in progress, so some things may not be so smooth, and I will also have more features in the future!\n" \
                + "`<param>` indicates a no-whitespace keyword.\n" \
                + "`[param]` indicates that the parameter can be comprised of several words (includes whitespace).\n" \
                + "`(optional)` indicates that the parameter is optional.\n" \
                + "If you really must have a `<param>` have whitespace, put it in quotes, although this is not recommended.\n"\
                + "__Available commands__\n" \
                + "\n".join(COMMANDS_DICT.values())
        await message.channel.send(reply)


@bot.command(brief="Get previously saved coordinates for your world", description="Invoke this command by typing " + COMMANDS_DICT["coords"])
@commands.before_invoke(connect_db)
@commands.after_invoke(disconnect_db)
async def coords(ctx, world, search_tag=None):
    if search_tag is None:
        cursor.execute("""
            SELECT 
                * 
            FROM 
                coords
            WHERE 
                world = %(world)s
            """, {
                "world": world
        })
    else:
        cursor.execute("""
            SELECT 
                * 
            FROM 
                coords
            WHERE 
                world = %(world)s
                AND tag = %(search_tag)s
            """, {
                "world": world,
                "search_tag": search_tag
        })
    
    coord = cursor.fetchone()
    reply = ""
    while coord is not None:
        print("coords command called")
        print(coord)
        
        # TODO refactor to use join command
        if coord["guild_id"] == ctx.guild.id:
            reply += "**World name**\t`{}`\n**Tag**\t`{}`\n**Name**\t`{}`**Coordinates**\t`{} {} {}`\n**Description**\t`{}`\n\n".format(coord["world"], coord["tag"], coord["world"] + ":" + coord["tag"], coord["x"], coord["y"], coord["z"], coord["description"])

        coord = cursor.fetchone()
    
    reply = reply.strip()
    if reply == "":
        reply = "No coordinates found!"
    await ctx.send(reply)


@bot.command(brief="Save a new set of coordinates for later use", description="Invoke this command by typing " + COMMANDS_DICT["add"])
@commands.before_invoke(connect_db)
@commands.after_invoke(disconnect_db)
async def add(ctx, world, tag, x, y, z, *, description=None):
    try:
        x = int(x)
        y = int(y)
        z = int(z)
    except:
        raise commands.BadArgument("Error converting xyz coordinates to integers")

    cursor.execute("""
        INSERT INTO 
            coords(
                guild_id, 
                world, 
                tag, 
                x, 
                y, 
                z, 
                description
            )
        VALUES(
            %(guild_id)s,
            %(world)s,
            %(tag)s,
            %(x)s,
            %(y)s,
            %(z)s,
            %(description)s
        )
        RETURNING world, tag, x, y, z, description
    """, {
        "guild_id": ctx.guild.id,
        "world": world,
        "tag": tag,
        "x": x,
        "y": y,
        "z": z,
        "description": description
    })

    new_coords = cursor.fetchone()
    reply = "__Recorded coordinates__\n**World name**\t`{}`\n**Tag**\t`{}`**Name**\t`{}`\n**Coordinates**\t`{} {} {}`\n**Description**\t`{}`\n\n".format(new_coords["world"], new_coords["tag"], new_coords["world"] + ":" + new_coords["tag"], new_coords["x"], new_coords["y"], new_coords["z"], new_coords["description"])
    print(reply)
    await ctx.send(reply)


@add.error
async def add_error(ctx, error):
    if isinstance(error, commands.UserInputError):
        await ctx.send("Looks like your command was typed incorrectly! Your command should look like " + COMMANDS_DICT["record"] + ". Make sure there are no spaces in your world name or coordinates tag, and that coordinates are integers!")


@bot.command(brief="Edit the x, y, or z value", description="Invoke this command by typing " + COMMANDS_DICT["editc"])
@commands.before_invoke(connect_db)
@commands.after_invoke(disconnect_db)
async def editc(ctx, world, tag, param, value):
    if param not in ["x", "y", "z"]:
        raise commands.BadArgument("Requested parameter to change is not of x, y, or z")

    # the following code assumes no duplicate tags

    # check the coordinates exists
    cursor.execute("""
        SELECT 
            %(param)s
        FROM
            coords
        WHERE
            world = %(world)s
            AND tag = %(tag)s
            AND guild_id = %(guild_id)s
    """, {
        "param": param,
        "world": world,
        "tag": tag,
        "guild_id": ctx.guild.id
    })

    coord = cursor.fetchone()
    reply = ""

    if coord is None:
        reply = "Coordinates with name `" + world + ":" + tag + "` not found!"
    else:
        prev_value = coord[param]
        cursor.execute("""
            UPDATE 
                coords
            SET
                %(param)s = %(value)s
            WHERE
                world = %(world)s
                AND tag = %(tag)s
                AND guild_id = %(guild_id)s
            RETURNING %(param)s
        """, {
            "param": param,
            "value": value,
            "world": world,
            "tag": tag,
            "guild_id": ctx.guild.id
        })

        new_coord = cursor.fetchone()
        reply = f"Changed `{param}` from `{prev_value}` to `{new_coord[param]}` for `{world}:{tag}`"

    await ctx.send(reply)


@editc.error
async def editc_error(ctx, error):
    if isinstance(error, commands.UserInputError):
        await ctx.send("Looks like your command was typed incorrectly! The command is " + COMMANDS_DICT["editc"] + ".\nExample: `\\tb editc myworld mytag x 10`")


def main():
    bot.run(TOKEN)


if __name__ == "__main__":
    main()

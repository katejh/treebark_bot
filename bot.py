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
    "record": f"`{COMMAND_PREFIX} record <world_name> <coords_tag> <x> <y> <z>`"
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
    commands_list_str = "Available commands:\n"
    commands_list_str += "\n".join(COMMANDS_DICT.values())
    if message.content.startswith(COMMAND_PREFIX) and len(message.content.split()) <= 1:
        reply = "Hello! I help save useful Minecraft coordinates! I am a work in progress, so some things may not be so smooth, and I will also have more features in the future!\n" \
                + commands_list_str
        await message.channel.send(reply)


@bot.command()
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
            reply += "World name: {}\nName: {}\nCoordinates: {} {} {}\nDescription: {}\n\n".format(coord["world"], coord["tag"], coord["x"], coord["y"], coord["z"], coord["description"])

        coord = cursor.fetchone()
    
    reply = reply.strip()
    if reply == "":
        reply = "No coordinates found!"
    await ctx.send(reply)


@bot.command()
@commands.before_invoke(connect_db)
@commands.after_invoke(disconnect_db)
async def record(ctx, world, tag, x, y, z, description=None):
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
    reply = "Recorded coordinates:\nWorld name: {}\nName: {}\nCoordinates: {} {} {}\nDescription: {}\n\n".format(new_coords["world"], new_coords["tag"], new_coords["x"], new_coords["y"], new_coords["z"], new_coords["description"])
    print(reply)
    await ctx.send(reply)


@record.error
async def record_error(ctx, error):
    if isinstance(error, commands.UserInputError):
        await ctx.send("Looks like your command was typed incorrectly! Your command should look like " + COMMANDS_DICT["record"] + ". Make sure there are no spaces in your world name or coordinates tag, and that coordinates are integers!")


bot.run(TOKEN)
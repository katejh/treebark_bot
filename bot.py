import os
import psycopg2
import psycopg2.extras

import discord
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

DATABASE_URL = os.environ['DATABASE_URL']

client = discord.Client()

COMMAND_PREFIX = "treebark"

@client.event
async def on_ready():
    print(f'{client.user} has connected to Discord!')

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.startswith(COMMAND_PREFIX):
        print(f'message {message.content} sent from guild {message.guild.id} from user {message.author.name}')
        reply = run_command(message)
        print(reply)
        if reply is not None:
            await message.channel.send(reply)

def run_command(message):
    args = message.content.split()
    
    if len(args) <= 1:
        return "Hello! I help save useful Minecraft coordinates! I am a work in progress, so some things may not be so smooth, and I will also have more features in the future!\nAvailable commands:\n`treebark coords <world_name> <coords_tag (optional)>`\n`treebark record <world_name> <coords_tag> <x> <y> <z>`"

    arg = args[1]
    result = None

    conn = None
    try:
        conn = psycopg2.connect(DATABASE_URL, sslmode='require')
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

        if arg == "coords":
            if len(args) <= 2:
                return None
                # TODO return helpful message
            elif len(args) == 3:
                result = run_command_coords(cursor, args[2], message.guild.id)
            elif len(args) == 4:
                result = run_command_coords(cursor, args[2], message.guild.id, args[3])
        elif arg == "record":
            if len(args) < 7:
                return None
                #TODO return something helpful
            elif len(args) == 7:
                result = run_command_record(cursor, message.guild.id, args[2], args[3], args[4], args[5], args[6])
            # TODO implement putting in description

        cursor.close()
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
        result = "sorry! something went wrong while connecting to the server :("
    finally:
        if conn is not None:
            conn.commit()
            conn.close()
    
    print(result)
    return result

def run_command_coords(cursor, world, guild_id, search_tag=None):
    if search_tag is None:
        cursor.execute("""
            SELECT 
                * 
            FROM 
                coords
            WHERE 
                world = %(world)s
            """, {
                'world': world
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
                'world': world,
                'search_tag': search_tag
        })
    
    coord = cursor.fetchone()
    reply = ""
    while coord is not None:
        print("coords command called")
        print(coord)
        
        # TODO refactor to use join command
        if coord["guild_id"] == guild_id:
            reply += "World name: {}\nName: {}\nCoordinates: {} {} {}\nDescription: {}\n\n".format(coord["world"], coord["tag"], coord["x"], coord["y"], coord["z"], coord["description"])

        coord = cursor.fetchone()
    
    reply = reply.strip()
    if reply == "":
        reply = None
    return reply

def run_command_record(cursor, guild_id, world, tag, x, y, z, description=None):
    try:
        x = int(x)
        y = int(y)
        z = int(z)
    except:
        return "Looks like your command was typed incorrectly! Your command should look like `treebark record <world_name> <coords_tag> <x> <y> <z>`. Make sure there are no spaces in your world name or coordinates tag, and that coordinates are integers!"

    if description is not None:
        cursor.execute("""
            INSERT INTO 
                coords(
                    guild_id, 
                    world, 
                    tag, 
                    x_coord, 
                    y_coord, 
                    z_coord, 
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
        """, {
            "guild_id": guild_id,
            "world": world,
            "tag": tag,
            "x": x,
            "y": y,
            "z": z,
            "description": description
        })
    else:
        cursor.execute("""
            INSERT INTO 
                coords(
                    guild_id, 
                    world, 
                    tag, 
                    x_coord, 
                    y_coord, 
                    z_coord 
                )
            VALUES (
                %(guild_id)s,
                %(world)s,
                %(tag)s,
                %(x)s,
                %(y)s,
                %(z)s
            )
        """, {
            "guild_id": guild_id,
            "world": world,
            "tag": tag,
            "x": x,
            "y": y,
            "z": z,
        })

    reply = "Recorded coordinates:\nWorld name: {}\nName: {}\nCoordinates: {} {} {}\nDescription: {}\n\n".format(world, tag, x, y, z, description)
    return reply
    

client.run(TOKEN)
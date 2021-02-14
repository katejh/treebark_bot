# TreeBark helper bot

Discord bot for saving Minecraft coordinates. Python 3.6.8

## Setting up

Pull this repo or something

Set up a .env file and set DISCORD_TOKEN

Set DATABASE_URL (no need if Heroku is set up)

## Deploying to Heroku

## Accessing database

In command line, run `heroku pg:psql`

Then in session do SQL commands and stuff

## Usage

Commands
- [ ] `/tb` or `/tb` - lists available commands
- [x] `/tb coords <world_name> <coords_tag (optional)>` - gets saved coordinates of world. world_name must not have any spaces, coords_tag should not have spaces either.
- [x] `/tb record <world_name> <coords_tag> <x> <y> <z> <description (optional)>` - records new coordinates
- [ ] `/tb update <world_name> <coords_tag> <description>` updates description of coords
- [ ] `/tb delete <world_name> <coords_tag>` - deletes coordinates
- [ ] `/tb worlds` - lists available worlds and saved coords associated with each

## TODOs

- move to AWS
- refactor for cleaner code and more OOP-oriented approach. also be consistent with code
- README with installation, setup, usage, deploy instructions, database stuff
- more security potentially in case harmful messages break the bot
- implement proper checking for connections and better error messages from bot - see Error Handling and Checks from https://discordpy.readthedocs.io/en/latest/ext/commands/commands.html#error-handling
- implement proper logging
- check for duplicate records
- improve database rules
- add user auths to worlds
- separate test and prod
- think about what to do for duplicate entries

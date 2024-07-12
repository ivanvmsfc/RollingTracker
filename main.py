import discord
from discord import Embed
import asyncio
import aiohttp
import json
import os
from lol_handle import *
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

intents = discord.Intents.default()
client = discord.Client(intents=intents)

# Read the API key from the file
def read_api_key(file_path):
    with open(file_path, 'r') as file:
        api_key = file.read().strip()
    return api_key

# Usage
file_path = 'tokendisc.txt'
TOKEN = read_api_key(file_path)
CHANNEL_ID = 1256350316673368159  # Replace with your channel ID
MESSAGE = "Hello, this is a periodic message!"
JSON_FILE_PATH = 'summoners.json'  # Path to your JSON file


async def check_players(champions):
    await client.wait_until_ready()
    channel = client.get_channel(CHANNEL_ID)
    while not client.is_closed():
        with open(JSON_FILE_PATH, 'r') as f:
            summoners = json.load(f)
        async with aiohttp.ClientSession() as session:
            for name, details in summoners.items():
                if len(details) != 4:
                    logger.error(f"Incorrect data format for summoner {name}: {details}")
                    continue
                
                puuid, is_playing, game_id, champion_name = details
                game_info = await fetch_active_game(session, puuid)
                if game_info:
                    game_id = game_info['gameId']
                    participant = next((p for p in game_info['participants'] if p['puuid'] == puuid), None)
                    if participant:
                        champion_id = participant['championId']
                        champion_name = champions.get(champion_id, "Unknown Champion")
                        summoners[name][3] = champion_name

                        if not is_playing:
                            summoners[name][1] = True
                            summoners[name][2] = game_id
                            tier, rank, lp = await get_current_elo(session, puuid)
                            acc_name, acc_tag = await get_name(session, puuid)

                                    # Define the colors for each tier
                            tier_colors = {
                                "IRON": 0x62636C,
                                "BRONZE": 0xCD7F32,
                                "SILVER": 0xC0C0C0,
                                "GOLD": 0xFFD700,
                                "PLATINUM": 0x00BFFF,
                                "EMERALD": 0x50C878,
                                "DIAMOND": 0xB9F2FF,
                                "MASTER": 0x800080,
                                "GRANDMASTER": 0xDC143C,
                                "CHALLENGER": 0xFFD700
                            }
                            color = tier_colors.get(tier.upper(), 0xFF0000)

                            try:
                                acc_name = acc_name.replace(" ", "%20")
                            except:
                                pass
                            
                            opgg_url = f'https://www.op.gg/summoners/euw/{acc_name}-{acc_tag}/ingame'

                            embed = Embed(title=f'{name} está en partida!', color=color)
                            embed.add_field(name='Campeón', value=champion_name, inline=False)
                            embed.add_field(name='ELO actual', value=f'{tier} {rank} {lp} LPs', inline=False)
                            embed.add_field(name='Perfil OPGG', value=f'[Ver perfil en OPGG]({opgg_url})', inline=False)
                            await channel.send(embed=embed)


                elif is_playing:
                    game_id = summoners[name][2]
                    tier, rank, lp = await get_current_elo(session, puuid)
                    relevant_data = await post_game(session, puuid, game_id)
                    
                    # Define the colors for each tier
                    tier_colors = {
                        "IRON": 0x62636C,
                        "BRONZE": 0xCD7F32,
                        "SILVER": 0xC0C0C0,
                        "GOLD": 0xFFD700,
                        "PLATINUM": 0x00BFFF,
                        "EMERALD": 0x50C878,
                        "DIAMOND": 0xB9F2FF,
                        "MASTER": 0x800080,
                        "GRANDMASTER": 0xDC143C,
                        "CHALLENGER": 0xFFD700
                    }
                    color = tier_colors.get(tier.upper(), 0xFF0000)
                    embed = Embed(title=f'{name} ha terminado la partida!', color=color)
                    embed.add_field(name='Resultado', value=relevant_data["Match Outcome"], inline=False)
                    embed.add_field(name='Campeón', value=summoners[name][3], inline=False)
                    embed.add_field(name='KDA', value=relevant_data["KDA"], inline=False)
                    embed.add_field(name='Posición', value=relevant_data["Role"], inline=False)
                    embed.add_field(name='Daño Total Realizado', value=relevant_data["Total Damage Dealt"], inline=False)
                    embed.add_field(name='Daño Total Recibido', value=relevant_data["Total Damage Taken"], inline=False)
                    embed.add_field(name='Puntuación de Visión', value=relevant_data["Vision Score"], inline=False)
                    embed.add_field(name='ELO final', value=f'{tier} {rank} {lp} LPs', inline=False)
                    await channel.send(embed=embed)

                    summoners[name][1] = False

            await asyncio.sleep(1)

        with open(JSON_FILE_PATH, 'w') as f:
            json.dump(summoners, f, indent=4)
        await asyncio.sleep(300)

@client.event
async def on_ready():
    logging.info(f'Bot is ready. Logged in as {client.user}')
    await client.change_presence(activity=discord.Game(name="Trackeao Lacra"))

@client.event
async def setup_hook():
    async with aiohttp.ClientSession() as session:
        champions = await fetch_and_store_champion_data(session)
    client.loop.create_task(check_players(champions))

async def main():
    async with client:
        await client.start(TOKEN)

# Run the main function
asyncio.run(main())
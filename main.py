import discord
from discord import Embed
import asyncio
import aiohttp
import json
import os
from lol_handle import *

intents = discord.Intents.default()
client = discord.Client(intents=intents)

TOKEN = 'MTI1NjM0MDkyMDMzNzU2Nzc0Ng.GkY8cb.RVs08J8doU-YXT3KqidbNfrYijeJKgW7O8s-sk'
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
            for name, (puuid, is_playing, test) in summoners.items():
                game_info = await fetch_active_game(session, puuid)
                if game_info:
                    game_id = game_info['gameId']
                    participant = next((p for p in game_info['participants'] if p['puuid'] == puuid), None)
                    if participant:
                        champion_id = participant['championId']
                        champion_name = champions.get(champion_id, "Unknown Champion")


                        if not is_playing:
                            summoners[name][1] = True
                            summoners[name][2] = game_id
                            tier, rank, lp = await get_current_elo(session, puuid)

                            embed = Embed(title=f'{name} está en partida!', color=0xff0000)
                            embed.add_field(name='Campeón', value=champion_name, inline=False)
                            embed.add_field(name='ELO actual', value=f'{tier} {rank} {lp} LPs', inline=False)
                            await channel.send(embed=embed)


                elif is_playing:
                    game_id = summoners[name][2]
                    tier, rank, lp = await get_current_elo(session, puuid)
                    relevant_data = await post_game(session, puuid, game_id)
                    
                    embed = Embed(title=f'{name} ha terminado la partida!', color=0xff0000)
                    embed.add_field(name='Resultado', value=relevant_data["Match Outcome"], inline=False)
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
    print(f'Bot is ready. Logged in as {client.user}')

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
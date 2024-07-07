import json

RIOT_API_KEY = 'RGAPI-eef7c8ac-953d-4fd3-9285-70a95419ee61'  # Replace with your Riot API key
CHAMPION_DATA_URL = 'https://ddragon.leagueoflegends.com/cdn/14.13.1/data/en_US/champion.json'


async def fetch_and_store_champion_data(session):
    url = "https://ddragon.leagueoflegends.com/cdn/14.13.1/data/en_US/champion.json"
    async with session.get(url) as response:
        champion_data = await response.json()
        champions = {int(champion_data['data'][champ]['key']): champion_data['data'][champ]['name'] for champ in champion_data['data']}
        return champions


async def fetch_active_game(session, puuid):
    url = f'https://euw1.api.riotgames.com/lol/spectator/v5/active-games/by-summoner/{puuid}'
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
        "Accept-Language": "es-ES,es;q=0.6",
        "Accept-Charset": "application/x-www-form-urlencoded; charset=UTF-8",
        "Origin": "https://developer.riotgames.com",
        "X-Riot-Token": RIOT_API_KEY
    }
    async with session.get(url, headers=headers) as response:
        if response.status == 200:
            data = await response.json()
            if data["gameQueueConfigId"] == 420:
                return await response.json()
            else:
                return None
        return None
    

async def get_current_elo(session, puuid):
    url = f'https://euw1.api.riotgames.com/lol/summoner/v4/summoners/by-puuid/{puuid}'
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
        "Accept-Language": "es-ES,es;q=0.6",
        "Accept-Charset": "application/x-www-form-urlencoded; charset=UTF-8",
        "Origin": "https://developer.riotgames.com",
        "X-Riot-Token": RIOT_API_KEY
    }
        
    async with session.get(url, headers=headers) as response:
        if response.status == 200:
            try:
                data = await response.json()
                account_id = data["id"]
                
                url2 = f'https://euw1.api.riotgames.com/lol/league/v4/entries/by-summoner/{account_id}'
                
                async with session.get(url2, headers=headers) as response2:
                    if response2.status == 200:
                        try:
                            data2 = await response2.json()
                            for entry in data2:
                                if entry.get("queueType") == "RANKED_SOLO_5x5":
                                    tier = entry.get("tier")
                                    rank = entry.get("rank")
                                    league_points = entry.get("leaguePoints")
                                    return tier, rank, league_points
                        except json.JSONDecodeError:
                            pass  # Handle JSON decoding errors
            except json.JSONDecodeError:
                pass  # Handle JSON decoding errors
    
    return None, None, None  # Return default values or handle errors appropriately


async def get_name(session, puuid):
    url = f'https://europe.api.riotgames.com/riot/account/v1/accounts/by-puuid/{puuid}'
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
        "Accept-Language": "es-ES,es;q=0.6",
        "Accept-Charset": "application/x-www-form-urlencoded; charset=UTF-8",
        "Origin": "https://developer.riotgames.com",
        "X-Riot-Token": RIOT_API_KEY
    }
        
    async with session.get(url, headers=headers) as response:
        if response.status == 200:
            try:
                data = await response.json()
                account_name = data["gameName"]
                account_tg = data["tagLine"]
                
                return account_name, account_tg
            except json.JSONDecodeError:
                pass  # Handle JSON decoding errors
    
    return None, None  # Return default values or handle errors appropriately


async def post_game(session, puuid, game_id):
    url = f'https://europe.api.riotgames.com/lol/match/v5/matches/EUW1_{game_id}'
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
        "Accept-Language": "es-ES,es;q=0.6",
        "Accept-Charset": "application/x-www-form-urlencoded; charset=UTF-8",
        "Origin": "https://developer.riotgames.com",
        "X-Riot-Token": RIOT_API_KEY
    }
    async with session.get(url, headers=headers) as response:
        if response.status == 200:
            data = await response.json()

            participant_data = None
            for participant in data['info']['participants']:
                if participant['puuid'] == puuid:
                    participant_data = participant
                    break

            if participant_data:
                match_outcome = "Victoria" if participant_data['win'] else "Derrota"
                kda = f"{participant_data['kills']}/{participant_data['deaths']}/{participant_data['assists']}"
                relevant_data = {
                    "Match Outcome": match_outcome,
                    "KDA": kda,
                    "Kills": participant_data['kills'],
                    "Deaths": participant_data['deaths'],
                    "Assists": participant_data['assists'],
                    "Champion": participant_data['championName'],
                    "Role": participant_data['individualPosition'],
                    "Total Damage Dealt": participant_data['totalDamageDealtToChampions'],
                    "Total Damage Taken": participant_data['totalDamageTaken'],
                    "Gold Earned": participant_data['goldEarned'],
                    "Vision Score": participant_data['visionScore'],
                    "Team Position": participant_data['teamPosition'],
                    "Lane": participant_data['lane'],
                    "Items Purchased": participant_data['itemsPurchased']
                }
                return relevant_data

        return None
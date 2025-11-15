import aiohttp

class Supabase:
    def __init__(self):
        self.session = aiohttp.ClientSession()
        
    async def create_user(self, user:dict):
        pass
    
    async def get_user(self, user_id:int):
        return None
    
    async def save_user(self, user_id:int, user:dict):
        pass
        
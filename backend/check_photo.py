import asyncio
from db import grievances_col
async def run():
    doc = await grievances_col.find_one({'photo_id': {'$exists': True}})
    print(doc)
asyncio.run(run())

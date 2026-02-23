import asyncio
from db import grievances_col

async def main():
    pipeline = [{"$group": {"_id": "$status", "count": {"$sum": 1}}}]
    cursor = grievances_col.aggregate(pipeline)
    async for doc in cursor:
        print(doc)

if __name__ == "__main__":
    asyncio.run(main())

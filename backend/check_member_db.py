import asyncio
from db import grievances_col, member_requests_col

async def main():
    g = await grievances_col.find_one({})
    m = await member_requests_col.find_one({})
    print("Grievance Sample:", g)
    print("Member Request Sample:", m)

if __name__ == "__main__":
    asyncio.run(main())

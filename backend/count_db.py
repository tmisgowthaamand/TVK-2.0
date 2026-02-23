import asyncio
from db import grievances_col, member_requests_col

async def main():
    print("Grievances Count:", await grievances_col.count_documents({}))
    print("Member Requests (Suggestions) Count:", await member_requests_col.count_documents({"type": "Suggestion"}))
    print("Member Requests (Volunteers) Count:", await member_requests_col.count_documents({"type": "Volunteer"}))
    print("Total Member Requests:", await member_requests_col.count_documents({}))

if __name__ == "__main__":
    asyncio.run(main())

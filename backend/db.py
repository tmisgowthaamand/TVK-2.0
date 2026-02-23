import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

# Setup Voter DB
MONGO_URI_VOTERS = os.getenv("MONGO_URI_VOTERS")
MONGO_DB_VOTERS = os.getenv("MONGO_DB_VOTERS")

voter_client = AsyncIOMotorClient(MONGO_URI_VOTERS)
voter_db = voter_client[MONGO_DB_VOTERS]
voters_collection = voter_db[os.getenv("MONGO_COLLECTION_VOTERS")]

# Setup Members DB
MONGO_URI_MEMBERS = os.getenv("MONGO_URI_MEMBERS")
MONGO_DB_MEMBERS = os.getenv("MONGO_DB_MEMBERS")

member_client = AsyncIOMotorClient(MONGO_URI_MEMBERS)
member_db = member_client[MONGO_DB_MEMBERS]
grievances_col = member_db[os.getenv("MONGO_COLLECTION_GRIEVANCES")]
member_requests_col = member_db[os.getenv("MONGO_COLLECTION_MEMBER_REQUESTS")]
logs_col = member_db[os.getenv("MONGO_COLLECTION_LOGS")]
booth_pulse_col = member_db[os.getenv("MONGO_COLLECTION_BOOTH_PULSE", "booth_pulse")]

import os
import datetime
from fastapi import FastAPI, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from bot_logic import handle_incoming_message
from db import voters_collection, grievances_col, member_requests_col
from whatsapp import send_text_message

load_dotenv()

CAT_MAP = {
    "cat_1": "Water & Drainage", "cat_2": "Roads & Infra", "cat_3": "Electricity",
    "cat_4": "Public Transport", "cat_5": "Education", "cat_6": "Healthcare",
    "cat_7": "Women Safety", "cat_8": "Employment", "cat_9": "Others",
    "pcat_1": "Water & Drainage", "pcat_2": "Roads & Infra", "pcat_3": "Electricity",
    "pcat_4": "Garbage & Sanitation", "pcat_5": "Public Property Damage", "pcat_6": "Others",
    "vol_1": "Volunteer @ Booth", "vol_2": "Organise Meetings", "vol_3": "Spread Information", "vol_4": "Future Coordination"
}

app = FastAPI(title="TVK WhatsApp Bot Backend")

app.mount("/assets", StaticFiles(directory="assets"), name="assets")

# CORS Configuration
origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

WHATSAPP_VERIFY_TOKEN = os.getenv("WHATSAPP_VERIFY_TOKEN", "tvk_verify_token_2026")

@app.get("/")
def read_root():
    return {"status": "ok", "message": "Backend is running"}

@app.get("/api/dashboard/stats")
async def get_stats():
    # Gather live data from DB!
    total_voters = await voters_collection.count_documents({})
    open_issues = await grievances_col.count_documents({"status": "Open"})
    # Existing member requests might not have 'type', so we look for our new types + old MBR prefix
    suggestions = await member_requests_col.count_documents({"$or": [{"type": "Suggestion"}, {"referenceId": {"$regex": "^MBR"}}]})
    volunteers = await member_requests_col.count_documents({"type": "Volunteer"})
    
    return {
        "stats": [
            {"id": 1, "title": "Total Voters Registered", "value": str(total_voters), "trend": "Database link active"},
            {"id": 2, "title": "Open Grievances", "value": str(open_issues), "trend": "Live from MongoDB"},
            {"id": 3, "title": "Suggestions Received", "value": str(suggestions), "trend": "Live from MongoDB"},
            {"id": 4, "title": "Active Volunteers", "value": str(volunteers), "trend": "Live from MongoDB"}
        ]
    }

@app.get("/api/dashboard/grievances")
async def get_grievances():
    cursor = grievances_col.find().sort("_id", -1).limit(10)
    items = await cursor.to_list(length=10)
    results = []
    for i in items:
        ref_id = i.get("ref_id") or i.get("ticketId") or "Unknown"
        voter_name = i.get("voter_name") or i.get("voterName") or i.get("name") or "Anonymous"
        cat_raw = i.get("category") or "Uncategorized"
        results.append({
            "id": ref_id,
            "name": voter_name,
            "booth": str(i.get("booth") or i.get("partNumber") or "Unknown"),
            "category": CAT_MAP.get(cat_raw, cat_raw),
            "status": i.get("status", "Open"),
            "date": i.get("timestamp") or (i.get("createdAt").strftime("%d %b %Y") if i.get("createdAt") else "N/A")
        })
    return {"grievances": results}

@app.get("/api/dashboard/all_grievances")
async def get_all_grievances():
    cursor = grievances_col.find().sort("_id", -1).limit(100)
    items = await cursor.to_list(length=100)
    results = []
    for i in items:
        ref_id = i.get("ref_id") or i.get("ticketId") or ""
        voter_name = i.get("voter_name") or i.get("voterName") or i.get("name") or ""
        cat_raw = i.get("category") or i.get("area", "General")
        results.append({
            "id": ref_id,
            "name": voter_name,
            "booth": str(i.get("booth") or i.get("partNumber") or ""),
            "category": CAT_MAP.get(cat_raw, cat_raw),
            "status": i.get("status", "Open"),
            "date": i.get("timestamp") or (i.get("createdAt").strftime("%d %b %Y") if i.get("createdAt") else ""),
            "description": i.get("description") or i.get("message") or ""
        })
    return {"grievances": results}

@app.get("/api/dashboard/suggestions")
async def get_suggestions():
    cursor = member_requests_col.find({"$or": [{"type": "Suggestion"}, {"referenceId": {"$regex": "^MBR"}}]}).sort("_id", -1).limit(100)
    items = await cursor.to_list(length=100)
    results = []
    for i in items:
        ref_id = i.get("ref_id") or i.get("referenceId") or ""
        voter_name = i.get("voter_name") or i.get("name") or ""
        results.append({
            "id": ref_id,
            "name": voter_name,
            "booth": str(i.get("booth") or i.get("partNumber") or ""),
            "suggestion": i.get("suggestion") or i.get("area") or "Member Request",
            "status": i.get("status", "Pending"),
            "date": i.get("timestamp") or (i.get("createdAt").strftime("%d %b %Y") if i.get("createdAt") else "")
        })
    return {"suggestions": results}

@app.get("/api/dashboard/volunteers")
async def get_volunteers():
    cursor = member_requests_col.find({"type": "Volunteer"}).sort("_id", -1).limit(100)
    items = await cursor.to_list(length=100)
    results = []
    for i in items:
        role_raw = i.get("role", "")
        results.append({
            "id": i.get("ref_id", ""),
            "name": i.get("voter_name", i.get("name", "")),
            "booth": str(i.get("booth", i.get("partNumber", ""))),
            "role": CAT_MAP.get(role_raw, role_raw),
            "status": i.get("status", "Registered"),
            "date": i.get("timestamp", i.get("createdAt").strftime("%d %b %Y") if i.get("createdAt") else "")
        })
    return {"volunteers": results}

@app.get("/api/dashboard/booth_analytics")
async def get_booth_analytics():
    pipeline = [
        {"$project": {"booth_id": {"$ifNull": ["$booth", "$partNumber"]}}},
        {"$group": {"_id": "$booth_id", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 15}
    ]
    cursor = grievances_col.aggregate(pipeline)
    items = await cursor.to_list(length=15)
    results = [{"booth": str(i["_id"]), "issues": i["count"]} for i in items if i["_id"]]
    return {"analytics": results}

@app.get("/api/dashboard/voters")
async def get_voters():
    cursor = voters_collection.find().sort("_id", -1).limit(200)
    items = await cursor.to_list(length=200)
    results = []
    for i in items:
        results.append({
            "id": i.get("voterId") or "N/A",
            "name": i.get("name") or "Anonymous",
            "booth": str(i.get("partNumber") or "N/A"),
            "district": i.get("district") or "N/A",
            "status": i.get("status") or "Active"
        })
    return {"voters": results}

@app.post("/api/dashboard/update_status")
async def update_status(request: Request):
    data = await request.json()
    ref_id = data.get("id")
    new_status = data.get("status")
    
    # Find the record first to get the phone number
    record = await grievances_col.find_one({"$or": [{"ref_id": ref_id}, {"ticketId": ref_id}]})
    col = grievances_col
    
    if not record:
        record = await member_requests_col.find_one({"$or": [{"ref_id": ref_id}, {"referenceId": ref_id}]})
        col = member_requests_col
        
    if record:
        # Update in DB
        await col.update_one(
            {"_id": record["_id"]},
            {"$set": {"status": new_status, "updatedAt": datetime.datetime.now()}}
        )
        
        # Send WhatsApp Notification
        phone = record.get("voter_phone") or record.get("phoneNumber")
        if phone:
            msg = f"🔔 *Constituency Update*\n\nYour reported issue/suggestion (ID: {ref_id}) status has been changed to: *{new_status}*.\n\nThank you for your engagement.\n_TVK Kavundampalayam Team_"
            send_text_message(phone, msg)
        
    return {"status": "success"}

@app.get("/webhook")
async def verify_webhook(request: Request):
    query_params = request.query_params
    mode = query_params.get("hub.mode")
    token = query_params.get("hub.verify_token")
    challenge = query_params.get("hub.challenge")

    if mode and token:
        if mode == "subscribe" and token == WHATSAPP_VERIFY_TOKEN:
            return int(challenge)
        raise HTTPException(status_code=403, detail="Forbidden")
    raise HTTPException(status_code=400, detail="Bad Request")

@app.post("/webhook")
async def handle_webhook(request: Request):
    data = await request.json()

    if data.get("object") == "whatsapp_business_account":
        for entry in data.get("entry", []):
            for change in entry.get("changes", []):
                value = change.get("value", {})
                if "messages" in value:
                    for message in value["messages"]:
                        phone_number = message.get("from")
                        msg_type = message.get("type")
                        
                        text = None
                        lat = None
                        lon = None
                        image_id = None
                        
                        if msg_type == "text":
                            text = message["text"]["body"]
                        elif msg_type == "interactive":
                            interactive = message["interactive"]
                            itype = interactive.get("type")
                            if itype == "button_reply":
                                text = interactive["button_reply"]["id"]
                            elif itype == "list_reply":
                                text = interactive["list_reply"]["id"]
                        elif msg_type == "location":
                            lat = message["location"]["latitude"]
                            lon = message["location"]["longitude"]
                        elif msg_type == "image":
                            image_id = message["image"]["id"]
                            text = message["image"].get("caption", "IMAGE")
                        
                        await handle_incoming_message(phone_number, text, lat, lon, image_id)
        return JSONResponse(content={"status": "ok"})
    return JSONResponse(status_code=404, content={"status": "not_found"})

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 3000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)

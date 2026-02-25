import time
import asyncio
import uuid
import datetime
import random
from db import voters_collection, grievances_col, member_requests_col, booth_pulse_col
from whatsapp import send_text_message, send_image_message, send_button_message, send_list_message

# Store sessions in memory { phone_number: { 'state': ..., 'last_active': ..., 'epic': ..., 'name': ..., 'booth': ... } }
sessions = {}

SESSION_TIMEOUT = 1800 # 30 mins

import os
WHATSAPP_WEBHOOK_URL = os.getenv("WHATSAPP_WEBHOOK_URL", "http://127.0.0.1:3000/webhook")
IMG_BASE = WHATSAPP_WEBHOOK_URL.replace("/webhook", "") + "/assets"

IMG_URLS = {
    "welcome_banner": f"{IMG_BASE}/welcome_banner.jpg?v=1",
    "desc_banner": f"{IMG_BASE}/desc_banner.png?v=2",
    "photo_banner": f"{IMG_BASE}/photo_banner.png?v=2",
    "loc_banner": f"{IMG_BASE}/loc_banner.png?v=2",
    "thank_you": f"{IMG_BASE}/thank_you.png?v={int(time.time())}",
    "success": f"{IMG_BASE}/success.png?v=2",
    "ward_connect": f"{IMG_BASE}/ward_connect.png?v=2",
    "epic_not_found": f"{IMG_BASE}/epic_not_found.png?v=1",
    "invite_1": f"{IMG_BASE}/invite_1.png?v=1",
    "invite_2": f"{IMG_BASE}/invite_2.png?v=1",
    "invite_3": f"{IMG_BASE}/invite_3.png?v=1",
    "booth_results": f"{IMG_BASE}/booth_results.png?v=1",
    "booth_cooldown": f"{IMG_BASE}/booth_cooldown.png?v=1",
    "track_submission": f"{IMG_BASE}/track_submission.png?v=1",
    "status_report": f"{IMG_BASE}/status_report.png?v=1",
    "constituency_update": f"{IMG_BASE}/constituency_update.png?v=1",
    "invalid_ref": f"{IMG_BASE}/invalid_ref.png?v=1",
    "engagement_summary": f"{IMG_BASE}/engagement_summary.png?v=1"
}

CAT_MAP = {
    "cat_1": "Water & Drainage", "cat_2": "Roads & Infra", "cat_3": "Electricity",
    "cat_4": "Public Transport", "cat_5": "Education", "cat_6": "Healthcare",
    "cat_7": "Agriculture & Farmers", "cat_8": "Women Safety", "cat_9": "Sports & Youth", "cat_10": "Others",
    "pcat_1": "Water & Drainage", "pcat_2": "Roads & Infra", "pcat_3": "Electricity",
    "pcat_4": "Garbage & Sanitation", "pcat_5": "Public Property Damage", "pcat_6": "Others",
    "vol_1": "Volunteer @ Booth", "vol_2": "Organise Meetings", "vol_3": "Spread Information", "vol_4": "Future Coordination"
}

PULSE_DATA = {
    "1": {"title": "Water & Drainage", "votes": 18, "percent": 42},
    "2": {"title": "Roads & Infra", "votes": 11, "percent": 25},
    "3": {"title": "Electricity", "votes": 6, "percent": 15},
    "4": {"title": "Transport", "votes": 4, "percent": 10},
    "5": {"title": "Healthcare", "votes": 3, "percent": 8}
}

async def handle_incoming_message(phone, incoming_text, lat=None, lon=None, image_id=None):
    current_time = time.time()
    session = sessions.get(phone, None)
    
    cancel_keywords = ["hi", "hello", "start", "menu", "reset", "vanakkam"]
    if incoming_text and incoming_text.lower() in cancel_keywords:
        sessions[phone] = {"state": "ASK_HAS_EPIC", "last_active": current_time}
        send_welcome(phone)
        return
        
    if session and (current_time - session["last_active"] > SESSION_TIMEOUT):
        session = None
        
    if not session:
        sessions[phone] = {"state": "ASK_HAS_EPIC", "last_active": current_time}
        send_welcome(phone)
        return

    state = session.get("state")
    session["last_active"] = current_time

    if state == "ASK_HAS_EPIC":
        await handle_ask_has_epic(phone, incoming_text, session)
    elif state == "ASK_EPIC":
        await verify_epic(phone, incoming_text, session)
    elif state == "MAIN_MENU":
        await handle_main_menu(phone, incoming_text, session)
    elif state == "FLOW1_CAT":
        handle_flow1_cat(phone, incoming_text, session)
    elif state == "FLOW1_DESC":
        handle_flow1_desc(phone, incoming_text, session)
    elif state == "FLOW1_PHOTO":
        handle_flow1_photo(phone, image_id, incoming_text, session)
    elif state == "FLOW1_LOC":
        await handle_loc_skip(phone, incoming_text, lat, lon, session, "FLOW1")

    elif state == "FLOW2_SUGG":
        handle_flow2_sugg(phone, incoming_text, session)
    elif state == "FLOW2_LOC":
        await handle_loc_skip(phone, incoming_text, lat, lon, session, "FLOW2")

    elif state == "FLOW3_MODE":
        handle_flow3_mode(phone, incoming_text, session)
    elif state == "FLOW3_LOC":
        await handle_loc_skip(phone, incoming_text, lat, lon, session, "FLOW3")

    elif state == "FLOW4_LOC":
        await handle_loc_skip(phone, incoming_text, lat, lon, session, "FLOW4")

    elif state == "FLOW5_REF":
        await handle_flow5_ref(phone, incoming_text, session)

    elif state == "FLOW7_POLL":
        await handle_flow7_poll(phone, incoming_text, session)

    elif state == "FLOW8_CAT":
        handle_flow8_cat(phone, incoming_text, session)
    elif state == "FLOW8_PHOTO":
        handle_flow8_photo(phone, image_id, incoming_text, session)
    elif state == "FLOW8_LOC":
        await handle_loc_skip(phone, incoming_text, lat, lon, session, "FLOW8")
        
    elif state == "POST_FLOW_EPIC":
        await handle_post_flow_epic(phone, incoming_text, session)
        
    elif state == "FLOW9_NETWORKS":
        await handle_flow9_networks(phone, incoming_text, session)
        
    elif state == "LOOP_PROMPT":
        if incoming_text and incoming_text.lower() == "btn_main_menu":
            session["state"] = "MAIN_MENU"
            await send_main_menu(phone, session)
        elif incoming_text and ("ward" in incoming_text.lower() or "connect" in incoming_text.lower()):
             # Trigger ward connect logic
             await handle_main_menu(phone, "menu_10", session)
        elif incoming_text and ("tvk" in incoming_text.lower() or "family" in incoming_text.lower() or "itwing" in incoming_text.lower() or "btn_tvk" in incoming_text.lower() or "invite" in incoming_text.lower() or "btn_invite" in incoming_text.lower()):
             # Directly handle the network/invite selection
             await handle_flow9_networks(phone, incoming_text, session)
        else:
             # If they type something else, just take them to main menu
             session["state"] = "MAIN_MENU" 
             await send_main_menu(phone, session)
    elif state == "DONE":
        await send_loop_prompt(phone, session)
    else:
        # Fallback
        sessions[phone] = {"state": "ASK_HAS_EPIC", "last_active": current_time}
        send_welcome(phone)

def send_welcome(phone):
    msg = """Vanakkam 🙏

This is the official WhatsApp of Venkatraman, TVK Candidate – Kavundampalayam.

We are building a structured, booth-level understanding of issues in this constituency so that future priorities are based on real voter input.

*Do you already have a Voter ID (EPIC number)?*"""
    send_button_message(phone, msg, [
        {"id": "btn_have_epic", "title": "✅ Have Voter ID"},
        {"id": "btn_no_epic", "title": "❌ Don't Have"}
    ], IMG_URLS["welcome_banner"])

async def handle_ask_has_epic(phone, text, session):
    text_lower = text.lower() if text else ""
    if "btn_have_epic" in text_lower or "have" in text_lower or "yes" in text_lower:
        session["state"] = "ASK_EPIC"
        msg = "Please enter your EPIC number (Voter ID number).\n\nExample: ABC123456"
        send_image_message(phone, IMG_URLS["welcome_banner"], msg)
    elif "btn_no_epic" in text_lower or "don" in text_lower or "no" in text_lower:
        session["state"] = "MAIN_MENU"
        session["name"] = "Citizen"
        session["booth"] = "Not provided yet"
        session["epic"] = None
        await send_main_menu(phone, session)
    else:
        send_text_message(phone, "Please select an option using the buttons.")

async def verify_epic(phone, epic, session):
    epic = epic.upper().strip()
    
    if len(epic) < 5 or len(epic) > 20:
        msg = "We could not locate this EPIC number in our constituency records.\n\nPlease verify and enter a valid formatted EPIC. If you believe this is an error, you may contact your booth-level representative."
        send_image_message(phone, IMG_URLS["epic_not_found"], msg)
        return

    voter = await voters_collection.find_one({"voterId": epic})
    if voter:
        name = voter.get("name", "Unknown Voter")
        booth = str(voter.get("partNumber", "Unknown"))
    else:
        name = "Unknown (Guest)"
        booth = "Pending"
        today = datetime.datetime.now().strftime("%d %b %Y")
        await voters_collection.insert_one({
            "voterId": epic,
            "name": name,
            "partNumber": booth,
            "phone": phone,
            "status": "Unverified",
            "source": "WhatsApp Bot",
            "createdAt": today
        })
        
    session["state"] = "MAIN_MENU"
    session["name"] = name
    session["booth"] = booth
    session["epic"] = epic
    await send_main_menu(phone, session)

async def send_main_menu(phone, session):
    name = session.get("name", "Citizen")
    booth = session.get("booth", "Not provided")
    epic = session.get("epic")
    
    if epic and name != "Unknown (Guest)" and name != "Citizen":
        text = f"""Thank you, *{name}*

We have identified you as a voter from:
📍 *Booth:* {booth}  🏛️ *Assembly:* Kavundampalayam
🏛️ *Parliament:* Coimbatore

We are documenting concerns booth-wise so that real priorities are shaped by people like you.
This system is designed to ensure that each booth's voice is heard clearly and documented responsibly.

*How would you like to engage today?*"""
    elif epic:
        text = f"""Thank you!

We have recorded your Voter ID: *{epic}*.
Your exact booth assignment is currently pending verification in our system.

We are documenting concerns booth-wise so that real priorities are shaped by people like you.
This system is designed to ensure that each booth's voice is heard clearly and documented responsibly.

*How would you like to engage today?*"""
    else:
        text = f"""Welcome!

While your Voter ID is pending, you can still participate! Every voice in Kavundampalayam matters.

We are documenting concerns so that future priorities are shaped by real people like you.

*How would you like to engage today?*"""
    
    sections = [
        {
            "title": "Core Services",
            "rows": [
                {"id": "menu_1", "title": "🔴 Report Local Issue"},
                {"id": "menu_2", "title": "💡 Ideas & Improvements"},
                {"id": "menu_3", "title": "🤝 Participate"},
                {"id": "menu_4", "title": "📢 Stay Informed"}
            ]
        },
        {
            "title": "My Account",
            "rows": [
                {"id": "menu_5", "title": "🔍 Track My Issue"},
                {"id": "menu_6", "title": "📋 My Activity"}
            ]
        },
        {
            "title": "Community",
            "rows": [
                {"id": "menu_7", "title": "📊 Booth Pulse"},
                {"id": "menu_8", "title": "📸 Photo Evidence"},
                {"id": "menu_9", "title": "🌐 TVK Networks"},
                {"id": "menu_10", "title": "📞 Ward Connect"},
                {"id": "menu_11", "title": "🗣️ Invite a Voter"}
            ]
        }
    ]
    send_list_message(phone, text, "Select Option", sections)

async def handle_main_menu(phone, text, session):
    sel = text.lower() if text else ""
    if "10" in sel or "ward" in sel or "menu_10" in sel:
        booth = session.get('booth', 'Unknown')
        name = "Suresh Murugan"
        phone_num = "+919876543210"
        
        msg = f"""📞 *Ward Connect — Booth {booth}*

Our movement is growing! There are currently *47 active participants* in your booth.

Your designated Ward Coordinator is available for immediate support and coordination:

👤 *Name:* {name}
🏛️ *Booth:* {booth}
📍 *Area:* Gandhi Nagar, Kavundampalayam

*Direct WhatsApp Call:*
https://wa.me/{phone_num.replace('+', '')}

_Click the link above to start a voice call or chat._"""
        send_image_message(phone, IMG_URLS["ward_connect"], msg)
        send_button_message(phone, "Would you like to explore other options?", [{"id": "btn_main_menu", "title": "🏠 Main Menu"}], None)
        session["state"] = "LOOP_PROMPT"

    elif "1" in sel or "issue" in sel or "report" in sel or "menu_1" in sel:
        session["state"] = "FLOW1_CAT"
        sections = [{"title": "Categories", "rows": [
            {"id": "cat_1", "title": "Water & Drainage"},
            {"id": "cat_2", "title": "Roads & Infra"},
            {"id": "cat_3", "title": "Electricity"},
            {"id": "cat_4", "title": "Public Transport"},
            {"id": "cat_5", "title": "Education"},
            {"id": "cat_6", "title": "Healthcare"},
            {"id": "cat_7", "title": "Agriculture & Farmers"},
            {"id": "cat_8", "title": "Women Safety"},
            {"id": "cat_9", "title": "Sports & Youth"},
            {"id": "cat_10", "title": "Others"},
        ]}]
        msg = f"Thank you, {session['name']}.\nPlease select the area where you are facing a concern:"
        send_list_message(phone, msg, "Select Category", sections, "📝 Report an Issue")
        
    elif "2" in sel or "idea" in sel or "improve" in sel or "menu_2" in sel:
        session["state"] = "FLOW2_SUGG"
        msg = "We believe strong constituencies are built not just by solving issues, but by listening to constructive ideas.\n\nPlease share your suggestion in up to 250 characters."
        send_image_message(phone, IMG_URLS["desc_banner"], msg)
    
    elif "3" in sel or "participate" in sel or "menu_3" in sel:
        session["state"] = "FLOW3_MODE"
        msg = f"🤝 Participate\n\nThat's encouraging to hear, {session['name']}.\nHow would you like to participate?"
        sections = [{"title": "Roles", "rows": [
            {"id": "vol_1", "title": "Volunteer @ Booth"},
            {"id": "vol_2", "title": "Organise Meetings"},
            {"id": "vol_3", "title": "Spread Information"},
            {"id": "vol_4", "title": "Future Coordination"}
        ]}]
        send_list_message(phone, msg, "Select Mode", sections)
        
    elif "4" in sel or "informed" in sel or "menu_4" in sel:
        session["state"] = "FLOW4_LOC"
        body = "Please share your location (Pin or Live Location) to receive updates specific to your area.\n\nYou may also type SKIP or use the button below."
        send_button_message(phone, body, [{"id": "skip_loc", "title": "SKIP"}], IMG_URLS["loc_banner"])
        
    elif "5" in sel or "track" in sel or "menu_5" in sel:
        session["state"] = "FLOW5_REF"
        send_image_message(phone, IMG_URLS["track_submission"], "🔍 Track Your Submission\n\nPlease enter your Reference ID to check the current status.\nYour Reference ID was shared when you first submitted.\n\nExamples: GRV12345, SUG67890, VOL11223")

    elif "6" in sel or "activity" in sel or "menu_6" in sel:
        # Load real data from mongodb 2 - supporting both schemas
        issues_raised = await grievances_col.count_documents({"phoneNumber": phone}) or await grievances_col.count_documents({"voter_phone": phone})
        issues_open = await grievances_col.count_documents({"$and": [{"status": "Open"}, {"$or": [{"phoneNumber": phone}, {"voter_phone": phone}]}]})
        issues_prog = await grievances_col.count_documents({"$and": [{"status": "In Progress"}, {"$or": [{"phoneNumber": phone}, {"voter_phone": phone}]}]})
        issues_res = await grievances_col.count_documents({"$and": [{"status": "Resolved"}, {"$or": [{"phoneNumber": phone}, {"voter_phone": phone}]}]})
        
        sugg_count = await member_requests_col.count_documents({"$and": [{"$or": [{"type": "Suggestion"}, {"referenceId": {"$regex": "^MBR"}}]}, {"$or": [{"phoneNumber": phone}, {"voter_phone": phone}]}]})
        
        vol_req = await member_requests_col.find_one({"$and": [{"type": "Volunteer"}, {"$or": [{"phoneNumber": phone}, {"voter_phone": phone}]}]})
        vol_status = "Registered" if vol_req else "None"
        vol_role_raw = vol_req.get("role", "N/A") if vol_req else "N/A"
        vol_role = CAT_MAP.get(vol_role_raw, vol_role_raw)

        send_image_message(phone, IMG_URLS["engagement_summary"], f"""📋 Your Engagement Summary\n\n👤 {session['name']} | Booth {session['booth']} | Kavundampalayam
───────────────
🔴 Issues Raised: {issues_raised}
├ Open: {issues_open}
├ In Progress: {issues_prog}
└ Resolved: {issues_res}

💡 Suggestions: {sugg_count}

🤝 Volunteer: {vol_status}
└ Role: {vol_role}

📢 Updates: Subscribed

📊 Booth Pulse: Voted
───────────────
Thank you for being an active voice in shaping Kavundampalayam.""")
        await send_loop_prompt(phone, session)
        
    elif "7" in sel or "pulse" in sel or "menu_7" in sel:
        session["state"] = "FLOW7_POLL"
        msg = "📊 Booth Pulse — Quick Poll\n\nHelp us understand the biggest concern in your area right now.\nWhat is the #1 issue affecting your daily life?"
        sections = [{"title": "Options", "rows": [
            {"id": "poll_1", "description": "💧 Water & Drainage", "title": "Water & Drainage"},
            {"id": "poll_2", "description": "🛣️ Roads & Infrastructure", "title": "Roads & Infra"},
            {"id": "poll_3", "description": "⚡ Electricity & Power Cuts", "title": "Electricity"},
            {"id": "poll_4", "description": "🏫 Education & Schools", "title": "Education"}
        ]}]
        send_list_message(phone, msg, "Vote Now", sections)
        
    elif "8" in sel or "photo" in sel or "menu_8" in sel:
        session["state"] = "FLOW8_CAT"
        msg = "📸 Submit Photo Evidence\n\nYou can send a photo of any local issue — broken road, garbage dump, water leakage, damaged public property, etc.\n\nFirst, select the category:"
        sections = [{"title": "Categories", "rows": [
            {"id": "pcat_1", "title": "Water & Drainage"},
            {"id": "pcat_2", "title": "Roads & Infra"},
            {"id": "pcat_3", "title": "Electricity"},
            {"id": "pcat_4", "title": "Garbage & Sanitation"},
            {"id": "pcat_5", "title": "Public Property Damage"},
            {"id": "pcat_6", "title": "Others"}
        ]}]
        send_list_message(phone, msg, "Select Category", sections)

    elif "9" in sel or "invite" in sel or "network" in sel or "menu_9" in sel:
        session["state"] = "FLOW9_NETWORKS"
        msg = "🌐 *TVK Networks & Portals*\n\nExplore our digital initiatives or invite others to join the movement:"
        send_button_message(phone, msg, [
            {"id": "btn_tvk_family", "title": "🌐 TVK Family"},
            {"id": "btn_tvk_itwing", "title": "💻 TVK IT Wing"},
            {"id": "btn_main_menu", "title": "🏠 Main Menu"}
        ], IMG_URLS["welcome_banner"])

    elif "11" in sel or "invite" in sel or "menu_11" in sel:
        # Reuse flow 9 logic for invite button
        await handle_flow9_networks(phone, "btn_invite", session)
        
    else:
        send_text_message(phone, "Please select a valid option from the menu.")


def handle_flow1_cat(phone, text, session):
    session["cat"] = text
    session["state"] = "FLOW1_DESC"
    body = "Please describe the situation briefly (up to 250 characters).\n\nSpecific details help us understand recurring patterns in your booth."
    send_button_message(phone, body, [{"id": "skip_desc", "title": "SKIP"}], IMG_URLS["desc_banner"])

def handle_flow1_desc(phone, text, session):
    session["desc"] = text
    session["state"] = "FLOW1_PHOTO"
    body = "Thank you for the information. Now, please share a photo of the issue if possible.\n\nVisual evidence helps our team assess the situation faster."
    send_button_message(phone, body, [{"id": "skip_photo", "title": "SKIP"}], IMG_URLS["photo_banner"])

def handle_flow1_photo(phone, image_id, text, session):
    is_skip = (text and "skip" in text.lower())
    
    if image_id:
        session["photo_id"] = image_id
        send_text_message(phone, "Thank you! This image is very helpful for our analysis.")
    elif not is_skip and text:
        # If they sent text instead of an image and it's not a skip
        send_text_message(phone, "Thank you for the update!")

    session["state"] = "FLOW1_LOC"
    body = "To help us identify the exact spot and resolve it faster, please share the location of the issue (Pin or Live Location)."
    send_button_message(phone, body, [{"id": "skip_loc", "title": "SKIP"}], IMG_URLS["loc_banner"])

def handle_flow2_sugg(phone, text, session):
    session["sugg"] = text
    session["state"] = "FLOW2_LOC"
    body = "Please share the location related to your suggestion (Pin or Live Location) so we can understand the context better.\n\nYou may also type SKIP or use the button below."
    send_button_message(phone, body, [{"id": "skip_loc", "title": "SKIP"}], IMG_URLS["loc_banner"])

def handle_flow3_mode(phone, text, session):
    session["vol_role"] = text
    session["state"] = "FLOW3_LOC"
    body = "Please share your location (Pin or Live Location) so our local organiser can reach you easily.\n\nYou may also type SKIP or use the button below."
    send_button_message(phone, body, [{"id": "skip_loc", "title": "SKIP"}], IMG_URLS["loc_banner"])

async def handle_flow5_ref(phone, text, session):
    ref = text.upper() if text else ""
    if not any(ref.startswith(prefix) for prefix in ["GRV", "SUG", "VOL", "PHT"]):
        send_image_message(phone, IMG_URLS["invalid_ref"], "Please enter a valid Reference ID starting with GRV, SUG, VOL, or PHT.\nExample: GRV12345")
        return
    
    record = await grievances_col.find_one({"$or": [{"ref_id": ref}, {"ticketId": ref}]})
    if not record:
        record = await member_requests_col.find_one({"$or": [{"ref_id": ref}, {"referenceId": ref}]})
        
    if record:
        cat_raw = record.get("category") or record.get("suggestion") or "General"
        cat = CAT_MAP.get(cat_raw, cat_raw)
        desc = record.get("description") or record.get("message") or ""
        booth = str(record.get("booth") or record.get("partNumber") or session.get('booth', 'Unknown'))
        date = record.get("timestamp") or (record.get("createdAt").strftime("%d %b %Y") if record.get("createdAt") else "N/A")

        send_image_message(phone, IMG_URLS["status_report"], f"""📋 Status Report\n
───────────────
🔖 Reference: {ref}
📁 Type: {record.get('type', 'Grievance')}
🏷️ Category: {cat}
📝 Issue: {desc[:50] + '...' if len(desc) > 50 else desc}
🏛️ Booth: {booth}
📅 Submitted: {date}
───────────────\n
⏳ Status: {record.get('status', 'Open')}\n
Your submission is on file. Our team will follow up as needed.""")
    else:
        send_text_message(phone, f"We could not find any record matching {ref}.\n\nPlease double-check your Reference ID and try again.")
    await send_loop_prompt(phone, session)

async def handle_flow7_poll(phone, text, session):
    sel = text.lower() if text else ""
    vote_val = ""
    if "poll_1" in sel or "water" in sel: vote_val = "poll_1"
    elif "poll_2" in sel or "road" in sel: vote_val = "poll_2"
    elif "poll_3" in sel or "electr" in sel: vote_val = "poll_3"
    elif "poll_4" in sel or "educat" in sel: vote_val = "poll_4"
    
    if not vote_val:
        send_text_message(phone, "Please select an option from the list above to vote.")
        return

    booth = session.get("booth", "Unknown")
    
    # Check if already voted (30-min cooldown)
    existing = await booth_pulse_col.find_one({"phone": phone, "booth": booth})
    if existing:
        vote_time = existing.get("timestamp")
        # Ensure it's a datetime object
        if isinstance(vote_time, datetime.datetime):
            time_diff = (datetime.datetime.now() - vote_time).total_seconds()
            if time_diff < 1800:
                mins_left = int((1800 - time_diff) / 60)
                send_image_message(phone, IMG_URLS["booth_cooldown"], f"📊 *Booth Pulse - Cool-down*\n\nYour voice has been recorded recently. To keep the live results balanced, you can update your pulse again in *{mins_left} minutes*.\n\n_Stay tuned for live updates!_")
                await send_loop_prompt(phone, session)
                return
        # If older than 30 mins, delete old vote to allow new one
        await booth_pulse_col.delete_one({"_id": existing["_id"]})

    # Save vote
    await booth_pulse_col.insert_one({
        "phone": phone,
        "booth": booth,
        "vote": vote_val,
        "timestamp": datetime.datetime.now()
    })

    # Calculate Live Results for this Booth
    results = await booth_pulse_col.aggregate([
        {"$match": {"booth": booth}},
        {"$group": {"_id": "$vote", "count": {"$sum": 1}}}
    ]).to_list(None)
    
    counts = {r["_id"]: r["count"] for r in results}
    total = sum(counts.values()) or 1
    
    poll_map = {
        "poll_1": "💧 Water & Drainage",
        "poll_2": "🛣️ Roads & Infra",
        "poll_3": "⚡ Electricity",
        "poll_4": "🏫 Education"
    }
    
    result_str = f"Thank you for voting, *{session['name']}*!\n\n─── *Booth {booth} Live Results* ───\n\n"

    for pid, label in poll_map.items():
        count = counts.get(pid, 0)
        pct = int((count / total) * 100)
        filled = int(pct / 10)
        bar = "█" * filled + "░" * (10 - filled)
        result_str += f"{label} {bar} {pct}% ({count} votes)\n"
        
    result_str += f"\n🗳️ *Total Votes: {total} from Booth {booth}*\n\nThis data directly shapes our constituency priorities."
    
    send_image_message(phone, IMG_URLS["booth_results"], result_str)

    await send_loop_prompt(phone, session)

def handle_flow8_cat(phone, text, session):
    session["photo_cat"] = text
    session["state"] = "FLOW8_PHOTO"
    send_button_message(phone, "Now please send a photo of the issue.\nYou can add a caption describing the problem along with the photo.", [{"id": "skip_photo", "title": "SKIP Photo"}], IMG_URLS["photo_banner"])

def handle_flow8_photo(phone, image_id, text, session):
    session["state"] = "FLOW8_LOC"
    session["photo_desc"] = text
    send_button_message(phone, "Photo received. Now please share the location of this issue (Pin or Live Location).", [{"id": "skip_loc", "title": "SKIP"}], IMG_URLS["loc_banner"])

async def handle_post_flow_epic(phone, text, session):
    skipped_epic = (text and text.upper() in ["SKIP", "⏭️ SKIP", "SKIP_POST_EPIC"])
    
    if not skipped_epic and text:
        epic = text.upper()
        voter = await voters_collection.find_one({"voterId": epic})
        if voter:
            session["name"] = voter.get("name", "Unknown Voter")
            session["booth"] = str(voter.get("partNumber", "Unknown"))
            session["epic"] = epic
        else:
            session["epic_unverified"] = epic
            today = datetime.datetime.now().strftime("%d %b %Y")
            # Insert this new unverified record into DB1
            await voters_collection.insert_one({
                "voterId": epic,
                "name": "Unknown (Guest)",
                "partNumber": "Pending",
                "phone": phone,
                "status": "Unverified",
                "source": "WhatsApp Bot",
                "createdAt": today
            })
            send_text_message(phone, "We recorded your input. Continuing to log your request...")
    
    # Mark that we bypassed the post-flow check
    session["post_flow_skipped"] = True
    
    lat = session.get("temp_lat")
    lon = session.get("temp_lon")
    skipped_loc = session.get("temp_skipped")
    flow = session.get("temp_flow")
    
    dummy_text = "SKIP" if skipped_loc else None 
    await handle_loc_skip(phone, dummy_text, lat, lon, session, flow)

async def handle_loc_skip(phone, text, lat, lon, session, flow):
    skipped = (text and text.upper() == "SKIP") or (not lat and not lon)

    # Intercept for guest users
    if session.get("epic") is None and session.get("post_flow_skipped") is None:
        session["temp_lat"] = lat
        session["temp_lon"] = lon
        session["temp_skipped"] = skipped
        session["temp_flow"] = flow
        session["state"] = "POST_FLOW_EPIC"
        msg = "Thank you for providing the details!\n\nTo officially link this request to your profile, please enter your Voter ID (EPIC number) below.\n\nIf you still don't have it, you can skip this step and we will generate the ticket anyway."
        send_button_message(phone, msg, [{"id": "skip_post_epic", "title": "⏭️ Skip"}], IMG_URLS["desc_banner"])
        return

    today = datetime.datetime.now().strftime("%d %b %Y")

    epic_to_save = session.get('epic') or session.get('epic_unverified')

    if flow == "FLOW1":
        ref_id = f"GRV{random.randint(10000, 99999)}"
        # Save to DB
        doc = {
            "ref_id": ref_id,
            "voter_phone": phone,
            "voter_name": session.get('name', 'Anonymous'),
            "booth": session.get('booth', 'Unknown'),
            "epic": epic_to_save,
            "category": session.get('cat', 'Others'),
            "description": session.get('desc', ''),
            "status": "Open",
            "timestamp": today,
            "type": "Grievance"
        }
        if not skipped:
            doc["location"] = {"lat": lat, "lon": lon}
        if session.get("photo_id"):
            doc["photo_id"] = session["photo_id"]
        await grievances_col.insert_one(doc)

        msg = f"✅ Issue Successfully Logged\n🔖 Reference ID: {ref_id}\n\nOur field team will visit this spot soon to verify and solve the issue.\n\nStatus: Open -> Ward Follow-up"
        send_image_message(phone, IMG_URLS["success"], msg)
        
        if not skipped:
            final_thanks = f"Thank you, *{session.get('name', 'Anonymous')}*. Your location has been recorded.\n\n🔖 Reference ID: {ref_id}\n\nOur field team will visit this spot soon to verify and solve the issue.\n\n*Our team will connect with you soon at your booth.*"
            send_image_message(phone, IMG_URLS["thank_you"], final_thanks)
        
    elif flow == "FLOW2":
        ref_id = f"SUG{random.randint(10000, 99999)}"
        # Save to member DB
        doc = {
            "ref_id": ref_id,
            "voter_phone": phone,
            "voter_name": session.get('name', 'Anonymous'),
            "booth": session.get('booth', 'Unknown'),
            "epic": epic_to_save,
            "suggestion": session.get('sugg', ''),
            "status": "Pending",
            "timestamp": today,
            "type": "Suggestion"
        }
        if not skipped:
            doc["location"] = {"lat": lat, "lon": lon}
        if session.get("photo_id"):
            doc["photo_id"] = session["photo_id"]
        await member_requests_col.insert_one(doc)

        if not skipped:
            msg = f"Thank you, *{session.get('name', 'Anonymous')}*. Your location has been recorded.\n\n🔖 Reference ID: {ref_id}\n\nOur team will review your suggestion for Kavundampalayam.\n\n*Our team will connect with you soon at your booth.*"
            send_image_message(phone, IMG_URLS["thank_you"], msg)
        else:
            msg = f"✅ Suggestion Officially Logged\n🔖 Reference ID: {ref_id}\n\nAll ideas are reviewed collectively to guide long-term planning for Kavundampalayam.\n\n*TVK Kavundampalayam Team*"
            send_image_message(phone, IMG_URLS["success"], msg)
            
    elif flow == "FLOW3":
        ref_id = f"VOL{random.randint(10000, 99999)}"
        doc = {
            "ref_id": ref_id,
            "voter_phone": phone,
            "voter_name": session.get('name', 'Anonymous'),
            "booth": session.get('booth', 'Unknown'),
            "epic": epic_to_save,
            "role": session.get('vol_role', 'General'),
            "status": "Registered",
            "timestamp": today,
            "type": "Volunteer"
        }
        if not skipped:
            doc["location"] = {"lat": lat, "lon": lon}
        if session.get("photo_id"):
            doc["photo_id"] = session["photo_id"]
        await member_requests_col.insert_one(doc)

        if not skipped:
            msg = f"Thank you, *{session.get('name', 'Anonymous')}*. Your location has been recorded.\n\n🔖 Reference ID: {ref_id}\n\nOur organiser from Booth {session.get('booth', 'Unknown')} will contact you with next steps.\n\n*Our team will connect with you soon at your booth.*"
            send_image_message(phone, IMG_URLS["thank_you"], msg)
        else:
            msg = f"✅ Volunteer Registration Complete\n🔖 Reference ID: {ref_id}\n\nThank you for stepping forward, {session.get('name', 'Anonymous')}. Our team will reach out to you soon.\n\n*TVK Kavundampalayam Team*"
            send_image_message(phone, IMG_URLS["success"], msg)
            
    elif flow == "FLOW4":
        if not skipped:
            msg = f"Thank you, *{session.get('name', 'Anonymous')}*. Your location has been recorded.\n\nYou will receive updates relevant to Booth {session.get('booth', 'Unknown')} and Kavundampalayam.\n\n*Our team will connect with you soon at your booth.*"
            send_image_message(phone, IMG_URLS["thank_you"], msg)
        else:
            msg = f"✅ Updates Subscribed\n\nYou will receive updates relevant to Booth {session.get('booth', 'Unknown')} and Kavundampalayam.\n\n*TVK Kavundampalayam Team*"
            send_image_message(phone, IMG_URLS["success"], msg)
            
    elif flow == "FLOW8":
        ref_id = f"PHT{random.randint(10000, 99999)}"
        doc = {
            "ref_id": ref_id,
            "voter_phone": phone,
            "voter_name": session.get('name', 'Anonymous'),
            "booth": session.get('booth', 'Unknown'),
            "epic": epic_to_save,
            "category": session.get('photo_cat', 'Others'),
            "description": session.get('photo_desc', ''),
            "status": "Open",
            "timestamp": today,
            "type": "Photo Evidence" # Treating photo evidenece like a grievance in DB
        }
        if not skipped:
            doc["location"] = {"lat": lat, "lon": lon}
        await grievances_col.insert_one(doc)

        if not skipped:
            msg = f"✅ Photo Evidence Submitted!\n\n───────────────\n🔖 Reference: {ref_id}\n📁 Category: {session.get('photo_cat', 'Others')}\n📝 Description: {session.get('photo_desc', '')}\n📸 Photo: Received\n📍 Location: Main Road, Kavundampalayam\n🏛️ Booth: {session['booth']}\n📅 Submitted: {today}\n───────────────\n\nOur field team will inspect the spot and take necessary action."
            send_image_message(phone, IMG_URLS["success"], msg)
        else:
            msg = f"✅ Photo Evidence Submitted!\n\n🔖 Reference: {ref_id}\n📁 Category: {session.get('photo_cat', 'Others')}\n📸 Photo: Received\n🏛️ Booth: {session['booth']}"
            send_image_message(phone, IMG_URLS["success"], msg)

    await send_loop_prompt(phone, session)


async def send_loop_prompt(phone, session):
    # Add a small delay to ensure the previous message arrives first and to create a natural pause
    await asyncio.sleep(2)
    
    # Rotate between showing Ward Connect, TVK Networks, and Invite
    choice = random.choice(["ward", "network", "invite"])
    
    if choice == "ward":
         booth = session.get('booth', 'Unknown')
         name = "Suresh Murugan"
         phone_num = "+919876543210"
         msg = f"📞 *Ward Connect — Booth {booth}*\n\nYour designated Ward Coordinator is available for support:\n\n👤 {name}\n📍 Gandhi Nagar, Kavundampalayam\n\nDirect Call: https://wa.me/{phone_num.replace('+', '')}"
         send_button_message(phone, msg, [{"id": "btn_main_menu", "title": "🏠 Main Menu"}], IMG_URLS["ward_connect"])
    elif choice == "network":
         msg = "🌐 *TVK Networks*\n\nExplore our digital initiatives:"
         send_button_message(phone, msg, [
            {"id": "btn_tvk_family", "title": "🌐 TVK Family"},
            {"id": "btn_tvk_itwing", "title": "💻 TVK IT Wing"}
        ], IMG_URLS["welcome_banner"])
    else:
         msg = "👥 *Join the Movement*\n\nHelp us build a stronger, more connected Kavundampalayam. Invite your friends and family to join Venkatraman's official WhatsApp platform!"
         send_button_message(phone, msg, [
             {"id": "btn_invite", "title": "👥 Invite a Voter"},
             {"id": "btn_main_menu", "title": "🏠 Main Menu"}
         ], IMG_URLS["invite_1"])
    
    session["state"] = "LOOP_PROMPT"

async def handle_flow9_networks(phone, text, session):
    sel = text.lower() if text else ""
    if "family" in sel or "btn_tvk_family" in sel:
        msg = "👨‍\u200d👩‍\u200d👧‍\u200d👦 *TVK Family*\n\nJoin our digital family and connect with fellow supporters across the globe!\n\nClick here to join 👉 https://tvk.family/"
        send_image_message(phone, IMG_URLS["welcome_banner"], msg)
        await send_loop_prompt(phone, session)
    elif "itwing" in sel or "btn_tvk_itwing" in sel:
        msg = "💻 *TVK IT Wing*\n\nBe part of the digital vanguard leading the change! Join the IT Wing today.\n\nClick here to explore 👉 https://tvkitwing.com/"
        send_image_message(phone, IMG_URLS["welcome_banner"], msg)
        await send_loop_prompt(phone, session)
    elif "invite" in sel or "btn_invite" in sel:
        send_image_message(phone, IMG_URLS["invite_1"], "👥 Spread the Word!\n\nHelp us build a stronger, more connected constituency. Forward the message below to your friends, family, and neighbours:")
        send_image_message(phone, IMG_URLS["invite_2"], """────────────────────\n🗳️ TVK Kavundampalayam — Voter Engagement Platform\n\nYour constituency. Your voice. Your future.\nJoin Venkatraman's official WhatsApp platform to:\n✅ Report local issues directly\n✅ Share ideas for development\n✅ Volunteer and participate\n✅ Get official campaign updates\n✅ Track your submitted issues\n\n👉 Send Hi to +91-XXXXXXXXXX on WhatsApp to get started.\n\nEvery voter's voice matters. Be heard.\nTVK — Kavundampalayam\n────────────────────""")
        send_image_message(phone, IMG_URLS["invite_3"], f"Your Referral Stats:\n\n👥 You have invited 3 voters so far.\n🏛️ Booth {session.get('booth', 'Unknown')} total participants: 47\n\nThank you for growing this movement, {session.get('name', 'Anonymous')}.")
        await send_loop_prompt(phone, session)
    else:
        send_button_message(phone, "Please select an option.", [
            {"id": "btn_tvk_family", "title": "🌐 TVK Family"},
            {"id": "btn_tvk_itwing", "title": "💻 TVK IT Wing"},
            {"id": "btn_main_menu", "title": "🏠 Main Menu"}
        ], None)

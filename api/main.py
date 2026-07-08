import os
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, Field
from supabase import create_client, Client
import requests

app = FastAPI(title="Vercel Caller ID & Telegram Bot API")

# ሰክሬቶች ከ Vercel Environment Variables
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")

if not SUPABASE_URL or not SUPABASE_KEY or not BOT_TOKEN:
    raise RuntimeError("የሚያስፈልጉ ሰክሬቶች በ Vercel ላይ አልተጫኑም!")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"

class NumberRegistration(BaseModel):
    phone_number: str = Field(..., example="+251911111111")
    name: str = Field(..., example="አበበ ካሳ")
    is_spam: bool = Field(default=False, example=False)

@app.get("/")
def read_root():
    return {"message": "Caller ID API እና ቴሌግራም ቦት በትክክል እየሰሩ ነው!"}

# 1. ቁጥር ማጽጃ ፋንክሽን
def clean_phone_number(phone_number: str) -> str:
    clean = phone_number.replace(" ", "")
    if clean.startswith("0"):
        clean = "+251" + clean[1:]
    return clean

# 2. ቁጥር መፈለጊያ (GET Route)
@app.get("/search/{phone_number}")
def search_number(phone_number: str):
    clean_number = clean_phone_number(phone_number)
    try:
        response = supabase.table("phone_directory").select("name", "is_spam").eq("phone_number", clean_number).execute()
        if response.data:
            return {"status": "found", "data": response.data[0]}
        return {"status": "not_found", "data": {"name": "ያልታወቀ ቁጥር (Unknown)", "is_spam": False}}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 3. አዲስ ቁጥር መመዝገቢያ (POST Route)
@app.post("/register")
def register_number(payload: NumberRegistration):
    clean_number = clean_phone_number(payload.phone_number)
    try:
        existing = supabase.table("phone_directory").select("id", "is_spam").eq("phone_number", clean_number).execute()
        if existing.data:
            if payload.is_spam:
                supabase.table("phone_directory").update({"is_spam": True}).eq("phone_number", clean_number).execute()
                return {"status": "updated", "message": "ቁጥሩ ስፓም ተብሏል።"}
            return {"status": "exists", "message": "ቁጥሩ ቀድሞ አለ።"}
        
        supabase.table("phone_directory").insert({"phone_number": clean_number, "name": payload.name, "is_spam": payload.is_spam}).execute()
        return {"status": "success", "message": "በትክክል ተመዝግቧል።"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 4. የቴሌግራም ቦት ዌብሁክ መቀበያ (Webhook Route)
@app.post("/webhook")
async def telegram_webhook(request: Request):
    try:
        update = await request.json()
        if "message" in update and "text" in update["message"]:
            chat_id = update["message"]["chat"]["id"]
            user_text = update["message"]["text"].strip()

            if user_text == "/start":
                msg = "እንኳን ወደ Caller ID ቦት በሰላም መጡ! 👋\n\nእባክዎ መፈለግ የሚፈልጉትን ስልክ ቁጥር ያስገቡ (ምሳሌ፡ 0911111111)።"
            else:
                # በቦት የመጣውን ቁጥር መፈለግ
                clean_num = clean_phone_number(user_text)
                res = supabase.table("phone_directory").select("name", "is_spam").eq("phone_number", clean_num).execute()
                
                if res.data:
                    name = res.data[0]["name"]
                    is_spam = "⚠️ አደገኛ ስፓም (Spam)!" if res.data[0]["is_spam"] else "✅ እውነተኛ ቁጥር"
                    msg = f"👤 ስም፦ {name}\nℹ️ ሁኔታ፦ {is_spam}"
                else:
                    msg = "🔍 ይቅርታ፣ ይህ ቁጥር በዳታቤዛችን ውስጥ አልተገኘም።"

            # መልሱን ለተጠቃሚው በቴሌግራም መላክ
            requests.post(f"{TELEGRAM_API}/sendMessage", json={"chat_id": chat_id, "text": msg})
            
    except Exception as e:
        print(f"Webhook Error: {e}")
    return {"status": "ok"}

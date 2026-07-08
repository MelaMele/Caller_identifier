import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from supabase import create_client, Client

app = FastAPI(title="Vercel Caller ID API")

# የ Supabase መገናኛዎች ከ Vercel Secrets
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError("የ Supabase ሰክሬቶች በ Vercel ላይ አልተጫኑም!")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# 1. አዲስ ቁጥር ሲመዘገብ የሚላከው ዳታ መዋቅር (Schema)
class NumberRegistration(BaseModel):
    phone_number: str = Field(..., example="+251911111111")
    name: str = Field(..., example="አበበ ካሳ")
    is_spam: bool = Field(default=False, example=False)

@app.get("/")
def read_root():
    return {"message": "እንኳን ወደ እውነተኛው እና አስተማማኙ Vercel Caller ID በሰላም መጡ!"}

# 2. ቁጥር መፈለጊያ (GET Route)
@app.get("/search/{phone_number}")
def search_number(phone_number: str):
    clean_number = phone_number.replace(" ", "")
    if clean_number.startswith("0"):
        clean_number = "+251" + clean_number[1:]

    try:
        response = supabase.table("phone_directory").select("name", "is_spam").eq("phone_number", clean_number).execute()
        
        if response.data:
            return {"status": "found", "data": response.data[0]}
        else:
            return {
                "status": "not_found",
                "data": {"name": "ያልታወቀ ቁጥር (Unknown)", "is_spam": False}
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database Error: {str(e)}")

# 3. አዲስ ቁጥር መመዝገቢያ እና ስፓም ሪፖርት ማድረጊያ (POST Route)
@app.post("/register")
def register_number(payload: NumberRegistration):
    # ቁጥሩን ማጽዳት
    clean_number = payload.phone_number.replace(" ", "")
    if clean_number.startswith("0"):
        clean_number = "+251" + clean_number[1:]
    try:
        # መጀመሪያ ቁጥሩ በዳታቤዙ ውስጥ መኖሩን ቼክ ማድረግ
        existing = supabase.table("phone_directory").select("id, is_spam").eq("phone_number", clean_number).execute()
        
        if existing.data:
            # ቁጥሩ ቀድሞ ካለ እና አሁን "Spam" ተብሎ ሪፖርት ከተደረገ፥ የድሮውን አዘምን (Update)
            if payload.is_spam:
                supabase.table("phone_directory").update({"is_spam": True}).eq("phone_number", clean_number).execute()
                return {"status": "updated", "message": "ቁጥሩ ስፓም (Spam) ተብሎ ተመዝግቧል።"}
            
            return {"status": "exists", "message": "ይህ ቁጥር ቀድሞውኑ ተመዝግቧል።"}
        
        # ቁጥሩ አዲስ ከሆነ አዲስ መስመር አስገባ (Insert)
        new_data = {
            "phone_number": clean_number,
            "name": payload.name,
            "is_spam": payload.is_spam
        }
        supabase.table("phone_directory").insert(new_data).execute()
        return {"status": "success", "message": "ቁጥሩ በትክክል ተመዝግቧል።"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database Error: {str(e)}")

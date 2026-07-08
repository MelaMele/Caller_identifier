import os
from fastapi import FastAPI, HTTPException
from supabase import create_client, Client

app = FastAPI(title="Vercel Caller ID API")

# Vercel ላይ ያስቀመጥካቸውን ሰክሬቶች በ os.environ በኩል መሳብ
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

# ሰክሬቶቹ በትክክል መኖራቸውን ማረጋገጫ (ካጡ Error ለመስጠት)
if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError("የ Supabase ሰክሬቶች በ Vercel ላይ አልተጫኑም!")

# የ Supabase ክላየንት መፍጠር
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

@app.get("/")
def read_root():
    return {"message": "እንኳን ወደ እውነተኛው እና አስተማማኙ Vercel Caller ID በሰላም መጡ!"}

@app.get("/search/{phone_number}")
def search_number(phone_number: str):
    clean_number = phone_number.replace(" ", "")
    
    if clean_number.startswith("0"):
        clean_number = "+251" + clean_number[1:]

    try:
        response = supabase.table("phone_directory").select("name", "is_spam").eq("phone_number", clean_number).execute()
        
        if response.data:
            return {
                "status": "found",
                "data": response.data[0]
            }
        else:
            return {
                "status": "not_found",
                "data": {"name": "ያልታወቀ ቁጥር (Unknown)", "is_spam": False}
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database Error: {str(e)}")

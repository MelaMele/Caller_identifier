from fastapi import FastAPI

app = FastAPI(title="Vercel Caller ID API")

# ለአሁኑ መረጃውን በዲክሽነሪ (In-Memory) እናስቀምጠው
# በኋላ ላይ ከኦንላይን ዳታቤዝ (ለምሳሌ MongoDB Atlas ወይም Supabase) ጋር እናገናኘዋለን
MOCK_DB = {
    "+251911111111": {"name": "አቤል በቀለ", "is_spam": False},
    "+251922222222": {"name": "አዋሽ ባንክ (ካዛንቺስ)", "is_spam": False},
    "+251933333333": {"name": "የማጭበርበር ጥሪ (Spam)", "is_spam": True}
}

@app.get("/")
def read_root():
    return {"message": "እንኳን ወደ Vercel Caller ID በሰላም መጡ!"}

@app.get("/search/{phone_number}")
def search_number(phone_number: str):
    if phone_number in MOCK_DB:
        return {
            "status": "found",
            "data": MOCK_DB[phone_number]
        }
    else:
        return {
            "status": "not_found",
            "data": {"name": "ያልታወቀ ቁጥር (Unknown)", "is_spam": False}
        }

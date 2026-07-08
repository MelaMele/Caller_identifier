from fastapi import FastAPI

app = FastAPI(title="Vercel Caller ID API")

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
    # ክፍተቶችን (Spaces) ማጽጃ (ለምሳሌ፡ "+251 911 11 1111" ወደ "+251911111111")
    clean_number = phone_number.replace(" ", "")
    
    # ተጠቃሚው በ 09 የጀመረውን ወደ +251 መቀየር ቢፈልግ (ተጨማሪ ማሻሻያ)
    if clean_number.startswith("0"):
        clean_number = "+251" + clean_number[1:]

    if clean_number in MOCK_DB:
        return {
            "status": "found",
            "data": MOCK_DB[clean_number]
        }
    else:
        return {
            "status": "not_found",
            "data": {"name": "ያልታወቀ ቁጥር (Unknown)", "is_spam": False}
        }

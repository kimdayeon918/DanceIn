from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import json
import yt_dlp
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class RecommendRequest(BaseModel):
    genre: str
    mood: str
    duration: str

def load_songs():
    with open("songs.json", "r", encoding="utf-8") as f:
        return json.load(f)

@app.post("/recommend")
def recommend_music(req: RecommendRequest):
    songs = load_songs()
    
    result = [s for s in songs if s["genre"] == req.genre]
    
    if req.mood:
        mood_filtered = [s for s in result if req.mood in s["mood"]]
        if mood_filtered:
            result = mood_filtered
    
    if not result:
        result = [s for s in songs if s["genre"] == req.genre]
    
    return {"result": result[:5]}

SCHOOL_CHANNELS = {
    "선화예술고등학교": "https://www.youtube.com/@%EC%84%A0%ED%99%94%EC%98%88%EC%88%A0%EA%B3%A0%EB%93%B1%ED%95%99%EA%B5%90",
    "국립전통예술고등학교": "https://www.youtube.com/@jeontongyego",
    "브니엘예술고등학교": "https://www.youtube.com/@%EB%B8%8C%EB%8B%88%EC%97%98%EC%98%88%EC%88%A0%EA%B3%A0%EB%93%B1%ED%95%99%EA%B5%90",
}

@app.get("/videos")
def get_recent_videos():
    results = []
    
    for school, url in SCHOOL_CHANNELS.items():
        try:
            ydl_opts = {
                "quiet": True,
                "extract_flat": True,
                "playlistend": 5,
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                videos = info.get("entries", [])
                for v in videos:
                    results.append({
                        "school": school,
                        "title": v.get("title"),
                        "url": f"https://www.youtube.com/watch?v={v.get('id')}",
                        "date": v.get("upload_date"),
                    })
        except Exception as e:
            results.append({"school": school, "error": str(e)})
    
    return {"videos": results}

@app.get("/contests")
def get_contests():
    try:
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        
        driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=options
        )
        
        driver.get("https://www.concourslink.kr/contest")
        time.sleep(6)
        
        soup = BeautifulSoup(driver.page_source, "html.parser")
        driver.quit()
        
        results = []
        
        # 제목 찾기
        titles = soup.find_all("p", class_="tit")
        tags = soup.find_all("span", class_="tag red")
        
        for tag in tags:
            parent = tag.find_parent()
            while parent:
                tit = parent.find("p", class_="tit")
                if tit:
                    results.append({
                        "title": tit.text.strip(),
                        "status": "접수중",
                        "url": "https://www.concourslink.kr/contest"
                    })
                    break
                parent = parent.find_parent()
        
        return {"contests": results}
    except Exception as e:
        return {"error": str(e)}

@app.get("/")
def root():
    return {"message": "DanceIn API 작동중!"}
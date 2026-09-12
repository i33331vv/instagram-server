from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from instagrapi import Client
import os

app = FastAPI()

class LoginRequest(BaseModel):
    username: str
    password: str

class FollowRequest(BaseModel):
    sessionid: str
    target_username: str

@app.post("/api/login")
def instagram_login(data: LoginRequest):
    client = Client()
    
    # تحديد إعدادات وبصمة جهاز وهمية لتجنب خطأ الإصدار القديم من انستغرام
    settings_file = f"session_{data.username}.json"
    
    try:
        # تعيين بصمة جهاز أندرويد مستقرة
        client.set_device({
            "app_version": "269.0.0.18.75",
            "android_version": 26,
            "android_release": "8.0.0",
            "nodpi": "480dpi",
            "resolution": "1080x1920",
            "manufacturer": "OnePlus",
            "device": "oneplus5",
            "model": "ONEPLUS A5000",
            "cpu": "qcom",
            "version_code": "314618774"
        })

        # محاولة تحميل إعدادات سابقة إن وجدت
        if os.path.exists(settings_file):
            client.load_settings(settings_file)

        client.login(data.username, data.password)
        
        # حفظ الإعدادات والجلسة للمستقبل
        client.dump_settings(settings_file)
        
        session_id = client.get_settings().get("authorization_data", {}).get("sessionid", "")
        if not session_id:
            session_id = client.sessionid
            
        return {"status": "success", "sessionid": session_id}
        
    except Exception as e:
        print(f"LOGIN ERROR: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/follow")
def instagram_follow(data: FollowRequest):
    client = Client()
    try:
        client.login_by_sessionid(data.sessionid)
        target_user_id = client.user_id_by_username(data.target_username)
        client.user_follow(target_user_id)
        return {"status": "success", "message": "تمت المتابعة بنجاح"}
    except Exception as e:
        print(f"FOLLOW ERROR DETAILS: {str(e)}")
        raise HTTPException(status_code=400, detail=f"فشل تنفيذ المتابعة: {str(e)}")

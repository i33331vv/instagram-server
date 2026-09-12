from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from instagrapi import Client

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
    try:
        client.login(data.username, data.password)
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
        client.set_sessionid(data.sessionid)
        target_user_id = client.user_id_by_username(data.target_username)
        client.user_follow(target_user_id)
        return {"status": "success", "message": "تمت المتابعة بنجاح"}
    except Exception as e:
        # طباعة الخطأ بوضوح في سجلات Render لسهولة التتبع
        print(f"FOLLOW ERROR DETAILS: {str(e)}")
        raise HTTPException(status_code=400, detail=f"فشل تنفيذ المتابعة: {str(e)}")

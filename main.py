from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from instagrapi import Client

app = FastAPI()

class SessionRequest(BaseModel):
    sessionid: str
    username: str

class FollowRequest(BaseModel):
    sessionid: str
    target_username: str

@app.post("/api/validate_session")
def validate_session(data: SessionRequest):
    cl = Client()
    try:
        cl.set_user_agent("Instagram 269.0.0.18.75 Android (32/12; 480dpi; 1080x2340; Samsung; SM-S908E; gts8ultra; en_US)")
        cl.login_by_sessionid(data.sessionid)
        # التأكد من أن صاحب الجلسة هو نفس اسم المستخدم المدخل
        account_info = cl.account_info()
        if account_info.username.lower() == data.username.lower():
            return {"status": "success"}
        else:
            raise HTTPException(status_code=400, detail="اسم المستخدم لا يتطابق مع الجلسة")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"جلسة غير صالحة: {str(e)}")

@app.post("/api/follow")
def follow_user(data: FollowRequest):
    cl = Client()
    try:
        cl.set_user_agent("Instagram 269.0.0.18.75 Android (32/12; 480dpi; 1080x2340; Samsung; SM-S908E; gts8ultra; en_US)")
        cl.login_by_sessionid(data.sessionid)
        user_id = cl.user_id_from_username(data.target_username)
        cl.user_follow(user_id)
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"فشلت المتابعة: {str(e)}")

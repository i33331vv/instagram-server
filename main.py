from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from instagrapi import Client
from instagrapi.exceptions import ChallengeRequired, TwoFactorRequired

app = FastAPI()

# تخزين مؤقت للعملاء الذين يحتاجون إلى تحقق أمني
pending_clients = {}

class LoginRequest(BaseModel):
    username: str
    password: str

class VerifyRequest(BaseModel):
    username: str
    code: str

class FollowRequest(BaseModel):
    sessionid: str
    target_username: str

@app.post("/api/login")
def login_instagram(data: LoginRequest):
    cl = Client()
    try:
        cl.set_user_agent("Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148")
        cl.login(data.username, data.password)
        
        cookies = cl.get_cookies()
        sessionid = cookies.get("sessionid")
        return {"status": "success", "sessionid": sessionid}
        
    except ChallengeRequired:
        pending_clients[data.username] = cl
        return {"status": "challenge_required", "message": "يرجى إدخال رمز التحقق أو الموافقة من تطبيق انستغرام الخاص بك."}
        
    except TwoFactorRequired:
        pending_clients[data.username] = cl
        return {"status": "two_factor_required", "message": "أدخل رمز التحقق الثنائي (2FA) المرسل لهاتفك أو بريدك."}
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/verify_challenge")
def verify_challenge(data: VerifyRequest):
    cl = pending_clients.get(data.username)
    if not cl:
        raise HTTPException(status_code=400, detail="انتهت صلاحية الجلسة، حاول تسجيل الدخول مجدداً.")
    
    try:
        # محاولة إدخال الرمز وإتمام التحقق
        cl.challenge_code_handler = lambda username: data.code
        cookies = cl.get_cookies()
        sessionid = cookies.get("sessionid")
        
        if not sessionid:
            sessionid = cl.get_setting("authorization")
            
        return {"status": "success", "sessionid": sessionid}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"رمز التحقق غير صحيح: {str(e)}")

@app.post("/api/follow")
def follow_user(data: FollowRequest):
    cl = Client()
    try:
        cl.login_by_sessionid(data.sessionid)
        user_id = cl.user_id_from_username(data.target_username)
        cl.user_follow(user_id)
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

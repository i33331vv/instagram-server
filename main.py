from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from instagrapi import Client
from instagrapi.exceptions import ChallengeRequired, TwoFactorRequired, BadPassword

app = FastAPI()

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
        # محاكاة هاتف آيفون رسمي لتفادي حظر السيرفرات السحابية
        cl.set_user_agent("Instagram 269.0.0.18.75 Android (32/12; 480dpi; 1080x2340; Samsung; SM-S908E; gts8ultra; en_US)")
        
        # محاولة تسجيل الدخول
        cl.login(data.username, data.password)
        
        cookies = cl.get_cookies()
        sessionid = cookies.get("sessionid")
        if not sessionid:
            sessionid = cl.get_setting("authorization")
            
        return {"status": "success", "sessionid": sessionid}
        
    except ChallengeRequired:
        pending_clients[data.username] = cl
        return {"status": "challenge_required", "message": "يطلب إنستغرام تأكيداً أمنياً. يرجى إدخال رمز التحقق."}
        
    except TwoFactorRequired:
        pending_clients[data.username] = cl
        return {"status": "two_factor_required", "message": "الحساب محمي بالتحقق الثنائي (2FA). أدخل الرمز."}
        
    except BadPassword:
        raise HTTPException(status_code=400, detail="كلمة المرور غير صحيحة.")
        
    except Exception as e:
        error_msg = str(e)
        if "feedback_required" in error_msg:
            raise HTTPException(status_code=400, detail="حسابك مقيد مؤقتاً من إنستغرام. جرب حساباً آخر.")
        raise HTTPException(status_code=400, detail=f"خطأ إنستغرام: {error_msg}")

@app.post("/api/verify_challenge")
def verify_challenge(data: VerifyRequest):
    cl = pending_clients.get(data.username)
    if not cl:
        raise HTTPException(status_code=400, detail="انتهت صلاحية الجلسة، حاول مجدداً.")
    
    try:
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
        cl.user_user_follow(user_id) # أو user_follow بحسب إصدار المكتبة
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

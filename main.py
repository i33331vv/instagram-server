import time
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from instagrapi import Client
from instagrapi.exceptions import ChallengeRequired, TwoFactorRequired, BadPassword

app = FastAPI()

class LoginRequest(BaseModel):
    username: str
    password: str

class FollowRequest(BaseModel):
    sessionid: str
    target_username: str

@app.post("/api/login")
def login_instagram(data: LoginRequest):
    cl = Client()
    try:
        # محاكاة جهاز حقيقي لتجنب الحظر السحابي
        cl.set_user_agent("Instagram 269.0.0.18.75 Android (32/12; 480dpi; 1080x2340; Samsung; SM-S908E; gts8ultra; en_US)")
        
        # محاولة تسجيل الدخول (هنا سيرسل انستغرام إشعار الموافقة لهاتفك)
        cl.login(data.username, data.password)
        
        cookies = cl.get_cookies()
        sessionid = cookies.get("sessionid")
        if not sessionid:
            sessionid = cl.get_setting("authorization")
            
        return {"status": "success", "sessionid": sessionid}
        
    except ChallengeRequired:
        # إذا طلب إنستغرام موافقة (This was me) أو تحدي أمني
        # سنقوم بانتظار استجابة المستخدم لمدة محدودة (مثلاً 30 ثانية) ريثما يضغط على "موافق" في هاتفه
        start_time = time.time()
        while time.time() - start_time < 35:
            try:
                # محاولة إعادة جلسة التحقق بعد ضغط المستخدم على "موافق" في هاتفه
                cl.challenge_resolve(cl.challenge_settings)
                cookies = cl.get_cookies()
                sessionid = cookies.get("sessionid")
                if sessionid:
                    return {"status": "success", "sessionid": sessionid}
            except Exception:
                pass
            time.sleep(3) # فحص كل 3 ثوانٍ هل وافقت من هاتفك أم لا
            
        raise HTTPException(status_code=400, detail="انتهى الوقت. لم تقم بتأكيد الموافقة من هاتفك، حاول مجدداً.")
        
    except TwoFactorRequired:
        raise HTTPException(status_code=400, detail="الحساب محمي بالتحقق الثنائي (2FA).")
        
    except BadPassword:
        raise HTTPException(status_code=400, detail="كلمة المرور غير صحيحة.")
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"خطأ: {str(e)}")

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

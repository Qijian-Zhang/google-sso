"""Google Login Example
"""

import os
import uvicorn
from fastapi import FastAPI, Request, Depends, HTTPException, status

from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi_sso.sso.google import GoogleSSO
import json
from starlette.middleware.sessions import SessionMiddleware

from fastapi.staticfiles import StaticFiles

from data_service import MySQLDataService

#import env

app = FastAPI()
my_sql_data_service = MySQLDataService()


os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
CLIENT_ID = "566480876817-3oom0reuo525tefvpsr6otpmg7fc8pjb.apps.googleusercontent.com"
CLIENT_SECRET = "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"
OAUTH_URL = "http://18.234.195.74.nip.io:5001"

app.mount("/static", StaticFiles(directory="static"), name="static")

sso = GoogleSSO(
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    redirect_uri=OAUTH_URL + "/auth/callback",
    allow_insecure_http=True,
)
callback=['http://localhost:3000/Dashboard','http://localhost:3000/customerhome','http://localhost:3000/storage']
usertypes=[]

# Secret key for signing the session cookie
SECRET_KEY = "mysecretkey"

# Middleware to enable sessions
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)

@app.get("/ping", response_class=HTMLResponse)
def ping():
    """

    :return:
    """

    rsp = """
     <!DOCTYPE html>
            <html>
            <head>
                <title>User Info</title>
            </head>
            <body>
               Pong.
            </body>
            </html>
    """
    return rsp

@app.get("/", response_class=HTMLResponse)
async def home_page(request: Request):
    print("Current directory = " + os.getcwd())
    print("Files = " + str(os.listdir("./")))
    user_type = request.query_params.get("user_type", "unknown")

    request.session['usertype'] = user_type
    result = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Google Login</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                text-align: center;
                margin-top: 100px;
            }
            .container {
                width: 300px;
                margin: 0 auto;
                padding: 20px;
                border: 1px solid #ccc;
                border-radius: 5px;
                background-color: #f9f9f9;
            }
            .logo {
                margin-bottom: 20px;
            }
            .button {
                display: inline-block;
                padding: 10px 20px;
                background-color: #4285f4;
                color: white;
                border: none;
                border-radius: 5px;
                cursor: pointer;
            }
        </style>
    </head>
    <body>
        <div class="container">
        
        <form action="{OAUTH_URL}/auth/login">
            
            <h2>Sign in with your Google Account</h2>
            <button type="submit" class="button">Login with Google</button>
            </form>
        </div>
    </body>
    </html>
    """

    result = result.replace("{OAUTH_URL}", OAUTH_URL)
    return result

@app.get("/auth/login")
async def auth_init():
    """Initialize auth and redirect"""
    with sso:
        return await sso.get_login_redirect(params={"prompt": "consent", "access_type": "offline"})


@app.get("/auth/callback", response_class=HTMLResponse)
async def auth_callback(request: Request):
    """Verify login"""
    print("Request = ", request)
    print("URL = ", request.url)

    try:
        with sso:
            user = await sso.verify_and_process(request)
            data = user
            usertype = request.session.get('usertype', -1)

            #student = my_sql_data_service.get_student_info(user.email)
            #print("Student = \n", json.dumps(student, indent=2, default=str))
            #coupon = student.get("student_coupon_code", None)
            #coupon_value = student.get("Value", None)

            # if user.email == "dff9@columbia.edu":
            #    raise Exception("Not cool dude.")

            html_content = f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <title>User Info</title>
                </head>
                <body>
                    <h1>User Information</h1>
                    <img src="{user.picture}" alt="User Picture" width="96" height="96"><br>
                    <p><b>ID:</b> {user.id}</p>
                    <p>Email: {user.email}</p>
                    <p>First Name: {user.first_name}</p>
                    <p>Last Name: {user.last_name}</p>
                    <p>Display Name: {user.display_name}</p>
                    <p>Identity Provider: {user.provider}</p>
                    <a href='http://6156ruoxing.s3-website-us-east-1.amazonaws.com/mid?auth={usertype}&email={user.email}' >Continue to home page</a>
                </body>
                </html>
                """

            return HTMLResponse(content=html_content)
    except Exception as e:
        print("Exception e = ", e)
        return RedirectResponse("/static/error.html")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5001)

from flask import Flask,request
from google.cloud import storage
import pandas as pd
import json
import io
import os
import datetime as dt
import pytz

tz = pytz.timezone('Asia/Bangkok')

PATH = os.path.join(os.getcwd() , '###.json')
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = PATH
storage_client = storage.Client(PATH)

bucket = storage_client.get_bucket('fitsi_bucket') # read all file in bucket

app = Flask(__name__)

# history filter by user
def history_data_user(body):
    df_history = pd.read_csv(
    io.BytesIO(
                 bucket.blob(blob_name = 'historyData.csv').download_as_string() 
              ) ,
                 encoding='UTF-8',
                 sep=',')
    user = body["username"]
    rslt_df = df_history[df_history['username'] == user]
    return rslt_df

# history function to calculate time spent
def datetime_diff(time_start,end_ts):
    start_ts = pd.Timestamp(time_start)
    end_ts = pd.Timestamp(end_ts)
    return round(pd.Timedelta(end_ts - start_ts).seconds / 60.0, 2)

# history save all log
def history_data_log(body):
    df_history = pd.read_csv(
    io.BytesIO(
                 bucket.blob(blob_name = 'historyData.csv').download_as_string() 
              ) ,
                 encoding='UTF-8',
                 sep=',')

    time_spent = datetime_diff(str(body["time_start"]),str(body["time_end"]))
    
    if body["result_of_grading"] == "Excelent Pose Exercise":
        res_of_grading = "excellent"
    elif body["result_of_grading"] == "Good Pose Exercise":
        res_of_grading = "good"
    elif body["result_of_grading"] == "Fair Pose Exercise":
        res_of_grading = "fair" 
    else:
        res_of_grading = "error" 
    
    df_body = {
        "TimeStamp":pd.Timestamp(dt.datetime.now(tz)),
        "username":body["username"],
        "posture_id":body["posture_id"], # 0-9 define index_style what count time maybe 1-2 posture?
        "counting_time":body["counting_time"],
        "result_of_grading":res_of_grading,
        "time_spent":time_spent,
        "time_start":body["time_start"],
        "time_end":body["time_end"]
        }

    df_history = pd.concat([df_history, pd.DataFrame.from_records([df_body])])

    filename= 'historyData.csv'
    bucket.blob(filename).upload_from_string(df_history.to_csv(index=False,encoding = "utf-8"), 'text/csv')

    return {"Message":"History save","values":1}

# save log function
def save_log(method,username,status):
    df_log = pd.read_csv(
    io.BytesIO(
                 bucket.blob(blob_name = 'log.csv').download_as_string() 
              ) ,
                 encoding='UTF-8',
                 sep=',',dtype={"TimeStamp": str,"Method":str,"username":str,"status":int})
    # prepare data into data frame
    df_body = {
    "TimeStamp":pd.Timestamp(dt.datetime.now(tz)),
    "username":username,
    "Method":method,
    "status":status
    }

    df_log = pd.concat([df_log, pd.DataFrame.from_records([df_body])])
    filename= 'log.csv'
    bucket.blob(filename).upload_from_string(df_log.to_csv(index=False,encoding = "utf-8"), 'text/csv')
    return 0

# signin function
def signin(body):

    df = pd.read_csv(
    io.BytesIO(
                 bucket.blob(blob_name = 'database_login.csv').download_as_string() 
              ) ,
                 encoding='UTF-8',
                 sep=',',dtype={"phoneNumber": str,"password":str,"confirmPassword":str})

    user = body["username"]
    pass_word = body["password"]
    if not df[((df.username == str(user)) | (df.email == str(user))) & (df.password == str(pass_word))].empty:
        save_log("signin",str(user),1)
        return {"Message":"login success","values":1}
    else:
        save_log("signin",str(user),0)
        return {"Message":"login not success","values":0}

# signup function
def signup(body):

    df = pd.read_csv(
    io.BytesIO(
                 bucket.blob(blob_name = 'database_login.csv').download_as_string() 
              ) ,
                 encoding='UTF-8',
                 sep=',',dtype={"phoneNumber": str,"password":str,"confirmPassword":str})
    try:
        try:
            id_no = int(df["ID_no"].iloc[-1])
            id_no+=1
        except:
            id_no = 0

        # prepare data into data frame
        df_body = {
        "TimeStamp":pd.Timestamp(dt.datetime.now(tz)),
        "ID_no":id_no,
        "fullname":body["fullname"],
        "lastname":body["lastname"],
        "email":body["email"],
        "gender":body["gender"],
        "phoneNumber":body["phoneNumber"],
        "username":body["username"],
        "password":body["password"],
        "confirmPassword":body["confirmPassword"]
        }
        
        user = body["username"]
        email = body["email"]

        if df[(df.username == str(user)) | (df.email == str(email))].empty:
            df = pd.concat([df, pd.DataFrame.from_records([df_body])])
            filename= 'database_login.csv'
            bucket.blob(filename).upload_from_string(df.to_csv(index=False,encoding = "utf-8"), 'text/csv')
            save_log("signup",str(user),1)
            return {"Message":"sign-up success","values":1}
        else:
            save_log("signup",str(user),2)
            return {"Message":"sign-up not success your have old user or email","values":2}

    except:
        save_log("signup",str(user),0)
        return {"Message":"sign-up not success","values":0}

# history system / only user login
@app.route('/history/user',methods=['POST'])
def History_Data_call():
    if request.method == 'POST':
        body = request.get_json()
        df = history_data_user(body)

        result = df.to_json(orient="records")
        parsed = json.loads(result)

        return parsed
    return 0

# history system
@app.route('/history',methods=['POST','GET'])
def History_Data():
    if request.method == 'POST':
        body = request.get_json()
        status = history_data_log(body)
        return status

    elif request.method == 'GET':
        df = pd.read_csv(
                io.BytesIO(
                 bucket.blob(blob_name = 'historyData.csv').download_as_string() 
              ) ,
                 encoding='UTF-8',
                 sep=',')
        # result = df.to_json(orient="split")
        result = df.to_json(orient="records")
        parsed = json.loads(result)

        return parsed

    return {"Message":"Hello!!"},201

# login system signin
@app.route('/login/signin',methods=['POST','GET']) # login no register
def Login_Signin_Method():
    if request.method == 'POST':

        body = request.get_json()
        status_in = signin(body)
        return status_in

    return {"Message":"Hello!!"},201

# login system signup
@app.route('/login/signup',methods=['POST','GET']) # register
def Login_Signup_Method():
    if request.method == 'POST':

        body = request.get_json()
        status_up = signup(body)
        return status_up

    return {"Message":"Hello!!"},201

# login system log
@app.route('/admin/log',methods=['GET']) # get admin check row
def get_admin_log():
    if request.method == 'GET':
        df = pd.read_csv(
                io.BytesIO(
                 bucket.blob(blob_name = 'log.csv').download_as_string() 
              ) ,
                 encoding='UTF-8',
                 sep=',',dtype={"TimeStamp": str,"Method":str,"username":str,"status":int})
        # df.to_csv('database//log.csv')
        result = df.to_json(orient="split")
        parsed = json.loads(result)
        return parsed

    return {"Message":"Hello!!"},201

# login system ad,in check all user in data base
@app.route('/admin',methods=['GET']) # get admin check row database
def get_admin():
    if request.method == 'GET':
        df = pd.read_csv(
                io.BytesIO(
                 bucket.blob(blob_name = 'database_login.csv').download_as_string() 
              ) ,
                 encoding='UTF-8',
                 sep=',',dtype={"phoneNumber": str,"password":str,"confirmPassword":str})
        # df.to_csv('database//database_login.csv')
        result = df.to_json(orient="split")
        parsed = json.loads(result)
        return parsed

    return {"Message":"Hello!!"},201

@app.route('/')
def test():
    """Return a simple HTML page with a friendly message."""
    return {"Message":"Hello!!"},201

if __name__ == "main":
    app.run()
import auth
from config import Config
import requests
from flask import Flask, redirect, request, jsonify, render_template

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def sign_in():
    if request.method == 'POST':
        try:
            username = request.form.get('username')
            password = request.form.get('password')
            token = auth.sign_in(username, password)
            print("adding token to app config in sign in")
            print(token)
            app.config["jwt_token"] = token
            print("adding token to app config in sign in done done")
            return render_template('home.html')
        except Exception as e:
            print(f"Exception: {e}")
        # r=requests.get("https://w4nume50g8.execute-api.us-east-1.amazonaws.com/sample/pets", headers={"Authorization":f"Bearer {token}"})
        # print(r.json())
            return render_template('login.html', error=True)
    
    return render_template('login.html')
    # return redirect(aws_auth.get_sign_in_url())

@app.route('/home', methods=['POST'])
def home():
    print("inside home")
    return render_template('home.html')


if __name__ == '__main__':
    app.run(debug=True)

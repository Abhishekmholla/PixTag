import boto3
import auth
from config import Endpoints, Config
import helper
import requests
import logging
from flask import Flask, redirect, request, jsonify, render_template, url_for
from io import BytesIO
from base64 import b64encode

app = Flask(__name__)

logging.basicConfig(level = logging.INFO)
log = logging.getLogger(__name__)

@app.route('/', methods=['GET', 'POST'])
def sign_in():
    """
    API to sign in to PixTag
    """

    if request.method == 'POST':
        try:
            username = request.form.get('username')
            password = request.form.get('password')
            token = auth.sign_in(username, password)
            log.info("Adding token to app config on successful sign-in")
            app.config["jwt_token"] = token
            return redirect(url_for('home'))
        except Exception as e:
            log.error(f"Exception: {e}")
            return render_template('login.html', error = True)
    
    return render_template('login.html')

@app.route('/pixtag', methods=['GET'])
def home():
    """
    Landing page API for PixTag
    """

    return render_template("home.html", error = False)

@app.route('/search-by-tags', methods=["POST"])
def search_by_tags():
    
    s3_image_keys = list()
    decoded_images = list()

    if request.method == 'POST':
        
        try:
    
            tags = request.form.get('tags')
            
            if tags.strip() == "":
                return render_template("home.html", error = True, error_message = "Tags can not be empty.")
            
            tags_list = [tag.strip() for tag in tags.split(";")]
            log.info(f"List of tags to query on: {tags_list}")

            # Get image links for given tags
            request_body = {"tags": tags_list}
            tags_response = requests.post(Endpoints.SEARCH_BY_TAGS.value, 
                                    json = request_body,
                                    headers = helper.format_header(app.config['jwt_token']))
            tags_response = helper.get_response_dict(tags_response)
            
            if "links" not in tags_response:
                return render_template("home.html", error = True, error_message = "No images found for given tags.")

            for link in tags_response["links"]:
                s3_image_keys.append(link.split(f"s3://{Config.S3_BUCKET_NAME.value}/")[1])

            
            # Get image base64 encoded strings for all images
            image_request_body = {
                "bucket_name": Config.S3_BUCKET_NAME.value,
                "keys": s3_image_keys
            }            
            images_response = requests.post(Endpoints.ENCODE_IMAGE.value, 
                                    json = image_request_body,
                                    headers = helper.format_header(app.config['jwt_token']))
            images_response = helper.get_response_dict(images_response)
            
            for image in images_response["images"]:
                decoded_images.append(image.decode('ascii'))

            return render_template(
                "home.html", 
                error = False,
                mimetype = 'image/jpeg',
                images = decoded_images, 
            )
        
        except Exception as e:
            log.error(f"Exception: {e}")
            return render_template("home.html", error = True, error_message = e)
    
    return render_template("home.html", error = False)

@app.route('/search-by-thumbnail', methods=["POST"])
def search_by_thumbnail():
    
    s3_image_keys = list()
    decoded_images = list()

    if request.method == 'POST':
        
        try:
    
            print("TODO")
        
        except Exception as e:
            log.error(f"Exception: {e}")
            return render_template("home.html", error = True, error_message = e)
    
    return render_template("home.html", error = False)

@app.route('/search-by-image', methods=["POST"])
def search_by_image():

    if request.method == 'POST':
        
        try:
    
            print("TODO")
        
        except Exception as e:
            log.error(f"Exception: {e}")
            return render_template("home.html", error = True, error_message = e)
    
    return render_template("home.html", error = False)

@app.route('/add-delete-tags', methods=["POST"])
def add_delete_tags():

    if request.method == 'POST':
        
        try:
    
            print("TODO")
        
        except Exception as e:
            log.error(f"Exception: {e}")
            return render_template("home.html", error = True, error_message = e)
    
    return render_template("home.html", error = False)

@app.route('/delete-image', methods=["POST"])
def delete_images():

    if request.method == 'POST':
        
        try:
    
            print("TODO")
        
        except Exception as e:
            log.error(f"Exception: {e}")
            return render_template("home.html", error = True, error_message = e)
    
    return render_template("home.html", error = False)

if __name__ == '__main__':
    app.run(debug = True)

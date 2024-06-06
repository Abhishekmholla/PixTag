import re
import auth
import base64
import helper
import logging
import requests
from config import Endpoints, Config
from flask import Flask, redirect, request, render_template, url_for

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

@app.route('/upload-image', methods=["POST"])
def upload_image():
    
    if request.method == 'POST':
        
        try:
    
            image = request.files['image']
            if image.filename == "":
                return render_template("home.html", error = True, error_message = "No image is uploaded.")

            log.info("Encoding image to base64 string")            
            image_string = base64.b64encode(image.read())

            # Invoking upload image API
            request_body = {
                "image": image_string.decode()
            }
            upload_response = requests.post(Endpoints.UPLOAD_IMAGE.value, 
                                    json = request_body,
                                    headers = helper.format_header(app.config['jwt_token']))
            upload_response = helper.get_response_dict(upload_response)
        
            return render_template(
                "home.html", 
                error = False,
                mimetype = 'image/jpeg',
                u_image = image_string.decode(), 
                upload_image = True
            )
        
        except Exception as e:
            log.error(f"Error during image upload. Please check logs. Exception{e}")
            return render_template("home.html", error = True, error_message = e)
    
    return render_template("home.html", error = False)

@app.route('/search-by-tags', methods=["POST"])
def search_by_tags():
    
    s3_image_keys = list()
    decoded_images = list()

    if request.method == 'POST':
        
        try:
        
            tags = request.form.get('tags')
            
                # if not re.search(r'[^\w\s;]', tags) is None:
                #     return render_template("home.html", error = True, error_message = "Tags need to be seperated by ; colon only")
                
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
                s3_image_keys.append(link.split(f"https://{Config.S3_BUCKET_NAME.value}.s3.amazonaws.com/")[1])

            
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
                search_by_tag = True,
                tags = tags
            )
        
        except Exception as e:
            log.error(f"Exception: {e}")
            return render_template("home.html", error = True, error_message = e)
    
    return render_template("home.html", error = False)

@app.route('/search-by-thumbnail', methods=["POST"])
def search_by_thumbnail():

    if request.method == 'POST':
        
        try:
    
            thumbnail_url = request.form.get('thumbnail_url')
            
            if thumbnail_url.strip() == "":
                return render_template("home.html", error = True, error_message = "Thumbnail URL can not be empty.")
            
            log.info(f"Thumbnail URL to query on: {thumbnail_url}")

            # Get image links for given thumbnail url
            request_body = {"thumbnail_url": thumbnail_url}
            url_response = requests.post(Endpoints.SEARCH_BY_THUMBNAIL.value, 
                                    json = request_body,
                                    headers = helper.format_header(app.config['jwt_token']))
            url_response = helper.get_response_dict(url_response)
            print(url_response)
            if "image_url" not in url_response or url_response["image_url"] == "":
                return render_template("home.html", error = True, error_message = "No images found for given thumbnail url.")
            
            # Get image base64 encoded strings for all images
            image_request_body = {
                "bucket_name": Config.S3_BUCKET_NAME.value,
                "keys": [url_response['image_url'].split(f"https://{Config.S3_BUCKET_NAME.value}.s3.amazonaws.com/")[1]]
            }            
            images_response = requests.post(Endpoints.ENCODE_IMAGE.value, 
                                    json = image_request_body,
                                    headers = helper.format_header(app.config['jwt_token']))
            images_response = helper.get_response_dict(images_response)
            print(images_response)

            return render_template(
                "home.html", 
                error = False,
                mimetype = 'image/jpeg',
                full_image = images_response["images"][0].decode(),
                search_by_thumbnail = True,
                image_url = url_response['image_url'],
                thumbnail_url = thumbnail_url
            )
        
        except Exception as e:
            log.error(f"Exception: {e}")
            return render_template("home.html", error = True, error_message = e)
    
    return render_template("home.html", error = False)

@app.route('/search-by-image', methods=["POST"])
def search_by_image():

    s3_image_keys = list()
    decoded_images = list()

    if request.method == 'POST':
        
        try:
    
            image = request.files['image']
            if image.filename == "":
                return render_template("home.html", error = True, error_message = "No image is uploaded.")

            log.info("Encoding image to base64 string")            
            image_string = base64.b64encode(image.read())

            # Invoking upload image API
            request_body = {
                "image": image_string.decode()
            }
            image_search_response = requests.post(Endpoints.SEARCH_BY_IMAGE.value, 
                                    json = request_body,
                                    headers = helper.format_header(app.config['jwt_token']))
            image_search_response = helper.get_response_dict(image_search_response)
            
            if "thumbnail_urls" not in image_search_response or len(image_search_response["thumbnail_urls"]) == 0:
                return render_template("home.html", error = True, error_message = "No thumbnails found for given image.")
            
            if "upload_image_tags" in image_search_response and len(image_search_response['upload_image_tags']) != 0:
                tags = ', '.join(image_search_response['upload_image_tags'])

            for url in image_search_response["thumbnail_urls"]:
                s3_image_keys.append(url.split(f"https://{Config.S3_BUCKET_NAME.value}.s3.amazonaws.com/")[1])

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
                uploaded_image = image_string.decode(), 
                tags = tags,
                thumbnails = decoded_images,
                search_by_image = True
            )
        
        except Exception as e:
            log.error(f"Exception: {e}")
            return render_template("home.html", error = True, error_message = e)
    
    return render_template("home.html", error = False)

@app.route('/add-delete-tags', methods=["POST"])
def add_delete_tags():

    if request.method == 'POST':
        
        try:
            
            # Fetch the tags, urls and type of operation from the user interface
            tags = request.form.get('tags')
            urls = request.form.get('urls')
            type_of_operation = request.form.get('type-of-operation')
            
            # Throwing an error incase the text box is empty
            if tags.strip() == "" or urls.strip() == "":
                return render_template("home.html", error = True, error_message = "Tags can not be empty.")
            
            # Converting tags and url list into a list
            tags_list = [tag.strip() for tag in tags.split(";")]
            log.info(f"List of tags to query on: {tags_list}")
            
            url_list = [url.strip() for url in urls.split(";")]
            log.info(f"List of tags to query on: {url_list}")

            # Making the request_body
            request_body = {
                "url": url_list,
                "type": int(type_of_operation),
                "tags" : tags_list
            }
            
            # Calling the API and fetching the response
            response = requests.post(Endpoints.ADD_REMOVE_BY_THUMBNAIL.value, 
                                    json = request_body,
                                    headers = helper.format_header(app.config['jwt_token']))
            
            # If the API fails, display the error
            if not response.ok:
                return render_template("home.html", error = True, error_message = "Tags cannot be updated. Please check the thumbnail urls and try again")
            
            # Display the rendered output 
            result = helper.get_response_dict(response)
            return render_template(
                "home.html", 
                error = False,
                message = result['message'],
                add_delete_tags = True,
                tags = tags
            )
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

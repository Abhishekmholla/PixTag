import secrets
import auth
import base64
import helper
import logging
import requests
from config import Endpoints, Config
from flask import Flask, redirect, request, render_template, session, url_for

app = Flask(__name__)
app.secret_key = secrets.token_urlsafe(24)
logging.basicConfig(level = logging.INFO)
log = logging.getLogger(__name__)

@app.route('/', methods=['GET', 'POST'])
def sign_in():
    """
    API to sign in to PixTag
    """

    if request.method == 'POST':
        try:
            # Fetch the token by signin to application
            username = request.form.get('username')
            password = request.form.get('password')
            token = auth.sign_in(username, password)
            log.info("Adding token to app config on successful sign-in")
            app.config["jwt_token"] = token
            session['logged_in'] = True
            return redirect(url_for('home'))
        except Exception as e:
            log.error(f"Exception: {e}")
            return render_template('login.html', error = False,
                           message = "Sign in unsuccessful. Have you verified the email address or not?",
                           show_modal_flag = True)
    
    return render_template('login.html',error = False)

@app.route('/sign-up', methods=['GET', 'POST'])
def sign_up():
    '''
    API to render the signup template
    '''
    return render_template('signup.html')

@app.route('/login-user', methods=['GET', 'POST'])
def login_user():
    '''
    API to render the login template
    '''
    message = request.args.get('message', "")
    show_modal_flag = request.args.get('show_modal_flag', False)
    return render_template('login.html', error = False,
                           message = message, show_modal_flag = show_modal_flag)

@app.route('/sign-up-user', methods=['GET', 'POST'])
def sign_up_user():
    '''
    API to sign up the user
    '''
    if request.method == 'POST':
        try:
            # Fetch the required details and create a new user
            givenname = request.form.get('givenname')
            familyname = request.form.get('familyname')
            password = request.form.get('password')
            email =  request.form.get('email')
            
            session['email'] = email
            log.info("Creating new user")
            
            # Signing in the user
            auth.sign_up(givenname, familyname, password, email)
        except Exception as e:   
            #  If any errors redirect the user to login page
            log.error(f"Exception: {e}")
            return render_template('login.html', error = True,
                                   message = e,show_modal_flag = True)
    
    # If all good, load the verification template
    return render_template('verification.html', error= False)

@app.route('/verify-email', methods=['GET', 'POST'])
def verify_email():
    '''
    API to verify the user
    '''
    response_message = ""
    if request.method == 'POST':
        try:
            # Fetch the details
            verification_code = request.form.get('verifyemail')
            email = session.get('email')
            log.info("Verifying new user")
            # Verify the user 
            response_message = auth.verify_user(email, verification_code)
        except Exception as e:
            # Send an error message as modal to UI
            log.error(f"Exception: {e}")
            return render_template('verification.html', error = False,message = e,
                           show_modal_flag = True)
    # If all good, redirect user to login page
    return render_template('login.html',
                           error = False,
                           message = response_message,
                           show_modal_flag = True
                           )

@app.route('/sign-out', methods=['GET', 'POST'])
def sign_out():
    """
    API to sign out of PixTag
    """
    if request.method == 'POST':
        try:
            # session.clear()
            session['logged_in'] = False
            app.config["jwt_token"] = ""
            return redirect(url_for('login_user', message = "It is sad to see you go...cya!!", 
                            show_modal_flag = True))
        except Exception as e:
            log.error(f"Exception: {e}")
            return render_template('login.html', error = True)
    
    is_logged_in = session.get('logged_in')
    if not is_logged_in:
        return redirect(url_for('login_user'))
    else:
        return render_template("home.html", error = False)
 
@app.route('/pixtag', methods=['GET'])
def home():
    """
    Landing page API for PixTag
    """
    is_logged_in = session.get('logged_in')
    
    if not is_logged_in:
        return redirect(url_for('login_user'))
    else:
        return render_template("home.html", error = False)

@app.route('/pixtag/upload-image', methods=["GET","POST"])
def upload_image():
    '''
    API to upload image 
    '''
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
    
    is_logged_in = session.get('logged_in')
    if not is_logged_in:
        return redirect(url_for('login_user'))
    else:
        return render_template("home.html", error = False)

@app.route('/pixtag/search-by-tags', methods=["GET","POST"])
def search_by_tags():
    '''
    API to search by tags
    '''
    
    s3_image_keys = list()
    decoded_images = list()
    all_found_tags = list()
    
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
                s3_image_keys.append(link.split(f"https://{Config.S3_BUCKET_NAME.value}.s3.amazonaws.com/")[1])
                all_found_tags.append(link)
            
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
                tags = tags,
                thumbnail_urls = all_found_tags
            )
        
        except Exception as e:
            log.error(f"Exception: {e}")
            return render_template("home.html", error = True, error_message = e)
    
    is_logged_in = session.get('logged_in')
    if not is_logged_in:
        return redirect(url_for('login_user'))
    else:
        return render_template("home.html", error = False)

@app.route('/pixtag/search-by-thumbnail', methods=["GET","POST"])
def search_by_thumbnail():
    '''
    API to search by thumbnail
    '''
    
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
    
    is_logged_in = session.get('logged_in')
    if not is_logged_in:
        return redirect(url_for('login_user'))
    else:
        return render_template("home.html", error = False)

@app.route('/pixtag/search-by-image', methods=["GET","POST"])
def search_by_image():
    '''
    API to search by image
    '''

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
                search_by_image = True,
                thumbnail_urls = image_search_response["thumbnail_urls"]
            )
        
        except Exception as e:
            log.error(f"Exception: {e}")
            return render_template("home.html", error = True, error_message = e)

    is_logged_in = session.get('logged_in')
    if not is_logged_in:
        return redirect(url_for('login_user'))
    else:
        return render_template("home.html", error = False)

@app.route('/pixtag/add-delete-tags', methods=["GET","POST"])
def add_delete_tags():
    '''
    API to delete tags
    '''

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
            
            return render_template(
                "home.html", 
                error = False,
                message = "Records updated successfully",
                add_delete_tags = True,
                tags = tags,
                thumbnail_url = urls
            )
        except Exception as e:
            log.error(f"Exception: {e}")
            return render_template("home.html", error = True, error_message = e)
    
    is_logged_in = session.get('logged_in')
    if not is_logged_in:
        return redirect(url_for('login_user'))
    else:
        return render_template("home.html", error = False)
    
@app.route('/pixtag/delete-image', methods=["GET","POST","DELETE"])
def delete_images():
    '''
    API to delete images
    '''

    if request.method == 'POST':
        
        try:
            
            # Fetch the tags, urls and type of operation from the user interface
            urls = request.form.get('urls')

            # Throwing an error incase the text box is empty
            if urls.strip() == "":
                return render_template("home.html", error = True, error_message = "urls can not be empty.")

            url_list = [url.strip() for url in urls.split(";")]
            log.info(f"List of tags to query on: {url_list}")

            # Making the request_body
            request_body = {
                "url": url_list
            }

            # Calling the API and fetching the response
            response = requests.delete(Endpoints.DELETE_IMAGE.value, 
                                    json = request_body,
                                    headers = helper.format_header(app.config['jwt_token']))
            
            # # If the API fails, display the error
            if not response.ok:
                return render_template("home.html", error = True, error_message = "Tags cannot be updated. Please check the thumbnail urls and try again")
            
            # Rendering the template 
            return render_template(
                "home.html", 
                error = False,
                message = "Images deleted successfully",
                delete_image = True,
                deleted_image_url = urls
            )
            
        except Exception as e:
            log.error(f"Exception: {e}")
            return render_template("home.html", error = True, error_message = e)
    
    is_logged_in = session.get('logged_in')
    if not is_logged_in:
        return redirect(url_for('login_user'))
    else:
        return render_template("home.html", error = False)

@app.route('/pixtag/subscribe-tag', methods=["POST","GET"])
def add_user_tag_subscription():
    '''
    API to subscribe to tags
    '''
    if request.method == 'POST':
        try:
            # Fetch the tags, urls and type of operation from the user interface
            tags = request.form.get('tags')
            
            # Throwing an error incase the text box is empty
            if tags.strip() == "":
                return render_template("home.html", error = True, error_message = "tags can not be empty.")

            tags_list = [tags.strip() for url in tags.split(";")]
            log.info(f"List of tags to query on: {tags_list}")

            # Making the request_body
            request_body = {
                "tags": tags_list
            }

            # Calling the API and fetching the response
            response = requests.post(Endpoints.SUBSCRIBE_TAGS.value, 
                                    json = request_body,
                                    headers = helper.format_header(app.config['jwt_token']))
            
            # If the API fails, display the error
            if not response.ok:
                return render_template("home.html", error = True, error_message = "Tags cannot be subscribed. Please check the tags and try again")
            
            # Rendering the template 
            return render_template(
                "home.html", 
                error = False,
                message = "Tags subscribed successfully",
                subscribe_tags = True,
                tags = tags
            )
            
        except Exception as e:
            log.error(f"Exception: {e}")
            return render_template("home.html", error = True, error_message = e)
    
    is_logged_in = session.get('logged_in')
    if not is_logged_in:
        return redirect(url_for('login_user'))
    else:
        return render_template("home.html", error = False)


if __name__ == '__main__':
    app.run(debug = True)

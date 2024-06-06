import requests



<form action = "{{ url_for('search_by_tags') }}" method="post">
<md-outlined-text-field name="tags" label="Tags"></md-outlined-text-field>
 <br><br>
<md-filled-button type="submit">Search</md-filled-button>
</form>
                        
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
// Configure AWS
AWS.config.update({
    region: 'us-east-1', // Your region
    credentials: new AWS.CognitoIdentityCredentials({
        IdentityPoolId: 'YOUR_COGNITO_IDENTITY_POOL_ID' // Your Cognito Identity Pool ID
    })
});

var s3 = new AWS.S3();

// Upload image
$('#upload-btn').click(function () {
    var file = $('#file-upload')[0].files[0];
    if (!file) {
        alert('Please select a file to upload.');
        return;
    }

    var params = {
        Bucket: 'pixtag-original-images-bucket', 
        Key: file.name,
        Body: file
    };

    s3.upload(params, function (err, data) {
        if (err) {
            alert('Error uploading file: ' + err.message);
        } else {
            alert('File uploaded successfully: ' + data.Location);
            displayThumbnails();
        }
    });
});

// Display thumbnails
function displayThumbnails() {
    var params = {
        Bucket: 'pixtag-thumbnail-images-bucket'
    };

    s3.listObjects(params, function (err, data) {
        if (err) {
            alert('Error fetching thumbnails: ' + err.message);
        } else {
            $('#thumbnails').empty();
            data.Contents.forEach(function (obj) {
                var url = s3.getSignedUrl('getObject', {
                    Bucket: 'pixtag-thumbnail-images-bucket',
                    Key: obj.Key
                });
                $('#thumbnails').append('<div class="col-md-3"><img src="' + url + '" class="img-thumbnail"><input type="text" class="form-control mt-2" placeholder="Add tags"></div>');
            });
        }
    });
}

// Query images by tags (dummy function)
$('#query-btn').click(function () {
    var tags = $('#tag-query').val();
    alert('Searching for images with tags: ' + tags);
    // Implement your tag query logic here
});

// Logout (dummy function)
$('#logout-btn').click(function () {
    alert('Logging out...');
    // Implement your logout logic here
});

// Initial display of thumbnails
displayThumbnails();

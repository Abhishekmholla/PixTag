from enum import Enum
 
class Config(Enum):
    CLIENT_ID = "ehhsu1dtpp996vvuqt02l4vdg"
    AWS_ACCESS_KEY = "ASIAUYOK3KUDX26I6UUL"
    AWS_SECRET_KEY = "znky+Qrq8b6m+EZVfZjpHEtfZFCbd0xfr9cnVc+j"
    S3_BUCKET_NAME = 'g74-a3'
    AWS_REGION = 'us-east-1'

class Endpoints(Enum):
    ENCODE_IMAGE = "https://8nzosr8g61.execute-api.us-east-1.amazonaws.com/pixtag/encode-image"
    UPLOAD_IMAGE = "https://8nzosr8g61.execute-api.us-east-1.amazonaws.com/pixtag/upload-image"
    SEARCH_BY_TAGS = "https://8nzosr8g61.execute-api.us-east-1.amazonaws.com/pixtag/search-by-tags"
    SEARCH_BY_THUMBNAIL = "https://8nzosr8g61.execute-api.us-east-1.amazonaws.com/pixtag/search-by-thumbnail"

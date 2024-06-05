import boto3
from config import Config

cognito_client = boto3.client("cognito-idp", region_name = "us-east-1")

def sign_in(username, password):
    """
    AWS Cognito sign in functionality

    Parameters
    ----------
    :param username: username to login
    :param password: password to login

    Returns
    -------
    :return auth token
    """

    token = None
    response = cognito_client.initiate_auth(
        AuthFlow = 'USER_PASSWORD_AUTH',
        AuthParameters = {
            'USERNAME': username,
            'PASSWORD': password,
        },
        ClientId = Config.CLIENT_ID.value
    )
    token = response["AuthenticationResult"]["IdToken"]

    return token

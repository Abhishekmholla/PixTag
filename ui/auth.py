import boto3
from flask import render_template
from config import Config

cognito_client = boto3.client("cognito-idp", region_name="us-east-1")


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
        AuthFlow='USER_PASSWORD_AUTH',
        AuthParameters={
            'USERNAME': username,
            'PASSWORD': password,
        },
        ClientId=Config.CLIENT_ID.value
    )
    token = response["AuthenticationResult"]["IdToken"]

    print(token)
    return token


def sign_up(givenname,familyname, password, email):
    """
    AWS Cognito sign up functionality

    Parameters
    ----------
    :param username: Username for the new user
    :param password: Password for the new user
    :param email: Email of the new user

    Returns
    -------
    :return: User confirmation status or error message
    """
    try:
        
        user_attributes = [{'Name': 'email', 'Value': email},
                        {'Name': 'given_name', 'Value': givenname},
                        {'Name': 'family_name', 'Value': familyname}]

        # Sign up the user
        cognito_client.sign_up(
            ClientId=Config.CLIENT_ID.value,
            Username=email,
            Password=password,
            UserAttributes=user_attributes
        )
    except cognito_client.exceptions.UsernameExistsException as e:
        print(e)
        return (False, "User already exists. Please use a different email for signup")
    except Exception as e:
        print(e)
        return (False,"Sign up unsuccessful. Can you please try with a different email address")

    return (True, "Sign up successful. User needs to confirm email address")

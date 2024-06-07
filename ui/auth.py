import boto3
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
        
        # Defining the user attributes
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
        raise Exception("User already exists. Please use a different email for signup")
    except Exception as e:
        print(e)
        raise Exception("Sign up unsuccessful. Can you please try with a different email address")
    return "Sign up successful. User needs to confirm email address"

def verify_user(email, verification_code):
    """
    AWS Cognito verify user functionality

    Parameters
    ----------
    :param verification code: code for verification
    :param email: Email of the new user

    Returns
    -------
    :return: User verified or error message
    """
    try:
        # Verify the user code and throw error if issues caused
        cognito_client.confirm_sign_up(
            ClientId= Config.CLIENT_ID.value,
            Username= email,
            ConfirmationCode=verification_code,
        )
    except cognito_client.exceptions.UserNotFoundException as e:
        print(e)
        raise Exception("User not found. Please try signing up with different email")
    except cognito_client.exceptions.CodeMismatchException:
        print(e)
        raise Exception("Invalid verification code. Please provide a proper verification code")
    except Exception as e:
        print(e)
        raise Exception("Verification unsuccessful. Please provide a proper verification code")
    return "Verification Successful"

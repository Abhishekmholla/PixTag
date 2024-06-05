import json

def format_header(token):
    """
    Formats token into header format

    Parameters
    ----------
    :param token: token to format

    Returns
    -------
    :return a dict with auth token in header format
    """

    return {
        "Authorization": f"Bearer {token}"
    }

def get_response_dict(response):
    """
    Converts response structure to json

    Parameters
    ----------
    :param token: response body to convert to json

    Returns
    -------
    :return json response body
    """

    return eval(response.text)
import json
import boto3
from boto3.dynamodb.conditions import Key

# DynamoDB boto3 client
ddb = boto3.resource('dynamodb')
ddb_table_name = "usertagsubscription"
table = ddb.Table(ddb_table_name)
client = boto3.client('cognito-idp', region_name="us-east-1")
sns = boto3.client('sns')

user_pool_id = "us-east-1_jcJBx2Erg"
topic_arn = "arn:aws:sns:us-east-1:327379801351:tag-email-notification"

def get_records(user_id):
    '''
    This function is to fetch the records related to the user and thumbnail user provided
    '''
    # Fetching the records for the user
    records = table.query(
            KeyConditionExpression = Key('user_id').eq(user_id)
        )
    
    # returning the records fetched  
    return records
    
    
def add_ddb(user_id, subscribed_tags):
    
    # DynamoDB put_item operation
    _ = table.put_item(
        Item={
            'user_id': user_id,
            'subscribed_tags':subscribed_tags
        }
    )
    
    # returning true on postive update
    return (True,f"Records updated successfully for the user with user_id {user_id} and tags:{subscribed_tags}")

def get_user_email_from_user_id(user_id):
    response = client.admin_get_user(
            UserPoolId=user_pool_id,
            Username=user_id
        )
    for attribute in response['UserAttributes']:
        if attribute['Name'] == 'email':
            return attribute['Value']

def subscribe_to_topic(email):

    subscription_arn = ""
    print("Get list of subscriptions for given SNS topic.")
    list_subs = sns.list_subscriptions_by_topic(TopicArn = topic_arn)
    
    if "Subscriptions" in list_subs and len(list_subs["Subscriptions"]) != 0:
        for subscription in list_subs["Subscriptions"]:
            if subscription["Endpoint"] == email:
                subscription_arn = subscription["SubscriptionArn"]
                break
        
    if subscription_arn == "":
        print("Subscribing to SNS topic.")
        response = sns.subscribe(
            TopicArn=topic_arn,
            Protocol='email',
            Endpoint=email,
            Attributes={
                'FilterPolicy': json.dumps({
                    'email_id': [email]
                })
            }
        )
        return response['SubscriptionArn']
    else:
        print("User has already subscribed to topic.")
        return subscription_arn

def run(event, _):
    """
    This function adds tags subscribed by user
    """
    
    try:
        user_id = event['requestContext']['authorizer']['claims']['cognito:username']
        
        request_body = eval(event['body'])
        
         # Fetching the record details from the dynamodb
        records = get_records(user_id)
        
        subscribed_tags = []
        if records["Count"] != 0:
            subscribed_tags = list(records['Items'][0]['subscribed_tags'])  
            
         # For all the urls in the request body
        for tag in request_body['tags']:
            subscribed_tags.append(tag)
            
        _,message = add_ddb(user_id, set(subscribed_tags))
        
        user_email = get_user_email_from_user_id(user_id)
        
        subscription_arn = subscribe_to_topic(user_email)
        print("Subscription ARN:", subscription_arn)
        return send_response(200, message)
    except Exception as e:
        print(f"Failed to add tags for subscription: {e}")
        return send_response(500,f"Exception: {e}")

def send_response(status_code, message):
    '''
    A generic function to handle the response body
    '''
    response_body = dict()
    response = dict()
    response_body["message"] = message
    response["statusCode"] = status_code
    response["body"] = response_body.__str__()
    return response
  
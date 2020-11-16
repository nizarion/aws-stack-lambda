import boto3
import json
import logging
import os
from boto3.dynamodb.conditions import Key
from decimal import Decimal
from datetime import date, datetime
import math
import csv

# set up nice logging in CloudWatch
LOGGER = logging.getLogger()
LOGGER.setLevel(logging.INFO)

DYNAMO_DB = boto3.resource('dynamodb')
CALLS_TABLE = DYNAMO_DB.Table('infra-smartnumbers-calls')
OPERATORS_TABLE = DYNAMO_DB.Table('infra-smartnumbers-operators')


S3 = boto3.resource('s3')
OUTPUT_BUCKET_NAME = 'infra-smartnumbers-output-bucket'
OUTPUT_BUCKET = S3.Bucket(OUTPUT_BUCKET_NAME)


def respond(err: ValueError, res: str = None) -> json:
    """ Builds response based on body """
    return {
        'statusCode': '400' if err else '200',
        'body': err.message if err else json.dumps(res),
        'headers': {
            'Content-Type': 'application/json',
        },
    }


def handler(event, context):
    LOGGER.info("Received event: \n" + json.dumps(event))

    operation = event['httpMethod']

    if operation == 'PUT':
        return match_calls_with_operator(event)
    else:
        return respond(ValueError('Unsupported method "{}"'.format(operation)))


def match_calls_with_operator(event):
    body = json.loads(event['body'])

    if body['event'] != 'New match trigger.':
        return {
            'statusCode': '400',
            'error': 'Event is not supported.'
        }

    calls = get_all_items(CALLS_TABLE)
    operators = get_all_items(OPERATORS_TABLE)
    matched_calls = []

    for call in calls:
        call_id = call['id']
        call_date = get_date_from_datetime(call['date'])

        call_number = call['number']

        if call_number == 'Withheld':
            pass

        call_prefix = call_number[3]
        call_operator = match_operator(operators, call_prefix)

        call_riskScore = calculate_riskScore(call)

        matched_calls.append(
            [call_id, call_date, call_number, call_operator, call_riskScore])

    try:
        create_store_csv(matched_calls)
    except Exception as e:
        LOGGER.error("Error updating object. Event {}".format(
            json.dumps(matched_calls, default=decimal_default)))
        LOGGER.error(e)
        return {
            'statusCode': '400',
            'error': e
        }

    LOGGER.info("ITEM received: " + json.dumps(matched_calls, default=decimal_default))

    return {
        'statusCode': '200',
        'body': json.dumps(body, default=decimal_default)
    }


def get_all_items(table):
    response = table.scan()
    return response['Items']


def decimal_default(obj):
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError


def get_date_from_datetime(date_time):
    return date_time.split("T")[0]


def create_store_csv(item_list):
    # dd/mm/YYTH:M:S
    dt_string = datetime.now().strftime("%d/%m/%YT%H:%M:%S")

    file_name = dt_string + '.csv'
    file_name = '/tmp/hello.csv'

    with open(file_name, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile, delimiter=',')
        # quotechar='|', quoting=csv.QUOTE_MINIMAL)
        for item in item_list:
            writer.writerow(item)

    key = '/tmp/' + 'hello.csv'
    OUTPUT_BUCKET.upload_file(file_name, key)


def match_operator(operators, call_prefix):
    call_operator = 'Unknown'

    for operator in operators:
        operator_prefix = operator['prefix'][0]

        if operator_prefix == call_prefix:
            call_operator = operator['operator']
            return call_operator

    return call_operator


def calculate_riskScore(call):
    if call['greenList'] == True:
        return 0.0
    elif call['redList'] == True:
        return 1.0
    else:
        riskScore = call['riskScore']
        return round(riskScore, 1)

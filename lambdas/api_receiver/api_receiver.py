import boto3
import json
import logging
import os
from boto3.dynamodb.conditions import Key

# set up nice logging in CloudWatch
LOGGER = logging.getLogger()
LOGGER.setLevel(logging.INFO)

DYNAMO_DB = boto3.resource('dynamodb')
CALL_TABLE = DYNAMO_DB.Table('infra-smartnumbers-call')
OPERATOR_TABLE = DYNAMO_DB.Table('infra-smartnumbers-operator')


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

    # if operation == 'GET':
    #     return event_receiver_GET(event)
    if operation == 'POST':
        return event_receiver_POST(event)
    else:
        return respond(ValueError('Unsupported method "{}"'.format(operation)))


def process_call_event(data_item):
    item = {
        'id': data_item['id'],
        'date': data_item['attributes']['date'],
        'riskScore': data_item['attributes']['riskScore'],
        'number': data_item['attributes']['number'],
        'greenList': data_item['attributes']['greenList'],
        'redList': data_item['attributes']['redList']
    }

    return item


def porcess_operator_event(data_item):
    item = {
        'id': data_item['id'],
        'prefix': data_item['attributes']['prefix'],
        'operator': data_item['attributes']['operator']
    }

    return item


def event_receiver_POST(event):
    body = json.loads(event['body'])

    for data_item in body:
        item = {}
        item_type = body['type']

        if item_type == 'call':
            item = process_call_event(data_item)
        elif item_type == 'operator':
            item = porcess_operator_event(data_item)
        else:
            return respond(ValueError('Unsupported method "{}"'.format(item_type)))

        try:
            if item_type == 'call':
                CALL_TABLE.put_item(
                    item
                )
            elif item_type == 'operator':
                OPERATOR_TABLE.put_item(
                    item
                )

        except Exception as e:
            LOGGER.error("Error processing object. Event {}".format(
                json.dumps(data_item)))
            LOGGER.error(e)
            return {
                'statusCode': '400',
                'error': e
            }

        LOGGER.info("ITEM: " + data_item)

        return {
            'statusCode': '200',
            'body': data_item
        }

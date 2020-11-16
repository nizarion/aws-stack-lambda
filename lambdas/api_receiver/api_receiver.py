import boto3
import json
import logging
import os
from boto3.dynamodb.conditions import Key
from decimal import Decimal

# set up nice logging in CloudWatch
LOGGER = logging.getLogger()
LOGGER.setLevel(logging.INFO)

DYNAMO_DB = boto3.resource('dynamodb')
CALLS_TABLE = DYNAMO_DB.Table('infra-smartnumbers-calls')
OPERATORS_TABLE = DYNAMO_DB.Table('infra-smartnumbers-operators')


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

    if operation == 'POST':
        return event_receiver_POST(event)
    else:
        return respond(ValueError('Unsupported method "{}"'.format(operation)))


def process_call_event(data_item):
    attributes = data_item.get('attributes')
    
    id: str = data_item['id']
    date: str = attributes['date']
    riskScore  = Decimal(str(attributes['riskScore']))
    number: str = attributes.get('number', 'Withheld')
    greenList: bool = attributes['greenList']
    redList: bool = attributes['redList']

    item = {
        'id': id,
        'date': date,
        'riskScore': riskScore,
        'number': number,
        'greenList': greenList,
        'redList': redList
    }

    return item


def porcess_operator_event(data_item):
    attributes = data_item.get('attributes')

    item = {
        'id': data_item['id'],
        'prefix': attributes['prefix'],
        'operator': attributes['operator']
    }

    return item


def event_receiver_POST(event):
    body = json.loads(event['body'])

    for data_item in body['data']:
        item = {}

        try:
            item_type = data_item['type']

            if item_type == 'call':
                item = process_call_event(data_item)
            elif item_type == 'operator':
                item = porcess_operator_event(data_item)
            else:
                return respond(ValueError('Unsupported method "{}"'.format(item_type)))

            if item_type == 'call':
                CALLS_TABLE.put_item(
                    Item = item
                )
            elif item_type == 'operator':
                OPERATORS_TABLE.put_item(
                    Item = item
                )

        except Exception as e:
            LOGGER.error("Error processing object. Event {}".format(
                json.dumps(data_item)))
            LOGGER.error(e)
            return {
                'statusCode': '400',
                'error': e
            }

        LOGGER.info("ITEM received: " + json.dumps(data_item))

    return {
        'statusCode': '200',
        'body': json.dumps(body)
    }

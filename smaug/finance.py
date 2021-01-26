import os
from datetime import datetime, timedelta
import time

import boto3

client = boto3.client('logs')


# cloudwatch logs insights query
QUERY = '''
    fields @message
    | filter @message like "smaug#id"
    | parse @message /\[(?<level>\S+)\]\s+(?<ts>\S+)\s+(?<rid>\S+)\s+(?<msg>\S+)/
    | parse msg /smaug#id#(?<id>\S+)#whitelabel#(?<whitelabel>\S+)#customer#(?<customer>\S+)#key#(?<key>\S+)#n#(?<calls>\S+)/
    | parse id /(?<endpoint>[^\s\?\#]+)(\?(?<query>\S+))?/
    | parse endpoint /(?<stage>[^\s\/]+)(?<api>\S+)?/
    | stats sum(calls) as total_calls by whitelabel, customer, stage, api
'''

STAGE = os.getenv('STAGE', 'dev')
# TODO: see if logs group can be inferred from serverless/cloudformation config
LOG_GROUP = f'/aws/lambda/smaug-{STAGE}-increment'


def get_yst_range():
    yst = datetime.utcnow() - timedelta(days=1)
    start = yst.replace(hour=0, minute=0, second=0, microsecond=0)
    end = start + timedelta(days=1) - timedelta(microseconds=1)
    return start, end


def query(start: datetime = None, end: datetime = None):
    # TODO: for now both start and end need to be supplied together, or ignored
    if not start or not end:
        start, end = get_yst_range()

    r = client.start_query(
        logGroupName=LOG_GROUP,
        startTime=int(start.timestamp()),
        endTime=int(end.timestamp()),
        queryString=QUERY,
    )

    response = None

    while response is None or response['status'] == 'Running':
        time.sleep(0.5)
        response = client.get_query_results(queryId=r['queryId'])

    return response


if __name__ == '__main__':
    from pprint import pprint
    pprint(query())
    # sample output
    '''
    {'ResponseMetadata': {'HTTPHeaders': {'content-length': '876',
                                      'content-type': 'application/x-amz-json-1.1',
                                      'date': 'Tue, 26 Jan 2021 18:25:22 GMT',
                                      'x-amzn-requestid': 'cc8625b3-b155-48ce-835e-b97716d59ecc'},
                        'HTTPStatusCode': 200,
                        'RequestId': 'cc8625b3-b155-48ce-835e-b97716d59ecc',
                        'RetryAttempts': 0},
    'results': [[{'field': 'whitelabel', 'value': '-1'},
                {'field': 'customer', 'value': '-1'},
                {'field': 'stage', 'value': 'prod'},
                {'field': 'api', 'value': '/activity/popular-times'},
                {'field': 'total_calls', 'value': '867'}],
                [{'field': 'whitelabel', 'value': '-1'},
                {'field': 'customer', 'value': '-1'},
                {'field': 'stage', 'value': 'prod'},
                {'field': 'api', 'value': '/dataset/enrich'},
                {'field': 'total_calls', 'value': '88104'}],
                [{'field': 'whitelabel', 'value': '-1'},
                {'field': 'customer', 'value': '-1'},
                {'field': 'stage', 'value': 'prod'},
                {'field': 'api', 'value': '/dataset/enrichments'},
                {'field': 'total_calls', 'value': '10'}],
                [{'field': 'whitelabel', 'value': '-1'},
                {'field': 'customer', 'value': '-1'},
                {'field': 'stage', 'value': 'prod'},
                {'field': 'api', 'value': '/dataset/poi-list/fsa'},
                {'field': 'total_calls', 'value': '2'}]],
    'statistics': {'bytesScanned': 267362.0,
                    'recordsMatched': 100.0,
                    'recordsScanned': 400.0},
    'status': 'Complete'}
    '''

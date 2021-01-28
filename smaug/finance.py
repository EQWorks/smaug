import os
from datetime import datetime, timedelta
import time

import boto3
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import insert

from smaug.db import engine

client = boto3.client('logs')


# cloudwatch logs insights query
QUERY = '''
    fields @message, @timestamp
    | filter @message like "smaug#id"
    | parse @message /\[(?<level>\S+)\]\s+(?<ts>\S+)\s+(?<rid>\S+)\s+(?<msg>\S+)/
    | parse msg /smaug#id#(?<id>\S+)#whitelabel#(?<whitelabel>\S+)#customer#(?<customer>\S+)#key#(?<key>\S+)#n#(?<counts>\S+)/
    | parse id /(?<endpoint>[^\s\?\#]+)(\?(?<query>\S+))?/
    # | display datefloor(@timestamp, 1h) as hour # can be grouped by through stats below
    # | display datefloor(@timestamp, 1d) as day # can be grouped by through stats below
    | stats sum(counts) as total_counts by whitelabel, customer, endpoint
'''  # noqa: W605

STAGE = os.getenv('STAGE', 'dev')
# TODO: see if logs group can be inferred from serverless/cloudformation config
LOG_GROUP = f'/aws/lambda/smaug-{STAGE}-increment'


def get_yst_range():
    yst = datetime.utcnow() - timedelta(days=1)
    start = yst.replace(hour=0, minute=0, second=0, microsecond=0)
    end = start + timedelta(days=1) - timedelta(microseconds=1)
    return start, end


def transform(results: list, date: datetime):
    rows = []

    for res in results:
        row = dict(date=date.strftime('%Y-%m-%d'))

        for kv in res:
            row[kv['field']] = kv['value']

        rows.append(row)

    return rows


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

    results = transform(response.get('results'), start)

    return results


def write(results):
    table = sa.Table(
        'locus_api_report',
        sa.MetaData(),
        autoload_with=engine,
    )
    stmt = insert(table).values(results)
    stmt = stmt.on_conflict_do_update(
        constraint=table.primary_key,
        set_=dict(total_counts=stmt.excluded.total_counts)
    )
    with engine.connect() as conn:
        conn.execute(stmt)


if __name__ == '__main__':
    results = query()
    write(results)

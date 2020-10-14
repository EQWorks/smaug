import json

from smaug.counter import incr


def increment(event):
    config = event.get('config')
    n = event.get('n') or 1

    return {
        'statusCode': 200,
        'body': json.dumps({'incremented': incr(config, n)}),
    }


if __name__ == '__main__':
    config = {'id': 'test-api-call', 'minute': 10}
    incremented = incr(config, n=3)
    print(config, f'\n\tincremented: {incremented}')

    config = {'id': 'test-api-call', 'minute': 10}
    incremented = incr(config, n=-10)
    print(config, f'\n\tincremented: {incremented}')

    config = {'id': 'test-api-call-unlimited'}
    incremented = incr(config, n=1)
    print(config, f'\n\tincremented: {incremented}')

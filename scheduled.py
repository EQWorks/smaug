from smaug.finance import query, write


def daily(event, *args, **kwargs):
    results = query()
    write(results)

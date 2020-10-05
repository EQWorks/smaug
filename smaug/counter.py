import os
from hashlib import sha1
from datetime import datetime
import calendar

try:
    import simplejson as json
except ImportError:
    import json

import redis


client = redis.from_url(os.getenv('REDIS_URL', 'redis://localhost:6379/9'))


# Dict[str, Tuple[type, default]]
CONFIG_TYPES = {
    # 'pre': (bool, False),  # TODO; implement pre/post-pay graceful limit
    'minute': (int, -1),
    'hour': (int, -1),
    'day': (int, -1),
    'month': (int, -1),
    'white-label': (str, None),
    'customer': (str, None),
    'user': (str, None),
}


def vet_config(id: str, **kwargs) -> dict:
    """Vetting function to ensure meaningful counter configs.

    Args:
        id (str): Required identification string for the counter.
        **kwargs: Arbitrary keyword arguments of counter config keys.
                  should be gradually displaced by specifically named
                  arguments once the APIs get stable.

    Returns:
        dict: vetted counter config.

    Examples:

        >>> vet_config(id='test_counter', a=1, pre=True, month=10000)
        {'id': 'test_counter', 'pre': True, 'month': 10000}
    """
    if not id or type(id) is not str:
        raise ValueError('A string id is required')

    r = dict(id=id)

    for k, v in kwargs.items():
        _type, _default = CONFIG_TYPES.get(k, (None, None))
        if _type is not None:
            r[k] = v if type(v) is _type else _default

    return r


def get_config_key(config: dict) -> str:
    """Get hash key from a given counter config.

    Args:
        config (dict): counter config dict.

    Returns:
        str: The hash hex digest string.

    Examples:

        >>> get_config_key(config={'id': 'test_counter', 'pre': True, 'per_month': 50000})
        'd78ac92af4ca90e8bc3c7c04981efd8f8bd7a95d'
    """
    return sha1(json.dumps(config, sort_keys=True).encode()).hexdigest()


def get_end_of(time: datetime = None):
    if datetime is not None:
        time = datetime.now()

    # end day of month
    month_end = (calendar.monthrange(time.year, time.month)[1], 23, 59, 59)
    # end time of day
    day_end = month_end[1:]
    # end time of hour
    hour_end = day_end[1:]
    # end time of minute
    minute_end = hour_end[1:]

    return dict(
        month=datetime(time.year, time.month, *month_end),
        day=datetime(time.year, time.month, time.day, *day_end),
        hour=datetime(time.year, time.month, time.day, time.hour, *hour_end),
        minute=datetime(time.year, time.month, time.day, time.hour, time.minute, *minute_end),
    )


def incr(config: dict, vet: bool = True, key: str = None) -> bool:
    """Increment periodic counter(s) based on the given config.

    Args:
        config (dict): counter configuration.
        vet (bool): whether to run vet_config(config). Default: True.
        key (str): run get_config_key(config) when not supplied. Default: None.

    Returns:
        bool - True when periodic counter(s) are incremented properly; False otherwise.
    """
    if vet:
        config = vet_config(config)

    if not key:
        key = get_config_key(config)

    ends = get_end_of()
    counts = get(config, vet=False, key=key)

    with client.pipeline() as pipe:
        # config hash/dict
        pipe.hmset(f'config#{key}', config)
        # periodic
        for k, v in config.items():
            if end := ends.get(k):
                counter_key = f'counter#{k}#{key}'

                if v > -1 and counts.get(k, 0) < v:
                    pipe.incr(counter_key)
                    pipe.expireat(counter_key, end.timestamp())
                else:
                    return False

        pipe.execute()
        return True

increment = incr


def get(config: dict, vet: bool = True, key: str = None) -> dict:
    """Get current counts from periodic counter(s) based on the given config."""
    if vet:
        config = vet_config(config)

    if key is None:
        key = get_config_key(config)

    with client.pipeline() as pipe:
        periods = []
        for k in config.keys():
            if ends.get('k'):
                counter_key = f'counter#{k}#{key}'
                periods.append(k)
                pipe.get(counter_key)

        return dict(zip(periods, [int(r) for r in pipe.execute()]))

from hashlib import sha1
from datetime import datetime
import calendar
from string import Template
try:
    import simplejson as json
except ImportError:
    import json


# Dict[str, Tuple[type, default]]
CONFIG_TYPES = {
    # 'pre': (bool, False),  # TODO: implement pre/post-pay graceful limit
    'minute': (int, -1),
    'hour': (int, -1),
    'day': (int, -1),
    'month': (int, -1),
    'white-label': (str, None),
    'customer': (str, None),
    'user': (str, None),
    'prefix': (str, None),
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

        >>> vet_config(id='test_counter', a=1, month=10000)
        {'id': 'test_counter', month': 10000}
    """
    if not id or type(id) is not str:
        raise ValueError('A string id is required')

    r = dict(id=id)

    for k, v in kwargs.items():
        _type, _default = CONFIG_TYPES.get(k, (None, None))
        if _type is not None:
            r[k] = v if type(v) is _type else _default

    return r


def get_config_key(config: dict, vet: bool = True) -> str:
    """Get hash key from a given counter config.

    Args:
        config (dict): counter config dict.
        vet (bool): whether to run through vet_config(). Default: True.

    Returns:
        str: the hash hex digest string.

    Examples:

        >>> get_config_key({'id': 'test_counter', 'a': 1, 'month': 50000})
        'a0f109817eb6f7ae4b201fb00338386354c026de'
        >>> get_config_key({'month': 50000, 'a': 1, 'id': 'test_counter'})
        'a0f109817eb6f7ae4b201fb00338386354c026de'
        >>> get_config_key({'a': 1, 'id': 'test_counter'}, vet=False)
        '58b67b3f1049f3863f69df4842f8fd743a8e00fa'
    """
    if vet:
        config = vet_config(**config)

    return sha1(json.dumps(config, sort_keys=True).encode()).hexdigest()


def get_end_of(time: datetime = None) -> dict:
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
        minute=datetime(
            time.year,
            time.month,
            time.day,
            time.hour,
            time.minute,
            *minute_end,
        ),
    )


def get_log_template(config: dict, vet: bool = True) -> str:
    if vet:
        config = vet_config(config)

    f = 'smaug'
    for k in config.keys():
        _type, _ = CONFIG_TYPES.get(k, (None, None))
        if k == 'id' or _type is str:  # categorical
            f += f'#{k}#${k}'

    f += '#config_key#$config_key}#n#$n'
    return Template(f)

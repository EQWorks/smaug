from hashlib import sha1

try:
    import simplejson as json
except ImportError:
    import json


# Dict[str, Tuple[type, default]]
CONFIG_TYPES = {
    'pre': (bool, False),
    'minute': (int, -1),
    'hour': (int, -1),
    'day': (int, -1),
    'month': (int, -1),
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

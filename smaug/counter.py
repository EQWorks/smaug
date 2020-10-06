import os

import redis

from smaug.config import vet_config, get_config_key, get_end_of


client = redis.from_url(os.getenv('REDIS_URL', 'redis://localhost:6379/9'))


def incr(config: dict, vet: bool = True, key: str = None, n: int = 1) -> bool:
    """Increment periodic counter(s) based on the given config.

    Args:
        config (dict): counter configuration.
        vet (bool): whether to run vet_config(config). Default: True.
        key (str): run get_config_key(config) when not supplied. Default: None.
        n (int): number of times counters should be incremented. Default: 1.

    Returns:
        bool - True when periodic counter(s) are incremented properly;
               False otherwise.
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

                if v == -1:  # no rate limiting
                    continue

                if (counts.get(k, 0) + n) <= v:
                    for _ in range(n):  # multiple counts
                        pipe.incr(counter_key)

                    pipe.expireat(counter_key, end.timestamp())
                else:
                    return False  # deny

        pipe.execute()
        return True  # pass


increment = incr


def get(config: dict, vet: bool = True, key: str = None) -> dict:
    """Get current counts from periodic counter(s) with the given config.

    Args:
        config (dict): counter configuration.
        vet (bool): whether to run vet_config(config). Default: True.
        key (str): run get_config_key(config) when not supplied. Default: None.

    Returns:
        dict - counts from periodic counter(s).
    """
    if vet:
        config = vet_config(config)

    if key is None:
        key = get_config_key(config)

    ends = get_end_of()

    with client.pipeline() as pipe:
        periods = []
        for k in config.keys():
            if ends.get(k):
                counter_key = f'counter#{k}#{key}'
                periods.append(k)
                pipe.get(counter_key)

        return dict(zip(periods, [int(r) for r in pipe.execute()]))

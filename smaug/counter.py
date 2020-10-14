import logging

from smaug.db import r
from smaug.config import (
    vet_config,
    get_config_key,
    get_end_of,
    get_log_template,
)


logger = logging.getLogger(__name__)


def incr(config: dict, n: int = 1) -> bool:
    """Increment periodic counter(s) based on the given config.

    Args:
        config (dict): counter config dict.
        n (int): number of times counters should be incremented. Default: 1.

    Returns:
        bool - True when periodic counter(s) are incremented properly;
               False otherwise.
    """
    ends = get_end_of()
    config = vet_config(**config)
    key = get_config_key(config, vet=False)
    t = get_log_template(config, vet=False)
    counts = get(config, key=key, vet=False, ends=ends)
    config_key = f'smaug#{key}'

    if n == 0:  # empty count returns False
        return False

    if n < 0:  # skip counter for -counts, eg for billing corrections
        # logging for billing purposes
        logger.info(t.substitute(**config, key=key, n=n))
        return True  # pass

    with r.pipeline() as pipe:
        # refresh config key
        pipe.hmset(config_key, config)
        pipe.expire(config_key, 5259600)  # ~2 months retention
        # periodic
        for k, v in config.items():
            if end := ends.get(k):
                counter_key = f'counter#{k}#{key}'

                if v == -1:  # no rate limiting
                    continue

                if (counts.get(k, 0) + n) <= v:
                    for _ in range(n):  # multiple counts
                        pipe.incr(counter_key)

                    pipe.expireat(counter_key, int(end.timestamp()))
                else:
                    return False  # deny

        pipe.execute()
        # logging for billing purposes
        logger.info(t.substitute(**config, key=key, n=n))
        return True  # pass


increment = incr


def get(
    config: dict,
    key: str = None,
    vet: bool = True,
    ends: dict = None,
) -> dict:
    """Get current counts from periodic counter(s) with the given config.

    Args:
        config (dict): counter config dict.
        key (str): computed config key. Default: None.
        vet (bool): whether to run through config.vet_config(). Default: True.
        ends (dict): end of periods generated from config.get_end_of().
                     Default: None, which will run get_end_of() to fetch.

    Returns:
        dict - counts from periodic counter(s).
    """
    if ends is None:
        ends = get_end_of()

    if vet:
        config = vet_config(**config)

    if key is None:
        key = get_config_key(config, vet=False)

    with r.pipeline() as pipe:
        periods = []
        for k in config.keys():
            if ends.get(k):
                counter_key = f'counter#{k}#{key}'
                periods.append(k)
                pipe.get(counter_key)

        return dict(zip(periods, [int(r) if r else 0 for r in pipe.execute()]))

import os
import logging


logger = logging.getLogger(__name__)
if not os.getenv('AWS_LAMBDA_DEPLOYED'):
    # no need for AWS Lambda deployed as it pre-configured logging
    logger.addHandler(logging.StreamHandler())

logger.setLevel(logging.INFO)

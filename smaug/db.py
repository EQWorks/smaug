import os

import redis
import sqlalchemy as sa


r = redis.from_url(os.getenv('REDIS_URL', 'redis://localhost:6379/9'))
engine = sa.create_engine(os.getenv('PG_URI', ''))

"""RQ worker entry point. Run: python worker.py"""
import logging
from redis import Redis
from rq import Worker, Queue
from config import settings

logging.basicConfig(level=logging.INFO)

redis_conn = Redis.from_url(settings.redis_url)
queue = Queue("crm", connection=redis_conn)

if __name__ == "__main__":
    worker = Worker([queue], connection=redis_conn)
    worker.work(with_scheduler=False)
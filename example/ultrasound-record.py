#!/usr/bin/env python3
import json
import os
import time
import warnings
from datetime import datetime, UTC
from pathlib import Path
from typing import Dict, List, Tuple

import redis
from gpiozero import UltrasonicSensor

warnings.simplefilter("ignore")


def redis_connection_params(**kwargs) -> Dict[str, str | int]:
    params = dict(
        unix_socket_path="/run/redis/redis.sock",
        db=1,
        # password="orthogonal-frequency-division-multiplexing$$$",
    )
    params.update(kwargs)
    return params


def redis_connection(**kwargs):
    return redis.Redis(**redis_connection_params(**kwargs))


def microwave_redis_key(timestamp: int | float) -> str:
    return f"mw:{timestamp}"


redis_conn_nanos = redis_connection(db=1)
redis_conn = redis_connection(db=1)
context = dict(last_datapoint=None)


def store_in_redis(connection, timestamp: float | int, datapoint: float):
    key = microwave_redis_key(timestamp)
    connection.lpush(key, datapoint)


def register_datapoint(timestamped_datapoint: Tuple[float, float]):
    timestamp_nanos, datapoint = timestamped_datapoint
    if context['last_datapoint'] == timestamped_datapoint:
        return
    context['last_datapoint'] = timestamped_datapoint
    store_in_redis(redis_conn_nanos, timestamp_nanos, datapoint)
    store_in_redis(redis_conn, int(timestamp_nanos), datapoint)

    ts_hf = datetime.fromtimestamp(timestamp_nanos, UTC)
    print(
        f"{ts_hf}:{datapoint}",
    )


ultrasonic_sensor = UltrasonicSensor(echo=12, trigger=16, callback=register_datapoint)

iteration = 0
while True:
    try:
        value = ultrasonic_sensor.value
        if value is None:
            continue

        if context['last_datapoint'] == value:
            continue

        # iteration += 1

        # timestamp_nanos, datapoint = value
        # ts_hf = datetime.fromtimestamp(timestamp_nanos, UTC)

        # print(
        #     f"{ts_hf} iteration {iteration}: {datapoint}",
        # )

    except KeyboardInterrupt:
        ultrasonic_sensor.close()
        raise SystemExit(1)

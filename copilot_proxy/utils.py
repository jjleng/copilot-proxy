import random
import string
import time
from typing import Any, Generator

from requests import Response
from sseclient import SSEClient


def generate_random_string(length: int = 32) -> str:
    """Generate a random string of fixed length."""
    letters_and_digits = string.ascii_lowercase + string.digits
    return "".join(random.choice(letters_and_digits) for i in range(length))


def generate_fake_asn():
    """Generate a fake ASN (Autonomous System Number) in the format ASXXXX:hash."""
    # Generate a random ASN number part
    asn_number = random.randint(1, 99999)
    # Generate a random hash part (32 characters long, similar to the example)
    hash_part = "".join(random.choices("0123456789abcdef", k=64))
    return f"AS{asn_number}:{hash_part}"


def generate_fake_ip():
    """Generate a fake IPv4 address."""
    return ".".join(str(random.randint(0, 255)) for _ in range(4))


def generate_epoch_15min_later():
    """Generate an epoch time for 15 minutes later."""
    current_time = time.time()
    fifteen_minutes = 15 * 60  # 15 minutes in seconds
    future_time = current_time + fifteen_minutes
    return int(future_time)


def parse_sse_stream(response: Response) -> Generator[str, Any, None]:
    client = SSEClient((chunk for chunk in response.iter_content()))
    for event in client.events():
        if event.data:
            yield event.data

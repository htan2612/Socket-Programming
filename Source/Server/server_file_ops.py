

import os
import sys

_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
_SOURCE_DIR = os.path.abspath(os.path.join(_BASE_DIR, ".."))
if _SOURCE_DIR not in sys.path:
    sys.path.append(_SOURCE_DIR)

from Common.protocol_constants import REPLY_CODES


def build_reply(code: int, extra: str = None) -> str:

    if code not in REPLY_CODES:
        raise ValueError(f"Mã reply {code} không tồn tại trong protocol_constants.REPLY_CODES")
    message = extra if extra else REPLY_CODES[code]
    return f"{code} {message}\r\n"


def is_success(code: int) -> bool:
    return 100 <= code < 400
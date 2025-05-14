import base64
import gzip
import io
import logging
from typing import Any, Dict, Optional, Tuple, Union

import nbtlib

meta_logger = logging.getLogger('meta')


def normalize_nbt(obj: Any) -> Any:
    """
    Recursively convert NBT tag objects and raw byte arrays
    into plain Python primitives (dict, list, int, str, etc.).
    This will handle:
      - nbtlib.tag.Compound (has .items)
      - nbtlib.tag.List (is iterable)
      - any Tag with a .value
      - raw bytes/bytearray
    """
    # 1) Raw bytes/bytearray → list of ints
    if isinstance(obj, (bytes, bytearray)):
        return list(obj)

    # 2) Any nbtlib Tag (it always has .value)
    if hasattr(obj, 'value'):
        return normalize_nbt(obj.value)

    # 3) Mapping types (Compound acts like a dict)
    if hasattr(obj, 'items'):
        return {k: normalize_nbt(v) for k, v in obj.items()}

    # 4) Iterable list types (nbtlib List, Python list/tuple, etc.)
    #    but skip strings (they're iterable but should stay str)
    if isinstance(obj, (list, tuple)) or (hasattr(obj, '__iter__') and not isinstance(obj, (str, bytes, bytearray))):
        return [normalize_nbt(v) for v in obj]

    # 5) Primitives (int, str, float, bool, None) pass through
    return obj


def decode_item_bytes(item_bytes_str: str) -> Optional[nbtlib.File]:
    """
    Decode a base64+gzip-compressed NBT payload into an nbtlib File.
    Returns None on failure.
    """
    try:
        compressed = base64.b64decode(item_bytes_str)
        with gzip.GzipFile(fileobj=io.BytesIO(compressed)) as gz:
            data = gz.read()
        return nbtlib.File.parse(io.BytesIO(data))
    except Exception:
        meta_logger.exception("Failed to decode item_bytes")
        return None


def resolve_name(raw: Dict[str, Any]) -> Union[str, Tuple[str, Dict[str, Any]]]:
    """
    Resolve an item's display name. Returns either:
      - a simple name (str)
      - a tuple (item_id, normalized_item_data) when parsed from NBT
      - 'Unknown' on failure
    """
    try:
        # get the raw base64 string or fallback to raw dict
        try:
            item_bytes = raw.get('item_bytes')
        except Exception:
            item_bytes = raw

        if item_bytes:
            nbt_file = decode_item_bytes(item_bytes)
            if nbt_file is None:
                return 'Unknown'

            item_list = nbt_file.get('i')
            if not item_list:
                return 'Unknown'

            item_data = item_list[0]
            item_id = (
                item_data
                .get('tag', {})
                .get('ExtraAttributes', {})
                .get('id', 'Unknown')
            )

            # **fully normalize** so no ByteArray or Tag objects remain
            item_data_clean = normalize_nbt(item_data)

            return item_id, item_data_clean

        return 'Unknown'
    except Exception:
        meta_logger.exception(f"Error resolving name for raw: {raw}")
        return 'Unknown'

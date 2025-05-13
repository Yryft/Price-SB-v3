import base64, gzip, io, logging, json
from typing import Dict, Any, Optional, Tuple, Union
import nbtlib

meta_logger = logging.getLogger('meta')

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
      - a tuple (item_id, item_data) when parsed from NBT
      - 'Unknown' on failure
    """
    try:

        # 1 Fallback to NBT bytes
        try: 
            item_bytes = raw.get('item_bytes')
        except Exception:
            item_bytes = raw
        if item_bytes:
            meta_logger.debug(f"Using item_bytes for name resolution")
            nbt = decode_item_bytes(item_bytes)
            if nbt is None:
                return 'Unknown'

            # Expect structure: { 'i': [ { ... } ] }
            item_list = nbt.get('i')
            if not item_list:
                return 'Unknown'
            meta_logger.debug(f"Resolved name: {item_list[0].get('tag', {}).get('ExtraAttributes', {}).get('id', 'Unknown')}")  
            item_data = item_list[0]
            item_id = item_data.get('tag', {}).get('ExtraAttributes', {}).get('id', 'Unknown')
            return item_id, item_data

        return 'Unknown'
    except Exception:
        meta_logger.exception(f"Error resolving name for raw: {raw}")
        return 'Unknown'
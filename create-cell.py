from tonsdk.boc import Builder, Cell, begin_dict
from tonsdk.utils import Address

from largeboc import to_boc

from pathlib import Path
import traceback
import hashlib
import json



def serialize_short(t: str) -> Cell:
  c = Builder()
  c.store_uint(0, 8)
  c.store_bytes(t.encode('utf-8'))
  assert len(t.encode('utf-8')) * 8 + 8 < 1024
  return c.end_cell()


def bytes_to_chunked(t: bytes) -> Cell:
  CHUNK_BYTES = 126
  b = Builder()
  b.store_uint(1, 8)
  d = begin_dict(32)
  for i in range(0, len(t), CHUNK_BYTES):
    part = t[i:i+CHUNK_BYTES]
    c = Builder()
    c.store_bytes(part)
    d.store_ref(i // CHUNK_BYTES, c.end_cell())
  b.store_maybe_ref(d.end_dict())
  return b.end_cell()

SERIALIZERS = {'__serialize_short': serialize_short, '__serialize_chunked': bytes_to_chunked}


def serialize_metadata(config: dict[str, list[str]]) -> Cell:
  sha256 = lambda v: hashlib.sha256(v.encode('utf-8')).digest()
  d = begin_dict(256)
  for param, store in config.items():
    serialize_method, store_value = store
    store_bytes = SERIALIZERS[serialize_method](store_value)
    d.store_ref(sha256(param), store_bytes)
  return d.end_dict()


def serialize_content(config: dict[str, list[str]]) -> Cell:
  b = Builder()
  b.store_uint(0, 8)
  b.store_maybe_ref(serialize_metadata(config))
  return b.end_cell()


def main():
  assets_dir = Path(__file__).parent / 'assets'
  config = json.loads((assets_dir / 'content.json').read_bytes())
  
  nft_config = config['nft']
  nft_config['image_data'] = ['__serialize_chunked', (assets_dir / nft_config.pop('image_path')).read_bytes()]
  (assets_dir / 'content.boc').write_bytes(to_boc(serialize_content(nft_config), False))
  # (assets_dir / 'content.boc').write_bytes(serialize_content(nft_config).to_boc(False))
  
  coll_config = config['collection']
  coll_config['image_data'] = ['__serialize_chunked', (assets_dir / coll_config.pop('image_path')).read_bytes()]
  (assets_dir / 'collection-content.boc').write_bytes(to_boc(serialize_content(coll_config), False))
  # (assets_dir / 'collection-content.boc').write_bytes(serialize_content(coll_config).to_boc(False))


if __name__ == '__main__':
  try:
    main()
  except:
    traceback.print_exc()
  # finally:
    input('...')

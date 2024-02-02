import base64


def to_top_upped_array(bs):
  buffer, cursor = bs.array, bs.cursor
  if cursor % 8 == 0:
    return buffer[:cursor//8]
  else:
    # example:  cursor % 8 = 6,  buffer[cursor//8] = XXXXXX00
    r = cursor % 8
    buffer[cursor//8] &= ~((256 >> r) - 1)
    buffer[cursor//8] |= 256 >> (r+1)
    return buffer[:cursor//8+1]


def cell_represent_len(cell, index, cell_id_size):
  return 2 + len(cell.bits.get_top_upped_array()) + cell_id_size * len(cell.refs)


def cell_represent(cell, index, cell_id_size):
  refs_descriptor = len(cell.refs) + 8 * 0 + 32 * 0
  bits_descriptor = cell.bits.cursor // 8 + (cell.bits.cursor + 7) // 8
  
  result = bytes([refs_descriptor, bits_descriptor])
  # result += cell.bits.get_top_upped_array()
  result += to_top_upped_array(cell.bits)
  for ref in cell.refs:
    i = index[ref.bytes_hash()]
    result += i.to_bytes(cell_id_size, 'big')
  return result


def to_boc(cell, has_idx=False, hash_crc32=True, has_cache_bits=False):
  from tonsdk.boc._bit_string import BitString
  from tonsdk.utils import crc32c
  
  bytes_len = lambda n: (n.bit_length() + 7) // 8
  
  tour_hash_to_cell, index = cell.tree_walk()
  
  result = BitString((1023 + 32 * 7) * len(tour_hash_to_cell))
  cell_id_size = bytes_len(len(tour_hash_to_cell))
  cell_lens = {}
  
  for (chash, cell) in tour_hash_to_cell:
    # cell_lens[chash] = cell.boc_serialization_size(index, cell_id_size)
    cell_lens[chash] = cell_represent_len(cell, index, cell_id_size)
  full_size = sum(cell_lens.values())
  full_size_size = bytes_len(full_size)
  
  # +32 bits: magic
  result.write_bytes(base64.b16decode('B5EE9C72'))
  
  # +8 bits: flags + cell ID size
  result.write_bit(has_idx)
  result.write_bit(hash_crc32)
  result.write_bit(has_cache_bits)
  result.write_uint(0, 2)
  result.write_uint(cell_id_size, 3)
  
  result.write_uint(full_size_size, 8)  # +8 bits: var-uint length for full size
  result.write_uint(len(tour_hash_to_cell), cell_id_size * 8)   # cells
  result.write_uint(1, cell_id_size * 8)                        # roots
  result.write_uint(0, cell_id_size * 8)                        # absent
  result.write_uint(full_size, full_size_size * 8)              # tot_cells_size
  result.write_uint(0, 1 * cell_id_size * 8)                    # root_list
  
  if has_idx:
    for (chash, cell) in tour_hash_to_cell:
      result.write_uint(cell_lens[chash], full_size_size * 8)
  
  for (chash, cell) in tour_hash_to_cell:
    # cell_repr = cell.serialize_for_boc(index, cell_id_size)
    cell_repr = cell_represent(cell, index, cell_id_size)
    if len(cell_repr) != cell_lens[chash]:
      print(chash)
      print(cell)
      print(cell_repr)
      print(cell_lens[chash])
      print('Maybe:', cell.serialize_for_boc(index, cell_id_size))
      raise Exception('Mismatch with representation length')
      
    result.write_bytes(cell_repr)                               # cell_data
  
  # boc = result.get_top_upped_array()
  boc = bytes(to_top_upped_array(result))
  
  dup_result = BitString((1023 + 32 * 7) * len(tour_hash_to_cell))
  dup_result.set_top_upped_array(boc)
  assert tuple(result) == tuple(dup_result)
  
  return boc + (crc32c(boc) if hash_crc32 else b'')

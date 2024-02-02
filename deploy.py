from tonsdk.crypto import mnemonic_to_wallet_key
from tonsdk.contract.wallet import Wallets
from tonsdk.boc import Cell, begin_cell
from base64 import b64encode, b64decode
from tonsdk.contract import Contract
from tonsdk.utils import Address
from largeboc import to_boc
from pathlib import Path
import requests
import getpass


owner_wallet_type = Wallets.ALL['v4r2']
owner = Address('EQCyoez1VF4HbNNq5Rbqfr3zKuoAjKorhK-YZr7LIIiVrSD7')
owner_mnemonic = getpass.getpass('Mnemonic: ')

public_key, private_key = mnemonic_to_wallet_key(owner_mnemonic.split())

def sign_multitransfer_body(wallet: Contract, seqno: int,
                            orders: list[tuple[Address,Cell,Cell,int]]) -> Cell:
    assert len(orders) <= 4
    send_mode = 3
    signing_message = wallet.create_signing_message(seqno)
    for (to_addr, state_init, payload, amount) in orders:
        order_header = Contract.create_internal_message_header(to_addr, amount)
        order = Contract.create_common_msg_info(order_header, state_init, payload)
        signing_message.bits.write_uint8(send_mode)
        signing_message.refs.append(order)
    return wallet.create_external_message(signing_message, seqno)['message']

def send_from_owner_wallet(endpoint: str, orders: list[tuple[Address,Cell,Cell,int]]):
    wallet = owner_wallet_type(public_key=public_key, private_key=private_key)
    # assert wallet.address.to_string(False) == owner.to_string(False)
    wallet_state = requests.get(f'{endpoint}getWalletInformation?address={owner.to_string()}').json()['result']
    seqno = wallet_state['seqno']
    external = sign_multitransfer_body(wallet, seqno, orders)
    
    to_send = {'boc': b64encode(to_boc(external, False)).decode('ascii')}
    print('About to send (from', wallet.address.to_string(True, True, False), ')', to_send)
    if input('OK? [y/n] ').lower() == 'y':
        print(requests.post(f'{endpoint}sendBoc', json=to_send).json())


collection_code_boc = (Path(__file__) / '../assets/collection-code.boc').read_bytes()
collection_code = Cell.one_from_boc(collection_code_boc)
collection_si = begin_cell().store_uint(6, 5).store_ref(collection_code).store_ref(begin_cell().store_uint(0, 1).end_cell()).end_cell()
collection_addr = Address('0:' + collection_si.bytes_hash().hex())

send_from_owner_wallet('https://ton.access.orbs.network/44A1c0ff5Bd3F8B62C092Ab4D238bEE463E644A1/1/mainnet/toncenter-api-v2/',
                       [(collection_addr, collection_si, begin_cell().end_cell(), int(1.2e9))])

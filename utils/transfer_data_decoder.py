import base58
import eth_abi


def decode_transfer(tx_data: str) -> (str, int):
    # sig = tx_data[:8]
    data = tx_data[8:]

    encoded_address = data[:64]
    encoded_uint256 = data[64:]

    address_bytes = bytes.fromhex(encoded_address)[-20:].rjust(32, b'\0')
    uint256_bytes = bytes.fromhex(encoded_uint256)

    decoded_address, decoded_amount = eth_abi.decode_abi(['address', 'uint256'], address_bytes + uint256_bytes)

    tron_address = base58.b58encode_check(bytes.fromhex('41' + decoded_address[2:]))

    return tron_address, decoded_amount

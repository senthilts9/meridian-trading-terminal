"""Step: Register a trading subkey against the EVM/SIWE main account.

Why this exists: an account onboarded via EVM key (SIWE/EIP-191) can read
account data and authenticate, but has no Starknet signing key of its own,
so it can't sign orders. Paradex's fix is a "subkey" -- a real Starknet
keypair registered to the main account specifically for order signing.

The SDK's own `ParadexEvm.create_trading_subkey()` helper is currently
broken against the live API (it omits the `evm_signature`/`siwe_message`
fields the server now requires for EIP-191 accounts -- confirmed against
both the released 0.6.3 package and the GitHub main branch). This script
builds that SIWE-signed payload by hand and calls the low-level
`create_subkey()` API method directly instead.
"""
import datetime
import secrets

from config import get_evm_client, logger
from eth_account import Account as EthAccount
from eth_account.messages import encode_defunct
from starknet_py.net.signer.key_pair import KeyPair

SUBKEY_EXPIRY_MINUTES = 5


def register_subkey(evm, l1_private_key: str, name: str = "lifecycle-bot"):
    l2_private_key_int = secrets.randbelow(2**251)
    key_pair = KeyPair.from_private_key(l2_private_key_int)
    pubkey_hex = hex(key_pair.public_key)

    domain = evm.account._siwe_domain()
    nonce = secrets.token_hex(16)
    now_dt = datetime.datetime.now(datetime.timezone.utc)
    expiry_dt = now_dt + datetime.timedelta(minutes=SUBKEY_EXPIRY_MINUTES)

    statement = f"Paradex Subkey Registration: {pubkey_hex.lower()}"
    siwe_message = (
        f"{domain} wants you to sign in with your Ethereum account:\n"
        f"{evm.account.evm_address}\n\n"
        f"{statement}\n\n"
        f"URI: https://{domain}\n"
        "Version: 1\n"
        f"Chain ID: {evm.account.config.l1_chain_id}\n"
        f"Nonce: {nonce}\n"
        f"Issued At: {now_dt.strftime('%Y-%m-%dT%H:%M:%SZ')}\n"
        f"Expiration Time: {expiry_dt.strftime('%Y-%m-%dT%H:%M:%SZ')}"
    )

    signed = EthAccount.from_key(l1_private_key).sign_message(encode_defunct(text=siwe_message))
    evm_signature = signed.signature.hex()
    if not evm_signature.startswith("0x"):
        evm_signature = "0x" + evm_signature

    payload = {
        "name": name,
        "public_key": pubkey_hex,
        "state": "active",
        "evm_signature": evm_signature,
        "siwe_message": siwe_message,
    }
    evm.api_client.create_subkey(payload)
    logger.info(f"Subkey registered: {pubkey_hex}")

    return {
        "subkey_l2_private_key": hex(l2_private_key_int),
        "main_l2_address": hex(evm.account.l2_address),
    }


def main():
    import os

    l1_private_key = os.getenv("L1_PRIVATE_KEY")
    evm = get_evm_client()
    result = register_subkey(evm, l1_private_key)
    print("\nAdd these to .env:\n")
    print(f"MAIN_L2_ADDRESS={result['main_l2_address']}")
    print(f"SUBKEY_L2_PRIVATE_KEY={result['subkey_l2_private_key']}")
    return result


if __name__ == "__main__":
    main()

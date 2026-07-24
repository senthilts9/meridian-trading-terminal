"""Generate a fresh, testnet-only Ethereum (L1) keypair.

Paradex derives your Starknet (L2) account deterministically from this L1
key the first time you authenticate (paradex_py handles onboarding for you).

This wallet is disposable: it holds no mainnet funds, no mnemonic to back up
elsewhere, and should never be reused for anything real.
"""
from eth_account import Account


def main():
    Account.enable_unaudited_hdwallet_features()
    acct = Account.create()

    print("Generated a new testnet-only wallet:\n")
    print(f"  L1_ADDRESS     = {acct.address}")
    print(f"  L1_PRIVATE_KEY = {acct.key.hex()}")
    print(
        "\nAdd these two lines to your .env file (copy .env.example -> .env first).\n"
        "Do NOT commit .env. Do NOT fund this address on Ethereum mainnet or any "
        "mainnet chain -- it is for Paradex TESTNET only."
    )


if __name__ == "__main__":
    main()

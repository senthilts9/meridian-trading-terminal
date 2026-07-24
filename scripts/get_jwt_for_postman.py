"""Print a short-lived JWT for manual use in Postman.

Paradex auth is a SIWE (EIP-191) signature over a challenge message --
Postman can't produce that signature itself. This script does the real
onboarding/auth via the SDK and prints the resulting bearer token so you
can paste it into the Postman `jwt_token` variable for the private-endpoint
requests (GET /account, /positions, /orders, /fills, etc.).

Note: the token expires in ~5 minutes; POST /orders in Postman still won't
work end-to-end because placing an order also requires a signed payload
(paradex_py signs it under the hood) -- use scripts/03_place_order.py for
that. This is mainly for exploring the read-only private GET endpoints
interactively in Postman.
"""
from config import get_authenticated_client, logger


def main():
    p = get_authenticated_client()
    jwt = p.account.jwt_token
    print("\nJWT (paste into Postman's jwt_token variable):\n")
    print(jwt)
    print("\nL2 address:", hex(p.account.l2_address))
    logger.info("Token expires in ~5 minutes.")


if __name__ == "__main__":
    main()

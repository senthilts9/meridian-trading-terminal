# Bug report draft — for Paradex Discord #developers

Copy-paste ready. Two independent issues hit while building a testnet integration with
`paradex-py` 0.6.3 (latest on PyPI) today (2026-07-24).

---

## Post 1 — Account deployment fails: proxy class not declared on testnet

**Environment:** `paradex-py==0.6.3`, testnet (`api.testnet.paradex.trade`)

Calling the standard onboarding path fails for *any* brand-new wallet:

```python
from paradex_py import Paradex
from paradex_py.environment import TESTNET
p = Paradex(env=TESTNET, l1_address="0x...", l1_private_key="0x...")
```

```
ValueError: ApiError(error='NOT_ONBOARDED', message='user has never called the /onboarding endpoint')
# after funding the wallet with Sepolia ETH and retrying onboarding:
POST /v1/onboarding -> 200 OK, but the account-deploy tx that follows REVERTS
```

Checked the revert directly against your Starknet RPC:

```
starknet_getTransactionReceipt(<the ACC_DEPLOY tx hash>)
revert_reason: "Class with hash 0x03530cc4759d78042f1b543bf797f5f3d647cde0388c33734cf91b7f7b9314a9 is not declared."
```

That hash is exactly what `GET /v1/system/config` returns as `paraclear_account_proxy_hash`.
I also checked `paraclear_account_hash` (`0x041cb0280eba...`) from the same config response
— **also not declared**. So the config is telling clients to deploy against classes that
don't exist on testnet right now.

**Workaround found:** `ParadexEvm` (SIWE/EIP-191) uses a *different* class,
`paraclear_evm_account_hash` (`0x073414441639...`), which **is** declared — account
creation, deploy tx, and the automatic test-USDC credit all worked cleanly through that
path. So this seems scoped to the native-Starknet-account proxy specifically, not testnet
deployment as a whole.

Happy to share the full transaction hash / repro script if useful.

---

## Post 2 — `ParadexEvm.create_trading_subkey()` fails against the live API

**Environment:** same as above; also checked against `main` on GitHub, same issue.

```python
evm = ParadexEvm(env=TESTNET, evm_address="0x...", evm_private_key="0x...")
evm.create_trading_subkey()
```

```
ValueError: ApiError(error='INVALID_REQUEST_PARAMETER', message='evm_signature is required for EIP-191 accounts')
```

Looking at the helper's payload, it only sends `{name, public_key, state}` — no
`evm_signature` / `siwe_message`, which `POST /v1/account/keys/subkeys` requires for
EIP-191-authenticated accounts per the docs at
`docs.paradex.trade/api/prod/subkey/register-subkey.md`.

**Workaround found:** building the SIWE message by hand (Statement =
`Paradex Subkey Registration: 0x<pubkey>`, lowercased, **plus an `Expiration Time` line —
required, but not mentioned by the doc snippet I could find**), signing it with
`personal_sign`, and calling the low-level `api_client.create_subkey()` directly with the
complete payload works fine. Looks like `create_trading_subkey()` just needs updating to
build the same payload it's already capable of sending.

---

Let me know if a minimal repro script would help track either of these down faster —
happy to share what I've got.

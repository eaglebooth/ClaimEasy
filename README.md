# ClaimEasy

ClaimEasy is a GenLayer-powered shipping damage compensation desk. It reads delivery evidence on-chain, asks an Intelligent Contract to judge whether damage happened during shipping, and releases fair refunds from a merchant insurance pool.

## Why It Needs GenLayer

Shipping damage claims are subjective and money-bearing: the contract must compare unboxing evidence, shipper proof, tracking pages, and merchant policy language. A normal smart contract cannot read this web evidence or reason about whether package damage was caused by the carrier. ClaimEasy dies without GenLayer.

## Architecture

- `contracts/ClaimEasy.py` stores an insurance fund, claim lifecycle, evidence URLs, AI decision scores, and payout state.
- `evaluate_claim` uses `gl.nondet.web.render` to read tracking, unbox, delivery slip, and policy evidence on-chain.
- The AI verdict uses `gl.eq_principle.prompt_comparative` so validators compare the real decision, refund amount, and score bands instead of byte-identical free-text wording.
- `frontend/` is a Next.js app using `genlayer-js` for wallet connection, reads, writes, verdict display, and payout actions.

## Contract Flow

1. Initialize the merchant shipping insurance fund.
2. File a damaged-delivery claim.
3. Attach tracking, unbox, delivery slip, and policy evidence URLs.
4. Run AI review inside the Intelligent Contract.
5. Release compensation if the on-chain verdict approves payout.

## Local Setup

```bash
python -m unittest discover -s tests
cd frontend
npm install
npm run dev
```

Create `frontend/.env.local`:

```bash
NEXT_PUBLIC_CONTRACT_ADDRESS=0x736552c8a46780c9AD02Ae80c5B875fE6789864B
NEXT_PUBLIC_NETWORK=testnetAsimov
NEXT_PUBLIC_GENLAYER_RPC=
```

## Deploy

```bash
python -c "import ast; ast.parse(open('contracts/ClaimEasy.py', encoding='utf-8').read())"
genlayer lint contracts/ClaimEasy.py
genlayer deploy contracts/ClaimEasy.py --name ClaimEasy
```

After deployment, set `NEXT_PUBLIC_CONTRACT_ADDRESS` and deploy `frontend/` to Vercel.

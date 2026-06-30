# ClaimEasy Deployment Notes

1. Validate the contract:

```bash
python -c "import ast; ast.parse(open('contracts/ClaimEasy.py', encoding='utf-8').read())"
genlayer lint contracts/ClaimEasy.py
```

2. Deploy in GenLayer Studio or CLI:

```bash
genlayer deploy contracts/ClaimEasy.py --name ClaimEasy
```

3. Add the returned address to `frontend/.env.local`:

```bash
NEXT_PUBLIC_CONTRACT_ADDRESS=0x...
NEXT_PUBLIC_NETWORK=testnetAsimov
```

4. Run the connected frontend:

```bash
cd frontend
npm install
npm run dev
```

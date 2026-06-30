"use client";

import { motion } from "framer-motion";
import {
  ArrowRight,
  Box,
  CheckCircle2,
  CircleDollarSign,
  ClipboardCheck,
  FileImage,
  Link2,
  PackageCheck,
  Radar,
  ReceiptText,
  RefreshCw,
  ShieldCheck,
  Sparkles,
  Truck,
  Wallet,
} from "lucide-react";
import { useMemo, useState } from "react";
import { connectWallet, readContract, writeContract } from "@/lib/genlayer";

type ClaimDraft = {
  ownerWallet: string;
  fundBalance: string;
  maxPayout: string;
  minConfidence: string;
  claimId: string;
  orderId: string;
  buyerWallet: string;
  merchantWallet: string;
  itemTitle: string;
  orderValue: string;
  requestedRefund: string;
  trackingUrl: string;
  unboxUrl: string;
  deliverySlipUrl: string;
  policyUrl: string;
};

const defaultDraft: ClaimDraft = {
  ownerWallet: "0x0000000000000000000000000000000000000F01",
  fundBalance: "250000",
  maxPayout: "35000",
  minConfidence: "72",
  claimId: "0",
  orderId: "CLM-8801",
  buyerWallet: "0x0000000000000000000000000000000000000B17",
  merchantWallet: "0x0000000000000000000000000000000000000A24",
  itemTitle: "Ceramic espresso machine",
  orderValue: "49900",
  requestedRefund: "21000",
  trackingUrl: "https://example.com/claimeasy/tracking-clm-8801",
  unboxUrl: "https://example.com/claimeasy/unbox-video-clm-8801",
  deliverySlipUrl: "https://example.com/claimeasy/shipper-slip-clm-8801",
  policyUrl: "https://example.com/claimeasy/merchant-policy",
};

const evidence = [
  {
    key: "trackingUrl",
    label: "Tracking timeline",
    icon: Truck,
    note: "Carrier scans, handoff gaps, and delivery timestamp.",
  },
  {
    key: "unboxUrl",
    label: "Unbox video",
    icon: PackageCheck,
    note: "Seal condition before opening and first visible damage.",
  },
  {
    key: "deliverySlipUrl",
    label: "Shipper proof",
    icon: FileImage,
    note: "Slip photo, delivery note, and package exterior.",
  },
  {
    key: "policyUrl",
    label: "Shop policy",
    icon: ReceiptText,
    note: "Coverage limits and eligible carrier fault rules.",
  },
] as const;

type Decision = {
  status: string;
  decision: string;
  refund: string;
  fault: string;
  integrity: string;
  confidence: string;
  reason: string;
};

function short(value: unknown) {
  const text = String(value || "");
  if (text.length <= 14) return text;
  return `${text.slice(0, 6)}...${text.slice(-4)}`;
}

function money(cents: string) {
  const value = Number(cents || "0") / 100;
  return value.toLocaleString("en-US", { style: "currency", currency: "USD" });
}

function parseJson(value: unknown) {
  try {
    return JSON.parse(String(value)) as Record<string, string>;
  } catch {
    return {};
  }
}

export default function Home() {
  const [draft, setDraft] = useState(defaultDraft);
  const [wallet, setWallet] = useState("");
  const [busy, setBusy] = useState(false);
  const [status, setStatus] = useState("Ready. Connected to ClaimEasy contract on GenLayer testnet.");
  const [decision, setDecision] = useState<Decision>({
    status: "No claim yet",
    decision: "PENDING",
    refund: "0",
    fault: "0",
    integrity: "0",
    confidence: "0",
    reason: "The GenLayer shipping jury memo appears here after review.",
  });
  const [fund, setFund] = useState({
    balance: "0",
    paid: "0",
    reserved: "0",
    maxPayout: "0",
  });

  const configured = useMemo(() => Boolean(process.env.NEXT_PUBLIC_CONTRACT_ADDRESS), []);

  function setField(key: keyof ClaimDraft, value: string) {
    setDraft((current) => ({ ...current, [key]: value }));
  }

  async function handleConnect() {
    const result = await connectWallet();
    if (result.success) {
      const account = String(result.data);
      setWallet(account);
      setStatus(`Wallet connected: ${short(account)}`);
    } else {
      setStatus(result.error || "Wallet connection failed");
    }
  }

  async function refreshFund() {
    const result = await readContract("get_fund_state");
    if (!result.success) {
      setStatus(result.error || "Fund state unavailable");
      return;
    }
    const parsed = parseJson(result.data);
    setFund({
      balance: parsed.balance || "0",
      paid: parsed.paid || "0",
      reserved: parsed.reserved || "0",
      maxPayout: parsed.max_payout || "0",
    });
    setStatus("Fund state refreshed from contract.");
  }

  async function readDecision() {
    const result = await readContract("get_decision", [BigInt(draft.claimId || "0")]);
    if (!result.success) {
      setStatus(result.error || "Decision unavailable");
      return;
    }
    const parsed = parseJson(result.data);
    setDecision({
      status: parsed.status || "UNKNOWN",
      decision: parsed.decision || "PENDING",
      refund: parsed.approved_refund || "0",
      fault: parsed.carrier_fault_score || "0",
      integrity: parsed.packaging_integrity_score || "0",
      confidence: parsed.confidence_score || "0",
      reason: parsed.reason || "No AI report stored yet.",
    });
    setStatus("Decision refreshed from contract.");
  }

  async function runWrite(label: string, functionName: string, args: unknown[], after?: () => Promise<void>) {
    setBusy(true);
    setStatus(label);
    const result = await writeContract(functionName, args);
    setBusy(false);
    if (result.success) {
      setStatus(`Done. Tx ${short(result.hash)} ${result.data ? `- ${String(result.data)}` : ""}`);
      if (after) await after();
    } else {
      setStatus(result.error || `${functionName} failed`);
    }
  }

  async function initializeFund() {
    await runWrite("Initializing carrier insurance fund...", "initialize_fund", [
      draft.ownerWallet,
      BigInt(draft.fundBalance || "0"),
      BigInt(draft.maxPayout || "0"),
      BigInt(draft.minConfidence || "0"),
    ], refreshFund);
  }

  async function fileClaim() {
    await runWrite("Filing damaged delivery claim...", "file_claim", [
      draft.orderId,
      draft.buyerWallet,
      draft.merchantWallet,
      draft.itemTitle,
      BigInt(draft.orderValue || "0"),
      BigInt(draft.requestedRefund || "0"),
    ]);
  }

  async function attachEvidence() {
    await runWrite("Attaching web evidence to the claim...", "attach_evidence", [
      BigInt(draft.claimId || "0"),
      draft.trackingUrl,
      draft.unboxUrl,
      draft.deliverySlipUrl,
      draft.policyUrl,
    ]);
  }

  async function evaluateClaim() {
    await runWrite("Running GenLayer shipping damage jury...", "evaluate_claim", [
      BigInt(draft.claimId || "0"),
    ], readDecision);
  }

  async function releaseCompensation() {
    await runWrite("Releasing approved compensation...", "release_compensation", [
      BigInt(draft.claimId || "0"),
    ], async () => {
      await refreshFund();
      await readDecision();
    });
  }

  return (
    <main className="page">
      <div className="shape shape-one" />
      <div className="shape shape-two" />
      <div className="browser-shell">
        <nav className="site-nav">
          <a className="brand" href="#top">
            <span><Box size={26} /></span>
            ClaimEasy
          </a>
          <div>
            <a href="#desk">Claim desk</a>
            <a href="#evidence">Evidence reel</a>
            <a href="#verdict">Verdict</a>
          </div>
          <button className="nav-wallet" type="button" onClick={handleConnect}>
            <Wallet size={18} />
            {wallet ? short(wallet) : "Connect wallet"}
          </button>
        </nav>

        <section className="hero" id="top">
          <motion.div
            className="hero-copy"
            initial={{ opacity: 0, y: 24 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.65, delay: 0.08 }}
          >
            <p className="eyebrow"><Sparkles size={16} /> GenLayer shipping compensation</p>
            <h1>ClaimEasy for damaged deliveries.</h1>
            <p>
              Verify unbox evidence, shipper proof, and policy pages inside an Intelligent Contract.
              When carrier fault is clear, the shop insurance pool pays instantly.
            </p>
            <div className="hero-actions">
              <a className="primary-cta" href="#desk">
                Open claim desk <ArrowRight size={18} />
              </a>
              <button className="secondary-cta" type="button" onClick={refreshFund}>
                Sync fund <RefreshCw size={17} />
              </button>
            </div>
          </motion.div>
        </section>

        <section className="demo-window">
          <div className="window-toolbar">
            <span>Live compensation console</span>
            <p>{configured ? "Contract configured" : "Waiting for contract address"}</p>
          </div>

          <div className="fund-strip" id="desk">
            <div className="fund-card">
              <small>Insurance fund</small>
              <strong>{money(fund.balance || draft.fundBalance)}</strong>
              <input value={draft.fundBalance} onChange={(event) => setField("fundBalance", event.target.value)} />
            </div>
            <div className="fund-card coral">
              <small>Max payout</small>
              <strong>{money(draft.maxPayout)}</strong>
              <input value={draft.maxPayout} onChange={(event) => setField("maxPayout", event.target.value)} />
            </div>
            <div className="fund-card">
              <small>Min confidence</small>
              <strong>{draft.minConfidence}%</strong>
              <input value={draft.minConfidence} onChange={(event) => setField("minConfidence", event.target.value)} />
            </div>
            <button className="dark-action" type="button" disabled={busy} onClick={initializeFund}>
              Prime fund <ShieldCheck size={18} />
            </button>
          </div>

          <div className="claim-board">
            <div className="parcel-card">
              <div className="parcel-top">
                <span>Claim capsule</span>
                <strong>#{draft.orderId}</strong>
              </div>
              <label>
                Damaged item
                <input value={draft.itemTitle} onChange={(event) => setField("itemTitle", event.target.value)} />
              </label>
              <div className="parcel-grid">
                <label>
                  Order value
                  <input value={draft.orderValue} onChange={(event) => setField("orderValue", event.target.value)} />
                </label>
                <label>
                  Refund ask
                  <input value={draft.requestedRefund} onChange={(event) => setField("requestedRefund", event.target.value)} />
                </label>
                <label>
                  Claim ID
                  <input value={draft.claimId} onChange={(event) => setField("claimId", event.target.value)} />
                </label>
              </div>
              <div className="wallet-stack">
                <label>Buyer <input value={draft.buyerWallet} onChange={(event) => setField("buyerWallet", event.target.value)} /></label>
                <label>Merchant <input value={draft.merchantWallet} onChange={(event) => setField("merchantWallet", event.target.value)} /></label>
                <label>Fund owner <input value={draft.ownerWallet} onChange={(event) => setField("ownerWallet", event.target.value)} /></label>
              </div>
              <button className="primary-cta full" type="button" disabled={busy} onClick={fileClaim}>
                File damaged delivery <ClipboardCheck size={18} />
              </button>
            </div>

            <div className="evidence-dock" id="evidence">
              {evidence.map((item) => {
                const Icon = item.icon;
                return (
                  <article key={item.key}>
                    <div><Icon size={25} /><span>{item.label}</span></div>
                    <p>{item.note}</p>
                    <label>
                      <Link2 size={15} />
                      <input
                        value={draft[item.key]}
                        onChange={(event) => setField(item.key, event.target.value)}
                        aria-label={item.label}
                      />
                    </label>
                  </article>
                );
              })}
              <button className="secondary-cta full" type="button" disabled={busy} onClick={attachEvidence}>
                Attach evidence packet <FileImage size={18} />
              </button>
            </div>
          </div>

          <div className="verdict-row" id="verdict">
            <div className="verdict-copy">
              <span><Radar size={17} /> AI jury output</span>
              <h2>{decision.decision}</h2>
              <p>{decision.reason}</p>
              <div className="status-line">{busy ? "Consensus pending..." : status}</div>
            </div>
            <div className="meters">
              <div>
                <small>Carrier fault</small>
                <strong>{decision.fault}%</strong>
                <span><i style={{ width: `${decision.fault}%` }} /></span>
              </div>
              <div>
                <small>Seal intact</small>
                <strong>{decision.integrity}%</strong>
                <span><i style={{ width: `${decision.integrity}%` }} /></span>
              </div>
              <div>
                <small>Confidence</small>
                <strong>{decision.confidence}%</strong>
                <span><i style={{ width: `${decision.confidence}%` }} /></span>
              </div>
            </div>
            <div className="payout-ticket">
              <small>Approved compensation</small>
              <strong>{money(decision.refund)}</strong>
              <button className="primary-cta full" type="button" disabled={busy} onClick={evaluateClaim}>
                Run AI review <Sparkles size={18} />
              </button>
              <button className="dark-action full" type="button" disabled={busy} onClick={releaseCompensation}>
                Release payout <CircleDollarSign size={18} />
              </button>
              <button className="secondary-cta full" type="button" onClick={readDecision}>
                Read verdict <CheckCircle2 size={18} />
              </button>
            </div>
          </div>
        </section>

        <footer className="submission-footer">
          <div>
            <span>Why GenLayer</span>
            <strong>ClaimEasy dies without on-chain web evidence and AI judgment.</strong>
          </div>
          <div className="footer-steps">
            <p><PackageCheck size={16} /> File claim</p>
            <p><FileImage size={16} /> Attach evidence</p>
            <p><CircleDollarSign size={16} /> Pay approved refund</p>
          </div>
          <div className="footer-status">
            <small>{configured ? "Ready for deployed contract" : "Contract address pending"}</small>
            <span>{configured ? "Testnet mode" : "Set NEXT_PUBLIC_CONTRACT_ADDRESS"}</span>
          </div>
        </footer>
      </div>
    </main>
  );
}

import { useEffect, useState } from "react";
import { deposit, getBalance, getTransactions, withdraw } from "./api";
import { formatRelativeTime } from "./format";

const TX_LABELS = {
  deposit: "Deposit",
  withdrawal: "Withdrawal",
  wager_lock: "Wager Stake",
  wager_payout: "Wager Payout",
  wager_refund: "Wager Refund",
};

export default function Wallet({ onBalanceChanged }) {
  const [balance, setBalance] = useState(null);
  const [transactions, setTransactions] = useState([]);
  const [amount, setAmount] = useState("");
  const [error, setError] = useState(null);

  const parsedAmount = Number(amount);
  const isValidAmount = amount.trim() !== "" && Number.isFinite(parsedAmount) && parsedAmount > 0;

  async function refresh() {
    const [balanceData, txData] = await Promise.all([getBalance(), getTransactions()]);
    setBalance(balanceData.balance);
    setTransactions(txData);
  }

  useEffect(() => {
    refresh();
  }, []);

  async function handleDeposit() {
    if (!isValidAmount) return;
    setError(null);
    try {
      await deposit(parsedAmount);
      setAmount("");
      await refresh();
      onBalanceChanged?.();
    } catch (err) {
      setError(err.message);
    }
  }

  async function handleWithdraw() {
    if (!isValidAmount) return;
    setError(null);
    try {
      await withdraw(parsedAmount);
      setAmount("");
      await refresh();
      onBalanceChanged?.();
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <div className="card">
      <h2>Wallet</h2>
      <p className="balance">Balance: ${balance ?? "..."}</p>
      <div className="row">
        <input
          type="number"
          min="0"
          step="0.01"
          placeholder="Amount"
          value={amount}
          onChange={(e) => setAmount(e.target.value)}
        />
        <button onClick={handleDeposit} disabled={!isValidAmount}>
          Deposit
        </button>
        <button onClick={handleWithdraw} disabled={!isValidAmount}>
          Withdraw
        </button>
      </div>
      {amount.trim() !== "" && !isValidAmount && (
        <p className="error">Enter an amount greater than 0.</p>
      )}
      {error && <p className="error">{error}</p>}
      <h3>Transactions</h3>
      {transactions.length === 0 ? (
        <p className="empty-state">No transactions yet.</p>
      ) : (
        <ul className="list">
          {transactions.map((tx) => (
            <li key={tx.id} className="tx-row">
              <span className="tx-badge">{TX_LABELS[tx.type] ?? tx.type}</span>
              <span className="tx-main">{tx.wager_id ? `Wager #${tx.wager_id}` : ""}</span>
              <span className={Number(tx.amount) >= 0 ? "tx-amount matched" : "tx-amount error"}>
                {Number(tx.amount) >= 0 ? "+" : "-"}${Math.abs(Number(tx.amount)).toFixed(2)}
              </span>
              <span className="tx-time">{formatRelativeTime(tx.created_at)}</span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

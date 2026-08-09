import { useEffect, useState } from "react";
import { deposit, getBalance, getTransactions, withdraw } from "./api";

export default function Wallet() {
  const [balance, setBalance] = useState(null);
  const [transactions, setTransactions] = useState([]);
  const [amount, setAmount] = useState("");
  const [error, setError] = useState(null);

  async function refresh() {
    const [balanceData, txData] = await Promise.all([getBalance(), getTransactions()]);
    setBalance(balanceData.balance);
    setTransactions(txData);
  }

  useEffect(() => {
    refresh();
  }, []);

  async function handleDeposit() {
    setError(null);
    try {
      await deposit(Number(amount));
      setAmount("");
      await refresh();
    } catch (err) {
      setError(err.message);
    }
  }

  async function handleWithdraw() {
    setError(null);
    try {
      await withdraw(Number(amount));
      setAmount("");
      await refresh();
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
        <button onClick={handleDeposit}>Deposit</button>
        <button onClick={handleWithdraw}>Withdraw</button>
      </div>
      {error && <p className="error">{error}</p>}
      <h3>Transactions</h3>
      {transactions.length === 0 ? (
        <p className="empty-state">No transactions yet.</p>
      ) : (
        <ul className="list">
          {transactions.map((tx) => (
            <li key={tx.id}>
              {tx.type} — {tx.amount > 0 ? "+" : ""}
              {tx.amount} ({new Date(tx.created_at).toLocaleString()})
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

"use client";

import { useEffect, useState } from "react";
import { useAuthStore } from "@/lib/auth";
import api from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { CreditCard, TrendingUp } from "lucide-react";
import { formatDistanceToNow } from "date-fns";

const PACKAGES = [
  { id: "100", name: "Starter", price: "$9", credits: 100, description: "Perfect for getting started" },
  { id: "500", name: "Growth", price: "$39", credits: 500, description: "For regular content creators", popular: true },
  { id: "2000", name: "Pro", price: "$99", credits: 2000, description: "For teams and agencies" },
];

interface Transaction {
  id: string;
  amount: number;
  type: string;
  description: string;
  balance_after: number;
  created_at: string;
}

export default function CreditsPage() {
  const { activeWorkspace } = useAuthStore();
  const [balance, setBalance] = useState<number | null>(null);
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [loading, setLoading] = useState<string | null>(null);

  useEffect(() => {
    if (!activeWorkspace) return;
    Promise.all([
      api.get(`/workspaces/${activeWorkspace.id}/credits/balance`),
      api.get(`/workspaces/${activeWorkspace.id}/credits/history`),
    ]).then(([b, t]) => {
      setBalance(b.data.balance);
      setTransactions(t.data);
    }).catch(() => {});
  }, [activeWorkspace]);

  const handleBuy = async (pkg: string) => {
    if (!activeWorkspace) return;
    setLoading(pkg);
    try {
      const { data } = await api.post(`/workspaces/${activeWorkspace.id}/credits/checkout`, { package: pkg });
      window.location.href = data.checkout_url;
    } catch {
      setLoading(null);
      alert("Failed to create checkout session");
    }
  };

  return (
    <div className="p-6 max-w-3xl mx-auto">
      <h1 className="text-2xl font-bold mb-6">Credits & Billing</h1>

      <Card className="mb-6">
        <CardContent className="pt-4 pb-4">
          <div className="flex items-center gap-3">
            <div className="p-3 rounded-xl bg-zinc-100">
              <CreditCard className="h-6 w-6 text-zinc-700" />
            </div>
            <div>
              <p className="text-sm text-zinc-500">Current balance</p>
              <p className="text-3xl font-bold">{balance ?? "—"} <span className="text-base font-normal text-zinc-400">credits</span></p>
            </div>
          </div>
        </CardContent>
      </Card>

      <h2 className="font-semibold text-zinc-900 mb-3">Buy credits</h2>
      <div className="grid grid-cols-3 gap-4 mb-8">
        {PACKAGES.map((pkg) => (
          <Card key={pkg.id} className={pkg.popular ? "border-zinc-900" : ""}>
            <CardContent className="pt-4 pb-4 text-center">
              {pkg.popular && <Badge className="mb-2">Most popular</Badge>}
              <p className="font-bold text-lg">{pkg.name}</p>
              <p className="text-3xl font-bold mt-1">{pkg.price}</p>
              <p className="text-sm text-zinc-500 mt-1">{pkg.credits} credits</p>
              <p className="text-xs text-zinc-400 mt-1 mb-3">{pkg.description}</p>
              <Button
                className="w-full"
                variant={pkg.popular ? "default" : "outline"}
                onClick={() => handleBuy(pkg.id)}
                disabled={loading === pkg.id}
              >
                {loading === pkg.id ? "Redirecting..." : "Buy now"}
              </Button>
            </CardContent>
          </Card>
        ))}
      </div>

      <h2 className="font-semibold text-zinc-900 mb-3">Transaction history</h2>
      {transactions.length === 0 ? (
        <p className="text-zinc-400 text-sm">No transactions yet.</p>
      ) : (
        <div className="space-y-1">
          {transactions.map((tx) => (
            <div key={tx.id} className="flex items-center justify-between py-2.5 border-b border-zinc-100 last:border-0">
              <div>
                <p className="text-sm">{tx.description}</p>
                <p className="text-xs text-zinc-400">{formatDistanceToNow(new Date(tx.created_at))} ago</p>
              </div>
              <div className="text-right">
                <p className={`text-sm font-medium ${tx.amount > 0 ? "text-green-600" : "text-red-500"}`}>
                  {tx.amount > 0 ? "+" : ""}{tx.amount}
                </p>
                <p className="text-xs text-zinc-400">balance: {tx.balance_after}</p>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

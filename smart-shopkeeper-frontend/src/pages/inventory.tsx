import { useState } from "react";
import { Boxes, Tags } from "lucide-react";
import { Button } from "@/components/ui/button";
import { api, type InventoryCheck } from "@/lib/api";
import {
  Badge,
  Field,
  Notice,
  PageHeader,
  Panel,
  StatCard,
  fmt,
  inputCls,
  useAction,
  useAsync,
} from "@/components/ui-bits";

function StockRow({
  name,
  stock,
  onChanged,
  onCheck,
}: {
  name: string;
  stock: number;
  onChanged: () => void;
  onCheck: (r: InventoryCheck) => void;
}) {
  const [qty, setQty] = useState("");
  const [learn, setLearn] = useState(false);
  const { busy, msg, run } = useAction();
  const n = Number(qty);

  return (
    <div className="border-border flex flex-col gap-3 rounded-lg border p-3">
      <div className="flex items-center justify-between">
        <span className="font-medium">{name}</span>
        <span className="text-lg font-semibold tabular-nums">
          {fmt(stock, 0)} <span className="text-muted-foreground text-sm font-normal">in stock</span>
        </span>
      </div>
      <div className="flex flex-wrap items-center gap-2">
        <input
          className={`${inputCls} max-w-32`}
          type="number"
          min={0}
          placeholder="Qty"
          value={qty}
          onChange={(e) => setQty(e.target.value)}
        />
        <Button
          variant="secondary"
          disabled={busy || !qty || n < 0}
          onClick={async () => {
            await run(() => api.inventory.setStock(name, n), "Stock updated");
            onChanged();
          }}
        >
          Set / Restock
        </Button>
        <Button
          disabled={busy || !qty || n <= 0}
          onClick={async () => {
            await run(() => api.inventory.sell(name, n, learn), (r) => r.message);
            setQty("");
            onChanged();
          }}
        >
          Sell
        </Button>
        <Button
          variant="secondary"
          disabled={busy}
          onClick={async () => {
            const r = await run(() => api.inventory.check(name));
            if (r) onCheck(r);
          }}
        >
          Check reorder
        </Button>
        <Button
          variant="ghost"
          disabled={busy}
          className="text-red-600"
          onClick={async () => {
            if (confirm(`Remove "${name}" and its stock?`)) {
              await run(() => api.categories.remove(name));
              onChanged();
            }
          }}
        >
          Remove
        </Button>
        <label className="text-muted-foreground flex items-center gap-1.5 text-xs">
          <input type="checkbox" checked={learn} onChange={(e) => setLearn(e.target.checked)} />
          Learn from this sale (retrains model)
        </label>
      </div>
      <Notice msg={msg} />
    </div>
  );
}

export default function Inventory() {
  const stock = useAsync(api.inventory.stock);
  const [name, setName] = useState("");
  const [initial, setInitial] = useState("0");
  const [check, setCheck] = useState<InventoryCheck | null>(null);
  const add = useAction();

  const rows = Object.entries(stock.data?.stock ?? {});
  const tone = (s: string) => (s.includes("CRITICALLY") ? "bad" : s.includes("1 week") ? "warn" : "ok");

  return (
    <>
      <PageHeader
        title="Inventory"
        subtitle="Categories and their stock are connected: adding a category creates its stock record."
      />
      <div className="mb-8 grid grid-cols-1 gap-3 sm:grid-cols-2">
        <StatCard icon={Tags} iconClass="text-[#A855F7]" label="Categories" value={String(rows.length)} />
        <StatCard icon={Boxes} iconClass="text-[#3B82F6]" label="Total stock" value={fmt(stock.data?.total_stock, 0)} />
      </div>

      <div className="grid grid-cols-1 gap-8 lg:grid-cols-3">
        <Panel title="Add Category">
          <form
            className="flex flex-col gap-3"
            onSubmit={async (e) => {
              e.preventDefault();
              const r = await add.run(
                () => api.categories.add(name.trim(), Number(initial)),
                (x) => x.message ?? "Category added",
              );
              if (r) {
                setName("");
                setInitial("0");
                stock.reload();
              }
            }}
          >
            <Field label="Name">
              <input className={inputCls} value={name} onChange={(e) => setName(e.target.value)} placeholder="Milk" required />
            </Field>
            <Field label="Starting stock">
              <input
                className={inputCls}
                type="number"
                min={0}
                value={initial}
                onChange={(e) => setInitial(e.target.value)}
              />
            </Field>
            <Button type="submit" className="h-11" disabled={add.busy || !name.trim()}>
              Add category
            </Button>
            <Notice msg={add.msg} />
          </form>
        </Panel>

        <div className="flex flex-col gap-4 lg:col-span-2">
          <h2 className="text-lg font-medium">Stock per category</h2>
          {stock.error && <Notice msg={{ kind: "err", text: stock.error }} />}
          {rows.length === 0 && !stock.loading && !stock.error && (
            <p className="text-muted-foreground text-sm">No categories yet.</p>
          )}
          {rows.map(([n, s]) => (
            <StockRow key={n} name={n} stock={s} onChanged={stock.reload} onCheck={setCheck} />
          ))}
          {check && (
            <Panel title={`Reorder check${check.category ? `: ${check.category}` : ""}`}>
              <div className="flex flex-col gap-2 text-sm">
                <div className="flex flex-wrap items-center gap-2">
                  <Badge tone={tone(check.status)}>{check.status}</Badge>
                  <span>{check.action_note}</span>
                </div>
                <p className="text-muted-foreground">
                  Stock {fmt(check.current_stock, 0)} · weekly demand {fmt(check.weekly_demand, 0)} · monthly demand{" "}
                  {fmt(check.monthly_demand, 0)} · reorder {check.reorder_units}
                </p>
                <p className="text-muted-foreground text-xs">
                  Demand is forecast for the whole shop, so single-category advice is approximate.
                </p>
              </div>
            </Panel>
          )}
        </div>
      </div>
    </>
  );
}

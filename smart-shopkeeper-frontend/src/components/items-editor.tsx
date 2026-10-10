import { Plus, Trash2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import type { OrderItem } from "@/lib/api";
import { fmt, inputCls } from "./ui-bits";

export const emptyItem = (): OrderItem => ({ name: "", quantity: 1, unit_price: 0, unit_weight_kg: 0 });

export function summarize(items: OrderItem[]) {
  return items.reduce(
    (a, i) => ({
      count: a.count + i.quantity,
      weight: a.weight + i.quantity * i.unit_weight_kg,
      price: a.price + i.quantity * i.unit_price,
    }),
    { count: 0, weight: 0, price: 0 },
  );
}

export function ItemsEditor({ items, onChange }: { items: OrderItem[]; onChange: (items: OrderItem[]) => void }) {
  const set = (idx: number, patch: Partial<OrderItem>) =>
    onChange(items.map((it, i) => (i === idx ? { ...it, ...patch } : it)));
  const totals = summarize(items);

  return (
    <div className="flex flex-col gap-3">
      {items.length > 0 && (
        <div className="text-muted-foreground hidden grid-cols-[1fr_80px_100px_100px_40px] gap-2 text-xs font-medium sm:grid">
          <span>Item</span>
          <span>Qty</span>
          <span>Unit price</span>
          <span>Unit kg</span>
          <span />
        </div>
      )}
      {items.map((it, idx) => (
        <div key={idx} className="grid grid-cols-3 gap-2 sm:grid-cols-[1fr_80px_100px_100px_40px]">
          <input
            className={`${inputCls} col-span-3 sm:col-span-1`}
            placeholder="Milk 1L"
            value={it.name}
            onChange={(e) => set(idx, { name: e.target.value })}
          />
          <input
            className={inputCls}
            type="number"
            min={1}
            value={it.quantity}
            onChange={(e) => set(idx, { quantity: Math.max(1, Number(e.target.value)) })}
          />
          <input
            className={inputCls}
            type="number"
            min={0}
            value={it.unit_price}
            onChange={(e) => set(idx, { unit_price: Number(e.target.value) })}
          />
          <input
            className={inputCls}
            type="number"
            min={0}
            step="0.1"
            value={it.unit_weight_kg}
            onChange={(e) => set(idx, { unit_weight_kg: Number(e.target.value) })}
          />
          <Button
            type="button"
            variant="ghost"
            size="icon"
            aria-label="Remove item"
            onClick={() => onChange(items.filter((_, i) => i !== idx))}
          >
            <Trash2 />
          </Button>
        </div>
      ))}
      <div className="flex flex-wrap items-center justify-between gap-2">
        <Button type="button" variant="secondary" onClick={() => onChange([...items, emptyItem()])}>
          <Plus /> Add item
        </Button>
        <span className="text-muted-foreground text-sm">
          {fmt(totals.count, 0)} items · {fmt(totals.weight, 2)} kg · {fmt(totals.price, 0)} total
        </span>
      </div>
    </div>
  );
}

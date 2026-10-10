import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { api, type Order, type OrderItem } from "@/lib/api";
import { ItemsEditor, emptyItem } from "@/components/items-editor";
import {
  Badge,
  Field,
  Notice,
  PageHeader,
  Panel,
  SectionTitle,
  fmt,
  inputCls,
  useAction,
  useAsync,
} from "@/components/ui-bits";

const STATUSES = ["Driver Assigned", "Picked Up", "On the Way", "Delivered", "Cancelled"];

function OrderCard({ order, onChanged }: { order: Order; onChanged: () => void }) {
  const [status, setStatus] = useState(order.status);
  const [mins, setMins] = useState("");
  const { busy, msg, run } = useAction();
  const closed = ["Delivered", "Cancelled"].includes(order.status);

  return (
    <Card className="border-border gap-3 rounded-lg border p-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <span className="font-medium">{order.tracking_id}</span>
        <Badge tone={order.status === "Delivered" ? "ok" : order.status === "Cancelled" ? "bad" : "warn"}>
          {order.status}
        </Badge>
      </div>
      <p className="text-muted-foreground text-sm">
        Rider {order.driver?.name} ({order.driver?.vehicle_type}) · {fmt(order.distance_km)} km · ETA{" "}
        {fmt(order.estimated_minutes)} min · {fmt(order.remaining_minutes)} min left
      </p>
      <p className="text-sm">
        {order.items_delivered ?? 0} delivered / {order.items_remaining ?? 0} remaining ·{" "}
        {fmt(order.total_weight_kg, 2)} kg · {fmt(order.total_price, 0)}
      </p>
      <div className="flex flex-wrap gap-2">
        {(order.items ?? []).map((it) => (
          <button
            key={it.name}
            type="button"
            disabled={closed || it.delivered || busy}
            title={it.delivered ? "Delivered" : "Click to mark as handed over"}
            onClick={async () => {
              await run(
                () => api.orders.status(order.tracking_id, order.status, undefined, [it.name]),
                "Item marked delivered",
              );
              onChanged();
            }}
            className={`rounded-lg px-3 py-1.5 text-sm ${
              it.delivered
                ? "bg-green-500/10 text-green-700 line-through dark:text-green-400"
                : "bg-secondary hover:bg-muted cursor-pointer"
            }`}
          >
            {it.quantity}× {it.name}
          </button>
        ))}
      </div>
      {!closed && (
        <div className="flex flex-wrap items-center gap-2">
          <select className={`${inputCls} max-w-48`} value={status} onChange={(e) => setStatus(e.target.value)}>
            {STATUSES.map((s) => (
              <option key={s}>{s}</option>
            ))}
          </select>
          {status === "Delivered" && (
            <input
              className={`${inputCls} max-w-40`}
              type="number"
              min={0}
              placeholder="Actual minutes"
              value={mins}
              onChange={(e) => setMins(e.target.value)}
            />
          )}
          <Button
            disabled={busy || status === order.status}
            onClick={async () => {
              await run(
                () => api.orders.status(order.tracking_id, status, mins ? Number(mins) : undefined),
                "Status updated",
              );
              onChanged();
            }}
          >
            Update
          </Button>
        </div>
      )}
      <Notice msg={msg} />
    </Card>
  );
}

export default function Orders() {
  const orders = useAsync(api.orders.list);
  const [distance, setDistance] = useState("5");
  const [traffic, setTraffic] = useState("5");
  const [items, setItems] = useState<OrderItem[]>([emptyItem()]);
  const create = useAction();
  const [created, setCreated] = useState<Order | null>(null);

  const list: Order[] = (orders.data ? Object.values(orders.data) : []).sort((a, b) =>
    b.created_at.localeCompare(a.created_at),
  );
  const validItems = items.filter((i) => i.name.trim());

  return (
    <>
      <PageHeader
        title="Orders"
        subtitle="Create deliveries with their items; a rider who can carry the load is assigned automatically."
      />
      <div className="grid grid-cols-1 gap-8 xl:grid-cols-5">
        <Panel title="New Order" className="xl:col-span-2">
          <form
            className="flex flex-col gap-4"
            onSubmit={async (e) => {
              e.preventDefault();
              const r = await create.run(
                () => api.orders.create(Number(distance), Number(traffic), validItems),
                (o) => `Order ${o.tracking_id} created. Rider: ${o.driver.name}, ETA ${fmt(o.estimated_minutes)} min.`,
              );
              if (r) {
                setCreated(r);
                setItems([emptyItem()]);
                orders.reload();
              }
            }}
          >
            <div className="grid grid-cols-2 gap-3">
              <Field label="Distance (km)">
                <input
                  className={inputCls}
                  type="number"
                  min={0}
                  step="0.1"
                  value={distance}
                  onChange={(e) => setDistance(e.target.value)}
                />
              </Field>
              <Field label="Traffic level">
                <input
                  className={inputCls}
                  type="number"
                  min={0}
                  step="0.1"
                  value={traffic}
                  onChange={(e) => setTraffic(e.target.value)}
                />
              </Field>
            </div>
            <div>
              <span className="text-secondary-foreground/80 mb-2 block text-sm font-medium">Items</span>
              <ItemsEditor items={items} onChange={setItems} />
            </div>
            <Button type="submit" className="h-11" disabled={create.busy || validItems.length === 0}>
              Create order
            </Button>
            <Notice msg={create.msg} />
            {created && (
              <p className="text-muted-foreground text-sm">
                Latest tracking ID: <b>{created.tracking_id}</b>
              </p>
            )}
          </form>
        </Panel>

        <div className="flex flex-col gap-4 xl:col-span-3">
          <div className="flex items-center justify-between">
            <SectionTitle>All Orders</SectionTitle>
            <Button variant="ghost" onClick={orders.reload}>
              Refresh
            </Button>
          </div>
          {orders.error && <Notice msg={{ kind: "err", text: orders.error }} />}
          {list.length === 0 && !orders.loading && !orders.error && (
            <p className="text-muted-foreground text-sm">No orders yet.</p>
          )}
          {list.map((o) => (
            <OrderCard key={o.tracking_id + o.updated_at} order={o} onChanged={orders.reload} />
          ))}
        </div>
      </div>
    </>
  );
}

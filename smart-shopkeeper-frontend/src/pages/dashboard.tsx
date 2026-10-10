import { ArrowRight, Bike, Boxes, PackagePlus, ShoppingBag, Tags, Truck, Wallet } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { Bar, BarChart, CartesianGrid, Cell, Pie, PieChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { api, type Order } from "@/lib/api";
import { Badge, PageHeader, SectionTitle, StatCard, fmt, today, useAsync } from "@/components/ui-bits";

const COLORS = ["#f10806", "#ff5150", "#ffacac", "#0a1b39", "#485066", "#858585"];

export default function Dashboard() {
  const navigate = useNavigate();
  const stock = useAsync(api.inventory.stock);
  const orders = useAsync(api.orders.list);
  const drivers = useAsync(api.drivers.list);
  const forecast = useAsync(() => api.demand.forecast(today()));
  const health = useAsync(api.health);

  const hour = new Date().getHours();
  const greeting = hour < 12 ? "Good Morning" : hour < 18 ? "Good Afternoon" : "Good Evening";

  const stockData = Object.entries(stock.data?.stock ?? {}).map(([name, value]) => ({ name, value }));
  const allOrders: Order[] = (orders.data ? Object.values(orders.data) : []).sort((a, b) =>
    b.created_at.localeCompare(a.created_at),
  );
  const activeOrders = allOrders.filter((o) => !["Delivered", "Cancelled"].includes(o.status));
  const freeDrivers = (drivers.data ?? []).filter((d) => d.status === "available").length;

  const quick = [
    { label: "Sell Items", icon: Wallet, to: "/inventory" },
    { label: "Add Category", icon: Tags, to: "/inventory" },
    { label: "Create Order", icon: PackagePlus, to: "/orders" },
    { label: "Predict Delivery", icon: Truck, to: "/delivery" },
  ];

  return (
    <>
      <PageHeader
        title={`${greeting}, Shopkeeper`}
        subtitle={new Date().toLocaleDateString(undefined, {
          weekday: "long",
          month: "short",
          day: "numeric",
          year: "numeric",
        })}
        action={
          <Button
            variant="secondary"
            className="h-11"
            onClick={() => {
              stock.reload();
              orders.reload();
              drivers.reload();
              forecast.reload();
              health.reload();
            }}
          >
            Refresh
          </Button>
        }
      />

      <div className="space-y-10">
        <section>
          <SectionTitle>Top Metrics</SectionTitle>
          <div className="mt-3 grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4">
            <StatCard
              icon={Boxes}
              iconClass="text-[#3B82F6]"
              label="Total Stock"
              value={fmt(stock.data?.total_stock, 0)}
              note="units across all categories"
            />
            <StatCard
              icon={Tags}
              iconClass="text-[#A855F7]"
              label="Categories"
              value={String(stockData.length)}
              note="products you track"
            />
            <StatCard
              icon={ShoppingBag}
              iconClass="text-[#22C55E]"
              label="Active Orders"
              value={String(activeOrders.length)}
              note={`${allOrders.length} orders in total`}
            />
            <StatCard
              icon={Bike}
              iconClass="text-[#F59E0B]"
              label="Free Riders"
              value={`${freeDrivers}/${drivers.data?.length ?? 0}`}
              note="available right now"
            />
          </div>
        </section>

        <section>
          <SectionTitle>Quick Actions</SectionTitle>
          <div className="mt-3 grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4">
            {quick.map((q) => (
              <Card
                key={q.label}
                onClick={() => navigate(q.to)}
                className="bg-secondary text-secondary-foreground cursor-pointer rounded-lg transition-colors hover:bg-[color-mix(in_oklch,var(--secondary),var(--foreground)_5%)]"
              >
                <div className="flex items-center justify-between p-3">
                  <div className="flex items-center gap-2">
                    <div className="bg-background flex size-11 items-center justify-center rounded-lg">
                      <q.icon className="size-5" />
                    </div>
                    <span className="text-secondary-foreground/80 text-base font-medium">{q.label}</span>
                  </div>
                  <ArrowRight className="text-muted-foreground size-5" />
                </div>
              </Card>
            ))}
          </div>
        </section>

        <section className="grid grid-cols-1 gap-8 lg:grid-cols-3">
          <div className="lg:col-span-2">
            <SectionTitle>Stock by Category</SectionTitle>
            <div className="mt-5 h-72">
              {stockData.length === 0 ? (
                <p className="text-muted-foreground text-sm">
                  {stock.error ?? "No categories yet. Add one in Inventory."}
                </p>
              ) : (
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={stockData} margin={{ left: 0, right: 4, top: 12 }}>
                    <CartesianGrid vertical={false} stroke="var(--border)" />
                    <XAxis dataKey="name" tickLine={false} axisLine={false} stroke="var(--muted-foreground)" fontSize={13} />
                    <YAxis tickLine={false} axisLine={false} stroke="var(--muted-foreground)" fontSize={13} />
                    <Tooltip
                      cursor={{ fill: "var(--secondary)" }}
                      contentStyle={{
                        background: "var(--foreground)",
                        color: "var(--background)",
                        border: "none",
                        borderRadius: 6,
                        fontSize: 12,
                      }}
                    />
                    <Bar dataKey="value" name="Stock" fill="var(--primary)" radius={[6, 6, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              )}
            </div>
          </div>

          <div>
            <SectionTitle>Stock Share</SectionTitle>
            <Card className="border-border mt-5 rounded-lg border p-4">
              <div className="relative mx-auto size-44">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie data={stockData} dataKey="value" innerRadius={55} outerRadius={80} paddingAngle={2} stroke="none">
                      {stockData.map((_, i) => (
                        <Cell key={i} fill={COLORS[i % COLORS.length]} />
                      ))}
                    </Pie>
                  </PieChart>
                </ResponsiveContainer>
                <div className="pointer-events-none absolute inset-0 flex flex-col items-center justify-center">
                  <span className="text-[23px] font-medium">{fmt(stock.data?.total_stock, 0)}</span>
                  <span className="text-accent-foreground text-xs">units</span>
                </div>
              </div>
              <div className="mt-4 flex flex-col gap-2">
                {stockData.map((s, i) => (
                  <div key={s.name} className="flex items-center justify-between text-sm">
                    <span className="flex items-center gap-2">
                      <span className="size-3 rounded" style={{ background: COLORS[i % COLORS.length] }} />
                      {s.name}
                    </span>
                    <span className="font-medium tabular-nums">{fmt(s.value, 0)}</span>
                  </div>
                ))}
              </div>
            </Card>
          </div>
        </section>

        <section className="grid grid-cols-1 gap-8 lg:grid-cols-2">
          <div>
            <SectionTitle>Recent Orders</SectionTitle>
            <div className="mt-5 flex flex-col gap-5">
              {allOrders.length === 0 && <p className="text-muted-foreground text-sm">No orders yet.</p>}
              {allOrders.slice(0, 5).map((o) => (
                <div key={o.tracking_id} className="flex items-center gap-3">
                  <div className="bg-secondary flex size-11 shrink-0 items-center justify-center rounded-lg">
                    <ShoppingBag className="size-5" />
                  </div>
                  <div className="flex min-w-0 flex-1 items-center justify-between gap-3">
                    <p className="text-base">
                      <span className="font-medium">{o.tracking_id}</span>{" "}
                      <span className="text-muted-foreground">
                        · {o.total_items ?? 0} items · {o.driver?.name}
                      </span>
                    </p>
                    <Badge tone={o.status === "Delivered" ? "ok" : o.status === "Cancelled" ? "bad" : "warn"}>
                      {o.status}
                    </Badge>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div>
            <SectionTitle>Shop Intelligence</SectionTitle>
            <div className="mt-5 flex flex-col gap-3">
              <Card className="bg-secondary rounded-lg p-3">
                <p className="text-sm font-semibold text-[#c803c8]">Demand forecast (today)</p>
                {forecast.data ? (
                  <p className="mt-1 text-base">
                    About <b>{fmt(forecast.data.predicted_daily, 0)}</b> units today,{" "}
                    <b>{fmt(forecast.data.predicted_weekly, 0)}</b> this week,{" "}
                    <b>{fmt(forecast.data.predicted_monthly, 0)}</b> this month.
                  </p>
                ) : (
                  <p className="text-muted-foreground mt-1 text-base">{forecast.error ?? "Loading..."}</p>
                )}
              </Card>
              <Card className="bg-secondary rounded-lg p-3">
                <p className="text-sm font-semibold text-[#d47c01]">Models</p>
                <p className="mt-1 text-base">
                  {health.data
                    ? `Demand model ${health.data.demand_model_trained ? "is trained" : "needs training"}; delivery model ${
                        health.data.delivery_model_trained ? "is trained" : "needs training"
                      }.`
                    : (health.error ?? "Loading...")}
                </p>
              </Card>
              <Card className="bg-secondary rounded-lg p-3">
                <p className="text-sm font-semibold text-[#15823e]">Riders</p>
                <p className="mt-1 text-base">
                  {freeDrivers} of {drivers.data?.length ?? 0} riders are free to take a new order.
                </p>
              </Card>
            </div>
          </div>
        </section>
      </div>
    </>
  );
}

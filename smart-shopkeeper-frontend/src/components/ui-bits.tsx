import { useEffect, useState, type ComponentType, type ReactNode } from "react";
import { Card } from "@/components/ui/card";
import { cn } from "@/lib/utils";

export const inputCls =
  "h-11 w-full rounded-lg bg-secondary px-3 text-sm outline-none placeholder:text-muted-foreground focus:ring-2 focus:ring-primary/40";

export const fmt = (n: number | null | undefined, d = 1) =>
  (n ?? 0).toLocaleString(undefined, { maximumFractionDigits: d });

export const today = () => new Date().toISOString().slice(0, 10);

export function PageHeader({ title, subtitle, action }: { title: string; subtitle?: string; action?: ReactNode }) {
  return (
    <div className="mb-8 flex flex-col items-start justify-between gap-4 sm:flex-row sm:items-end">
      <div className="flex flex-col gap-1.5">
        <h1 className="text-xl font-medium italic">{title}</h1>
        {subtitle && <p className="text-muted-foreground text-base">{subtitle}</p>}
      </div>
      {action}
    </div>
  );
}

export function SectionTitle({ children }: { children: ReactNode }) {
  return <h2 className="text-lg font-medium">{children}</h2>;
}

export function Panel({ title, children, className }: { title?: string; children: ReactNode; className?: string }) {
  return (
    <section className={className}>
      {title && <SectionTitle>{title}</SectionTitle>}
      <Card className={cn("border-border rounded-lg border p-4 shadow-none", title && "mt-4")}>{children}</Card>
    </section>
  );
}

export function Field({ label, children }: { label: string; children: ReactNode }) {
  return (
    <label className="flex flex-col gap-1.5">
      <span className="text-secondary-foreground/80 text-sm font-medium">{label}</span>
      {children}
    </label>
  );
}

export function StatCard({
  icon: Icon,
  iconClass,
  label,
  value,
  note,
}: {
  icon: ComponentType<{ className?: string }>;
  iconClass: string;
  label: string;
  value: string;
  note?: string;
}) {
  return (
    <Card className="bg-secondary text-secondary-foreground gap-6 rounded-lg p-4">
      <div className="flex items-center gap-2">
        <Icon className={cn("size-5 shrink-0", iconClass)} />
        <span className="text-secondary-foreground/80 text-sm font-medium">{label}</span>
      </div>
      <div className="flex flex-col gap-2">
        <h3 className="text-foreground text-[32px] leading-none font-medium">{value}</h3>
        {note && <p className="text-muted-foreground text-xs">{note}</p>}
      </div>
    </Card>
  );
}

export type Msg = { kind: "ok" | "err"; text: string } | null;

export function Notice({ msg }: { msg: Msg }) {
  if (!msg) return null;
  return (
    <p
      className={cn(
        "rounded-lg px-3 py-2 text-sm",
        msg.kind === "ok" ? "bg-green-500/10 text-green-700 dark:text-green-400" : "bg-red-500/10 text-red-600",
      )}
    >
      {msg.text}
    </p>
  );
}

export function Badge({ children, tone = "muted" }: { children: ReactNode; tone?: "ok" | "warn" | "bad" | "muted" }) {
  const tones = {
    ok: "bg-green-500/10 text-green-700 dark:text-green-400",
    warn: "bg-amber-500/10 text-amber-700 dark:text-amber-400",
    bad: "bg-red-500/10 text-red-600",
    muted: "bg-secondary text-secondary-foreground",
  };
  return <span className={cn("rounded-full px-2.5 py-0.5 text-xs font-medium", tones[tone])}>{children}</span>;
}

/** Loads data from the backend; call reload() to refetch. */
export function useAsync<T>(fn: () => Promise<T>, deps: unknown[] = []) {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [tick, setTick] = useState(0);

  useEffect(() => {
    let alive = true;
    setLoading(true);
    fn()
      .then((d) => {
        if (alive) {
          setData(d);
          setError(null);
        }
      })
      .catch((e: Error) => {
        if (alive) setError(e.message);
      })
      .finally(() => {
        if (alive) setLoading(false);
      });
    return () => {
      alive = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [tick, ...deps]);

  return { data, error, loading, reload: () => setTick((t) => t + 1) };
}

/** Runs a button action with a busy flag and a success/error message. */
export function useAction() {
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState<Msg>(null);

  async function run<T>(fn: () => Promise<T>, ok?: string | ((r: T) => string)): Promise<T | undefined> {
    setBusy(true);
    setMsg(null);
    try {
      const r = await fn();
      if (ok) setMsg({ kind: "ok", text: typeof ok === "function" ? ok(r) : ok });
      return r;
    } catch (e) {
      setMsg({ kind: "err", text: (e as Error).message });
    } finally {
      setBusy(false);
    }
  }

  return { busy, msg, run, setMsg };
}

import React from "react";
import { clsx } from "clsx";

// ── Spinner ───────────────────────────────────────────────────────────────────
export function Spinner({ size = 20 }: { size?: number }) {
  return (
    <span
      style={{ width: size, height: size }}
      className="inline-block rounded-full border-2 border-pip-200 border-t-pip-500 animate-spin flex-shrink-0"
    />
  );
}

// ── Badge ─────────────────────────────────────────────────────────────────────
type BadgeColor = "green" | "amber" | "red" | "blue" | "pip" | "gray";

const badgeMap: Record<BadgeColor, string> = {
  green: "bg-emerald-50  text-emerald-700  border-emerald-200",
  amber: "bg-amber-50    text-amber-700    border-amber-200",
  red:   "bg-red-50      text-red-700      border-red-200",
  blue:  "bg-blue-50     text-blue-700     border-blue-200",
  pip:   "bg-pip-50      text-pip-600      border-pip-200",
  gray:  "bg-gray-100    text-gray-500     border-gray-200",
};

export function Badge({
  children, color = "gray", className,
}: { children: React.ReactNode; color?: BadgeColor; className?: string }) {
  return (
    <span className={clsx(
      "inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-semibold border",
      badgeMap[color], className
    )}>
      {children}
    </span>
  );
}

// ── Field ─────────────────────────────────────────────────────────────────────
export function Field({
  label, value, highlight,
}: { label: string; value: React.ReactNode; highlight?: "green" | "red" | "amber" | "pip" }) {
  const highlightClass = highlight
    ? { green: "text-emerald-600", red: "text-red-600", amber: "text-amber-600", pip: "text-pip-600" }[highlight]
    : "text-gray-900";

  return (
    <div className="flex flex-col gap-0.5 min-w-0">
      <span className="text-[9px] font-semibold text-gray-400 uppercase tracking-wider">
        {label}
      </span>
      <span className={clsx("text-[11px] font-medium leading-snug break-words", highlightClass)}>
        {value ?? "—"}
      </span>
    </div>
  );
}

// ── Section Card ──────────────────────────────────────────────────────────────
export function SectionCard({
  title, children, className, action,
}: {
  title: string;
  children: React.ReactNode;
  className?: string;
  action?: React.ReactNode;
}) {
  return (
    <div className={clsx("bg-white border border-gray-200 rounded-xl shadow-sm overflow-hidden", className)}>
      <div className="flex items-center justify-between px-4 py-2.5 border-b border-gray-100 bg-gray-50">
        <span className="text-[10px] font-bold text-gray-700 uppercase tracking-wider">{title}</span>
        {action}
      </div>
      {children}
    </div>
  );
}

// ── Empty state ───────────────────────────────────────────────────────────────
export function Empty({ message }: { message: string }) {
  return (
    <div className="flex items-center justify-center py-10 text-gray-400 text-xs">
      {message}
    </div>
  );
}

// ── KPI card ──────────────────────────────────────────────────────────────────
export function KpiCard({
  label, value, sub, color = "default",
}: {
  label: string;
  value: React.ReactNode;
  sub?: string;
  color?: "default" | "pip" | "green" | "red" | "amber";
}) {
  const valueClass = {
    default: "text-gray-900",
    pip:     "text-pip-600",
    green:   "text-emerald-600",
    red:     "text-red-600",
    amber:   "text-amber-600",
  }[color];

  return (
    <div className="bg-white px-4 py-2.5">
      <div className="text-[9px] font-semibold text-gray-400 uppercase tracking-wider mb-0.5">
        {label}
      </div>
      <div className={clsx("text-[15px] font-bold", valueClass)}>{value}</div>
      {sub && <div className="text-[10px] text-gray-400 mt-0.5">{sub}</div>}
    </div>
  );
}

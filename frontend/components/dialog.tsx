"use client";

import { useEffect, useRef } from "react";
import { X } from "lucide-react";

export function Dialog({ title, children, onClose, busy = false, wide = false }: {
  title: string;
  children: React.ReactNode;
  onClose: () => void;
  busy?: boolean;
  wide?: boolean;
}) {
  const ref = useRef<HTMLElement>(null);
  const close = useRef(onClose);
  const locked = useRef(busy);
  close.current = onClose;
  locked.current = busy;

  useEffect(() => {
    const previous = document.activeElement as HTMLElement | null;
    const overflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    ref.current?.querySelector<HTMLElement>("button, input, select, textarea")?.focus();
    function onKey(event: KeyboardEvent) {
      if (event.key === "Escape" && !locked.current) close.current();
      if (event.key !== "Tab") return;
      const elements = Array.from(ref.current?.querySelectorAll<HTMLElement>(
        'button:not([disabled]), input:not([disabled]), select:not([disabled]), textarea:not([disabled]), a[href]'
      ) || []).filter(element => element.offsetParent !== null);
      const first = elements[0];
      const last = elements.at(-1);
      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault();
        last?.focus();
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault();
        first?.focus();
      }
    }
    document.addEventListener("keydown", onKey);
    return () => {
      document.body.style.overflow = overflow;
      document.removeEventListener("keydown", onKey);
      previous?.focus();
    };
  }, []);

  return <div className="dialog-backdrop" onMouseDown={event => {
    if (event.target === event.currentTarget && !busy) onClose();
  }}>
    <section ref={ref} className={`dialog ${wide ? "dialog-wide" : ""}`}
      role="dialog" aria-modal="true" aria-labelledby="dialog-title">
      <header className="dialog-heading">
        <h2 id="dialog-title">{title}</h2>
        <button className="icon-button" disabled={busy} onClick={onClose} aria-label="Close dialog"><X size={20} /></button>
      </header>
      {children}
    </section>
  </div>;
}

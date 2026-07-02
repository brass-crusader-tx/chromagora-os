"use client";

import { useRef, useState } from "react";
import type { BeforeAfterRevealConfig } from "./types";

interface BeforeAfterRevealProps {
  config?: BeforeAfterRevealConfig;
  children: React.ReactNode;
}

export default function BeforeAfterReveal({ config, children }: BeforeAfterRevealProps) {
  const orientation = config?.orientation || "horizontal";
  const [reveal, setReveal] = useState(config?.default_reveal_percent ?? 45);
  const [imageFailed, setImageFailed] = useState(false);
  const ref = useRef<HTMLDivElement | null>(null);
  const beforeImage =
    config?.before_image_url || config?.before_desktop_image_url || config?.before_mobile_image_url;

  if (!config?.enabled || !beforeImage || imageFailed) {
    return <>{children}</>;
  }

  function updateReveal(clientX: number, clientY: number) {
    const rect = ref.current?.getBoundingClientRect();
    if (!rect) return;
    const raw = orientation === "vertical"
      ? ((clientX - rect.left) / rect.width) * 100
      : ((clientY - rect.top) / rect.height) * 100;
    setReveal(Math.max(0, Math.min(100, raw)));
  }

  const clipPath = orientation === "vertical"
    ? `inset(0 ${100 - reveal}% 0 0)`
    : `inset(0 0 ${100 - reveal}% 0)`;

  return (
    <div
      ref={ref}
      className="relative min-h-screen overflow-hidden bg-slate-950"
      onPointerDown={(event) => {
        event.currentTarget.setPointerCapture(event.pointerId);
        updateReveal(event.clientX, event.clientY);
      }}
      onPointerMove={(event) => {
        if (event.buttons) updateReveal(event.clientX, event.clientY);
      }}
    >
      <div className="absolute inset-0">
        <picture>
          {config.before_mobile_image_url && (
            <source media="(max-width: 767px)" srcSet={config.before_mobile_image_url} />
          )}
          {config.before_desktop_image_url && (
            <source media="(min-width: 768px)" srcSet={config.before_desktop_image_url} />
          )}
          <img
            src={beforeImage}
            alt="Current website preview"
            className="h-full w-full object-cover opacity-80"
            onError={() => setImageFailed(true)}
          />
        </picture>
      </div>

      <div className="absolute inset-0 overflow-hidden bg-white" style={{ clipPath }}>
        {children}
      </div>

      <div
        className="pointer-events-none absolute z-30 bg-white/80 shadow-lg"
        style={
          orientation === "vertical"
            ? { top: 0, bottom: 0, left: `${reveal}%`, width: 2 }
            : { left: 0, right: 0, top: `${reveal}%`, height: 2 }
        }
      />
      <div
        className="pointer-events-none absolute z-30 rounded-full border border-white/70 bg-slate-950/80 px-3 py-1 text-xs font-medium text-white shadow"
        style={
          orientation === "vertical"
            ? { left: `calc(${reveal}% - 84px)`, top: 24 }
            : { top: `calc(${reveal}% - 16px)`, left: 24 }
        }
      >
        {config.instruction_text || "Slide to reveal the rebuilt version"}
      </div>
      <button
        type="button"
        className="absolute bottom-4 right-4 z-40 rounded-md bg-white px-4 py-2 text-sm font-semibold text-slate-950 shadow"
        onClick={() => setReveal(100)}
      >
        Reveal full site
      </button>
    </div>
  );
}

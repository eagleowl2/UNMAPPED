import { QRCodeSVG } from 'qrcode.react';

interface Props {
  hlId: string;
  size?: number;
}

export function QrSimulation({ hlId, size = 92 }: Props) {
  // Demo URL — replace with verifiable-credential resolver in v0.4.
  const url = `https://unmapped.demo/hl/${hlId}`;

  return (
    <div className="flex flex-col items-center gap-1.5">
      <div className="rounded-lg bg-white p-2 ring-1 ring-clay-200">
        <QRCodeSVG
          value={url}
          size={size}
          bgColor="#ffffff"
          fgColor="#241c13"
          level="M"
          aria-label={`QR code for human-layer ${hlId}`}
        />
      </div>
      <p className="font-mono text-[10px] text-clay-600">{hlId.slice(0, 14)}…</p>
    </div>
  );
}

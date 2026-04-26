import { QRCodeSVG } from 'qrcode.react';

interface Props {
  profileId: string;
  size?: number;
}

export function QrSimulation({ profileId, size = 92 }: Props) {
  // Demo URL — replace with verifiable-credential resolver in v0.4.
  const url = `https://unmapped.demo/p/${profileId}`;

  return (
    <div className="flex flex-col items-center gap-1.5">
      <div className="rounded-lg bg-white p-2 ring-1 ring-clay-200">
        <QRCodeSVG
          value={url}
          size={size}
          bgColor="#ffffff"
          fgColor="#241c13"
          level="M"
          aria-label={`QR code for profile ${profileId}`}
        />
      </div>
      <p className="font-mono text-[10px] text-clay-600">{profileId}</p>
    </div>
  );
}

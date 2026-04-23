import type { Metadata } from 'next';

import './globals.css';

export const metadata: Metadata = {
  title: 'Soficca Clinical Decision Layer',
  description: 'Cardiology triage demo powered by deterministic routing, safety policy, and audit trace',
  icons: { icon: '/favicon.png' },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="font-sans antialiased">{children}</body>
    </html>
  );
}

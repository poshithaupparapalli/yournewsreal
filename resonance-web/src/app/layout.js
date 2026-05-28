import "./globals.css";

export const metadata = {
  title: "resonance",
  description: "your morning briefing, shaped around what you care about.",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body style={{ minHeight: '100%', display: 'flex', flexDirection: 'column', background: '#f5f4f0' }}>{children}</body>
    </html>
  );
}

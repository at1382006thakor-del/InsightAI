import type { Metadata } from "next";
import "./globals.css";
import Providers from "./providers";

export const metadata: Metadata = {
  title: "InsightAI – Sales Analytics & Strategic Planning Console",
  description: "Transform raw transactions into active intelligence dashboards, forecasts, and strategical strategy drafts.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="antialiased selection:bg-brand-500 selection:text-white bg-zinc-950 text-zinc-50">
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}

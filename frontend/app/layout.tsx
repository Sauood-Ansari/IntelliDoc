import type { Metadata } from "next";
import "./globals.css";
export const metadata: Metadata = {title: "IntelliDoc · Documentation intelligence", description: "Understand documentation drift. Review findings, track reliability, and give your team a clearer picture."};
export default function Layout({children}: Readonly<{children: React.ReactNode}>) {
  return <html lang="en"><body>{children}</body></html>;
}


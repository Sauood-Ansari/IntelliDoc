import type { Metadata } from "next";
import "./globals.css";
export const metadata: Metadata = {title: "IntelliDoc · Python documentation review", description: "Review Python documentation within projects and teams. Upload source, inspect findings and track scan results."};
export default function Layout({children}: Readonly<{children: React.ReactNode}>) {
  return <html lang="en"><body>{children}</body></html>;
}


import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import { SessionProvider } from "next-auth/react";
import CleanExtensionAttrs from "@/components/CleanExtensionAttrs";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Synkrone — Plateforme de services Discord & gaming",
  description: "Créez et gérez vos bots Discord, serveurs Minecraft, sites web et applications depuis une interface unifiée.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="fr" suppressHydrationWarning>
      <body className={`${geistSans.variable} ${geistMono.variable} antialiased bg-[#0a0a0a] text-neutral-50`} suppressHydrationWarning>
        <SessionProvider>
          <CleanExtensionAttrs />
          {children}
        </SessionProvider>
      </body>
    </html>
  );
}

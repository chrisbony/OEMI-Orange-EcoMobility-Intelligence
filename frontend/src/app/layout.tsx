import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Orange EcoMobility Intelligence (OEMI) — Aide à la Décision Territoriale",
  description:
    "Plateforme d'intelligence territoriale combinant mobilité agrégée, données géographiques et analyse économique pour l'implantation commerciale à Abidjan.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="fr" className="dark">
      <body className="min-h-screen bg-slate-950 text-slate-100 antialiased selection:bg-orange-500 selection:text-white">
        {children}
      </body>
    </html>
  );
}

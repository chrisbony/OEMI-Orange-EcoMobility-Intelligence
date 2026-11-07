import React from "react";
import Navbar from "@/components/Navbar";
import DecisionDashboard from "@/components/DecisionDashboard";
import { ShieldCheck, Info } from "lucide-react";

export default function HomePage() {
  return (
    <div className="min-h-screen flex flex-col bg-slate-950">
      <Navbar backendConnected={true} />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
        {/* Hero Header */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800/80 pb-6">
          <div>
            <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-orange-500/10 border border-orange-500/20 text-orange-400 text-xs font-semibold mb-3">
              <span>Orange Think Tank Challenge 2026</span>
              <span>•</span>
              <span>Intelligence Territoriale & Mobilité</span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-black text-slate-100 tracking-tight">
              Tableau de Bord Décisionnel d&apos;Implantation Commerciale
            </h1>
            <p className="text-sm text-slate-400 max-w-2xl mt-1.5">
              Croisement des mobilités agrégées d&apos;Abidjan, des données démographiques RGPH 2021 de l&apos;INS et du réseau viaire OSM pour calculer l&apos;Indice de Potentiel Économique Territorial (IPET).
            </p>
          </div>

          <div className="flex items-center space-x-3 bg-slate-900/60 border border-slate-800 p-3 rounded-2xl">
            <div className="w-10 h-10 rounded-xl bg-orange-500/20 border border-orange-500/30 flex items-center justify-center text-orange-400">
              <ShieldCheck className="w-5 h-5" />
            </div>
            <div>
              <div className="text-xs font-bold text-slate-200">Gouvernance & Éthique</div>
              <div className="text-[11px] text-slate-400">
                k-Anonymat (k ≥ 15) • Loi n° 2013-450 • Zéro PII
              </div>
            </div>
          </div>
        </div>

        {/* Core Interactive Decision Application */}
        <DecisionDashboard />

        {/* Methodological Footer Disclaimer per Cahier des Charges §13.2 */}
        <div className="bg-slate-900/40 border border-slate-800/80 rounded-2xl p-4 text-xs text-slate-400 flex items-start space-x-3">
          <Info className="w-4 h-4 text-orange-400 shrink-0 mt-0.5" />
          <div className="space-y-1">
            <div className="font-semibold text-slate-300">
              Avertissements méthodologiques & Limites du modèle (Cahier des Charges §13.2) :
            </div>
            <p className="text-[11px] text-slate-400 leading-relaxed">
              Le score multicritère IPET est un indicateur d&apos;aide à la décision et de présélection des territoires ; il ne garantit en aucun cas le chiffre d&apos;affaires ou la rentabilité d&apos;un point de vente. La fréquentation d&apos;une zone ne correspond pas strictement à sa population résidente. Les données de mobilité présentées sont issues du simulateur synthétique spatialement contraint labellisé conformément au protocole de repli du challenge.
            </p>
          </div>
        </div>
      </main>

      <footer className="border-t border-slate-800 bg-slate-950/60 py-6 text-center text-xs text-slate-500">
        <p>Orange EcoMobility Intelligence © 2026 — Orange Think Tank Challenge • Conforme à la Loi ivoirienne n° 2013-450</p>
      </footer>
    </div>
  );
}

"use client";

import React, { useState, useEffect } from "react";
import ThreeCanvas3D from "./ThreeCanvas3D";
import {
  Building2,
  TrendingUp,
  MapPin,
  Users,
  Navigation,
  FileDown,
  Sparkles,
  Sliders,
  CheckCircle2,
  AlertTriangle,
  RotateCcw,
  BarChart3,
  Calendar,
  Layers,
} from "lucide-react";

interface ZoneItem {
  id: string;
  nom_commune: string;
  nom_zone: string;
  type_zone: string;
  population: number;
  score_ipet: number;
  score_connectivite?: number;
  coordinates: [number, number][];
  centroid: [number, number];
  rang?: number;
  facteurs_positifs?: { facteur: string; contribution: number }[];
  facteurs_limitants?: { facteur: string; impact: number }[];
}

interface PredictionPoint {
  date_horizon: string;
  valeur_estimee: number;
  borne_inferieure: number;
  borne_superieure: number;
  modele_utilise: string;
  metrique_wape: number;
}

export default function DecisionDashboard() {
  const [communeFilter, setCommuneFilter] = useState<string>("Toutes");
  const [timeSlot, setTimeSlot] = useState<string>("07h-09h");
  const [sector, setSector] = useState<string>("SUPERMARCHE");

  // IPET weights (default: 30%, 25%, 20%, 15%, 10%)
  const [weights, setWeights] = useState({
    frequentation: 0.30,
    demographie: 0.25,
    accessibilite: 0.20,
    dynamique: 0.15,
    concurrence: 0.10,
  });

  const [zones, setZones] = useState<ZoneItem[]>([]);
  const [selectedZone, setSelectedZone] = useState<ZoneItem | null>(null);
  const [forecastModel, setForecastModel] = useState<string>("PROPHET");
  const [forecastData, setForecastData] = useState<PredictionPoint[]>([]);
  const [loading, setLoading] = useState<boolean>(true);

  // Fetch zones & initial IPET
  useEffect(() => {
    async function loadData() {
      try {
        setLoading(true);
        // Call backend API /api/zones
        const zonesRes = await fetch(
          `/api/zones${communeFilter !== "Toutes" ? `?commune=${communeFilter}` : ""}`
        );
        const zonesGeo = await zonesRes.json();

        // Call backend API /api/ipet with active weights
        const ipetRes = await fetch("/api/ipet", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ secteur: sector, weights }),
        });
        const ipetData = await ipetRes.json();

        const recsMap = new Map();
        if (ipetData.recommendations) {
          ipetData.recommendations.forEach((r: any) => recsMap.set(r.zone_id, r));
        }

        const parsedZones: ZoneItem[] = (zonesGeo.features || []).map((f: any) => {
          const rec = recsMap.get(f.id) || {};
          const coords = f.geometry?.coordinates?.[0] || [];
          // Calculate centroid
          let sumLon = 0;
          let sumLat = 0;
          coords.forEach(([lon, lat]: [number, number]) => {
            sumLon += lon;
            sumLat += lat;
          });
          const cLon = coords.length ? sumLon / coords.length : -4.0;
          const cLat = coords.length ? sumLat / coords.length : 5.34;

          return {
            id: f.id,
            nom_commune: f.properties?.nom_commune || "Abidjan",
            nom_zone: f.properties?.nom_zone || f.id,
            type_zone: f.properties?.type_zone || "Quartier",
            population: f.properties?.population || 90000,
            score_ipet: rec.score_ipet || f.properties?.score_ipet || 75.0,
            score_connectivite: f.properties?.score_connectivite || 80.0,
            coordinates: coords,
            centroid: [cLon, cLat],
            rang: rec.rang || 1,
            facteurs_positifs: rec.facteurs_positifs || [
              { facteur: "Fréquentation pendulaire", contribution: 26.5 },
              { facteur: "Bassin démographique", contribution: 21.0 },
              { facteur: "Connectivité routière", contribution: 18.2 },
            ],
            facteurs_limitants: rec.facteurs_limitants || [],
          };
        });

        // Sort by IPET
        parsedZones.sort((a, b) => b.score_ipet - a.score_ipet);
        parsedZones.forEach((z, i) => (z.rang = i + 1));

        setZones(parsedZones);
        if (parsedZones.length > 0 && !selectedZone) {
          setSelectedZone(parsedZones[0]);
        }
      } catch (err) {
        console.error("Error loading dashboard data:", err);
      } finally {
        setLoading(false);
      }
    }

    loadData();
  }, [communeFilter, sector, weights]);

  // Load predictions when selectedZone or forecastModel changes
  useEffect(() => {
    if (!selectedZone) return;
    async function loadForecast() {
      try {
        const res = await fetch(
          `/api/predictions/${selectedZone.id}?model=${forecastModel}&horizon=7`
        );
        const data = await res.json();
        setForecastData(data.predictions || []);
      } catch (e) {
        console.error("Error loading predictions:", e);
      }
    }
    loadForecast();
  }, [selectedZone, forecastModel]);

  const handleWeightChange = (key: keyof typeof weights, value: number) => {
    setWeights((prev) => {
      const updated = { ...prev, [key]: value };
      // Normalize sum to 1.0
      const sum = Object.values(updated).reduce((acc, v) => acc + v, 0);
      if (sum > 0) {
        for (const k in updated) {
          updated[k as keyof typeof weights] = Number(
            (updated[k as keyof typeof weights] / sum).toFixed(2)
          );
        }
      }
      return updated;
    });
  };

  const resetWeights = () => {
    setWeights({
      frequentation: 0.30,
      demographie: 0.25,
      accessibilite: 0.20,
      dynamique: 0.15,
      concurrence: 0.10,
    });
  };

  return (
    <div className="space-y-6">
      {/* Control Filters Ribbon */}
      <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-4 sm:p-5 backdrop-blur-md shadow-lg">
        <div className="flex flex-wrap items-center justify-between gap-4">
          {/* Commune Selector */}
          <div className="flex items-center space-x-2">
            <MapPin className="w-4 h-4 text-orange-500" />
            <span className="text-xs font-semibold text-slate-300">Commune Pilote :</span>
            <div className="flex bg-slate-950 p-1 rounded-xl border border-slate-800">
              {["Toutes", "Cocody", "Yopougon", "Marcory"].map((c) => (
                <button
                  key={c}
                  onClick={() => setCommuneFilter(c)}
                  className={`px-3 py-1 text-xs font-medium rounded-lg transition ${
                    communeFilter === c
                      ? "bg-orange-500 text-white shadow-md shadow-orange-500/30"
                      : "text-slate-400 hover:text-slate-200"
                  }`}
                >
                  {c}
                </button>
              ))}
            </div>
          </div>

          {/* Time Slice Selector */}
          <div className="flex items-center space-x-2">
            <Calendar className="w-4 h-4 text-sky-400" />
            <span className="text-xs font-semibold text-slate-300">Plage Horaire :</span>
            <select
              value={timeSlot}
              onChange={(e) => setTimeSlot(e.target.value)}
              className="bg-slate-950 border border-slate-800 text-slate-200 text-xs rounded-xl px-3 py-1.5 focus:outline-none focus:border-orange-500"
            >
              <option value="07h-09h">07h-09h (Pointe Pendulaire Matin)</option>
              <option value="12h-14h">12h-14h (Déjeuner & Commerces)</option>
              <option value="17h-20h">17h-20h (Pointe Pendulaire Soir)</option>
              <option value="02h-04h">02h-04h (Nuit / Seuil &lt; 15 masqué)</option>
            </select>
          </div>

          {/* Sector Selector */}
          <div className="flex items-center space-x-2">
            <Building2 className="w-4 h-4 text-amber-400" />
            <span className="text-xs font-semibold text-slate-300">Activité Cible :</span>
            <span className="px-3 py-1 text-xs font-bold bg-amber-500/10 text-amber-400 border border-amber-500/30 rounded-xl">
              Supermarché (Cas d&apos;usage officiel)
            </span>
          </div>
        </div>
      </div>

      {/* Main Grid: 3D Visualization (Left) + Interactive Weight Tuner & Zone Card (Right) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left: 3D Three.js Cartographic Canvas (7 cols) */}
        <div className="lg:col-span-7 space-y-4">
          <ThreeCanvas3D
            zones={zones}
            selectedZone={selectedZone}
            onSelectZone={(z) => setSelectedZone(z)}
          />

          {/* Quick Metrics Bar below 3D Map */}
          <div className="grid grid-cols-3 gap-3">
            <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-3 text-center">
              <div className="text-[11px] text-slate-400">Zones Analysées</div>
              <div className="text-xl font-bold text-slate-100">{zones.length}</div>
            </div>
            <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-3 text-center">
              <div className="text-[11px] text-slate-400">Zone N°1 Recommandée</div>
              <div className="text-sm font-bold text-orange-400 truncate">
                {zones[0]?.nom_zone || "Calcul..."}
              </div>
            </div>
            <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-3 text-center">
              <div className="text-[11px] text-slate-400">Score IPET Max</div>
              <div className="text-xl font-bold text-emerald-400">
                {zones[0]?.score_ipet || "--"}/100
              </div>
            </div>
          </div>
        </div>

        {/* Right: Selected Zone Detailed Factsheet & Weight Tuning (5 cols) */}
        <div className="lg:col-span-5 space-y-6">
          {/* Interactive Weight Sliders (Feature F16) */}
          <div className="bg-slate-900/70 border border-slate-800 rounded-2xl p-5 shadow-xl space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div className="flex items-center space-x-2">
                <Sliders className="w-4 h-4 text-orange-500" />
                <h3 className="text-sm font-bold text-slate-100">
                  Calibration Multicritère IPET
                </h3>
              </div>
              <button
                onClick={resetWeights}
                className="text-[11px] flex items-center space-x-1 text-slate-400 hover:text-orange-400 transition"
                title="Rétablir les poids recommandés du Cahier des Charges"
              >
                <RotateCcw className="w-3 h-3" />
                <span>Par défaut</span>
              </button>
            </div>

            <div className="space-y-3 text-xs">
              <div>
                <div className="flex justify-between text-slate-300 mb-1">
                  <span>Fréquentation agrégée</span>
                  <span className="font-bold text-orange-400">
                    {Math.round(weights.frequentation * 100)}%
                  </span>
                </div>
                <input
                  type="range"
                  min="0.05"
                  max="0.60"
                  step="0.05"
                  value={weights.frequentation}
                  onChange={(e) =>
                    handleWeightChange("frequentation", parseFloat(e.target.value))
                  }
                  className="w-full accent-orange-500 bg-slate-800 h-1.5 rounded-lg appearance-none cursor-pointer"
                />
              </div>

              <div>
                <div className="flex justify-between text-slate-300 mb-1">
                  <span>Bassin démographique (INS RGPH)</span>
                  <span className="font-bold text-sky-400">
                    {Math.round(weights.demographie * 100)}%
                  </span>
                </div>
                <input
                  type="range"
                  min="0.05"
                  max="0.60"
                  step="0.05"
                  value={weights.demographie}
                  onChange={(e) =>
                    handleWeightChange("demographie", parseFloat(e.target.value))
                  }
                  className="w-full accent-sky-500 bg-slate-800 h-1.5 rounded-lg appearance-none cursor-pointer"
                />
              </div>

              <div>
                <div className="flex justify-between text-slate-300 mb-1">
                  <span>Accessibilité & connectivité routière</span>
                  <span className="font-bold text-emerald-400">
                    {Math.round(weights.accessibilite * 100)}%
                  </span>
                </div>
                <input
                  type="range"
                  min="0.05"
                  max="0.60"
                  step="0.05"
                  value={weights.accessibilite}
                  onChange={(e) =>
                    handleWeightChange("accessibilite", parseFloat(e.target.value))
                  }
                  className="w-full accent-emerald-500 bg-slate-800 h-1.5 rounded-lg appearance-none cursor-pointer"
                />
              </div>

              <div>
                <div className="flex justify-between text-slate-300 mb-1">
                  <span>Dynamique de croissance</span>
                  <span className="font-bold text-purple-400">
                    {Math.round(weights.dynamique * 100)}%
                  </span>
                </div>
                <input
                  type="range"
                  min="0.05"
                  max="0.60"
                  step="0.05"
                  value={weights.dynamique}
                  onChange={(e) =>
                    handleWeightChange("dynamique", parseFloat(e.target.value))
                  }
                  className="w-full accent-purple-500 bg-slate-800 h-1.5 rounded-lg appearance-none cursor-pointer"
                />
              </div>

              <div>
                <div className="flex justify-between text-slate-300 mb-1">
                  <span>Opportunité / Concurrence modérée</span>
                  <span className="font-bold text-rose-400">
                    {Math.round(weights.concurrence * 100)}%
                  </span>
                </div>
                <input
                  type="range"
                  min="0.05"
                  max="0.60"
                  step="0.05"
                  value={weights.concurrence}
                  onChange={(e) =>
                    handleWeightChange("concurrence", parseFloat(e.target.value))
                  }
                  className="w-full accent-rose-500 bg-slate-800 h-1.5 rounded-lg appearance-none cursor-pointer"
                />
              </div>
            </div>
          </div>

          {/* Selected Zone Factsheet (Feature F18: Decision Explainability) */}
          {selectedZone && (
            <div className="bg-slate-900/70 border border-slate-800 rounded-2xl p-5 shadow-xl space-y-4">
              <div className="flex items-start justify-between">
                <div>
                  <div className="flex items-center space-x-2">
                    <span className="px-2 py-0.5 text-xs font-bold bg-orange-500/20 text-orange-400 rounded-md border border-orange-500/30">
                      Rang #{selectedZone.rang}
                    </span>
                    <h3 className="text-base font-bold text-slate-100">
                      {selectedZone.nom_zone}
                    </h3>
                  </div>
                  <p className="text-xs text-slate-400 mt-0.5">
                    Commune de {selectedZone.nom_commune} • {selectedZone.type_zone}
                  </p>
                </div>
                <div className="text-right">
                  <div className="text-2xl font-black text-emerald-400">
                    {selectedZone.score_ipet}
                  </div>
                  <div className="text-[10px] text-slate-500 font-medium">IPET / 100</div>
                </div>
              </div>

              {/* Baseline stats */}
              <div className="grid grid-cols-2 gap-2 text-xs">
                <div className="bg-slate-950 p-2.5 rounded-xl border border-slate-800/80">
                  <div className="text-slate-400 text-[10px] flex items-center space-x-1">
                    <Users className="w-3 h-3 text-sky-400" />
                    <span>Population (RGPH 2021)</span>
                  </div>
                  <div className="font-semibold text-slate-200 mt-1">
                    {selectedZone.population.toLocaleString()} habitants
                  </div>
                </div>
                <div className="bg-slate-950 p-2.5 rounded-xl border border-slate-800/80">
                  <div className="text-slate-400 text-[10px] flex items-center space-x-1">
                    <Navigation className="w-3 h-3 text-emerald-400" />
                    <span>Connectivité Routière</span>
                  </div>
                  <div className="font-semibold text-slate-200 mt-1">
                    {selectedZone.score_connectivite || 80}/100
                  </div>
                </div>
              </div>

              {/* Explainability: Positive Drivers */}
              <div className="space-y-1.5">
                <div className="text-[11px] font-semibold text-slate-300">
                  Facteurs contributifs favorables :
                </div>
                {(selectedZone.facteurs_positifs || []).map((fp, idx) => (
                  <div
                    key={idx}
                    className="flex items-center justify-between text-xs bg-emerald-950/20 border border-emerald-500/20 px-2.5 py-1.5 rounded-lg text-emerald-300"
                  >
                    <div className="flex items-center space-x-1.5">
                      <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
                      <span>{fp.facteur}</span>
                    </div>
                    <span className="font-bold">+{fp.contribution} pts</span>
                  </div>
                ))}
              </div>

              {/* Limiting factors */}
              {selectedZone.facteurs_limitants && selectedZone.facteurs_limitants.length > 0 && (
                <div className="space-y-1.5 pt-1">
                  <div className="text-[11px] font-semibold text-slate-300">
                    Points de vigilance / Limites :
                  </div>
                  {selectedZone.facteurs_limitants.map((fl, idx) => (
                    <div
                      key={idx}
                      className="flex items-center justify-between text-xs bg-amber-950/20 border border-amber-500/20 px-2.5 py-1.5 rounded-lg text-amber-300"
                    >
                      <div className="flex items-center space-x-1.5">
                        <AlertTriangle className="w-3.5 h-3.5 text-amber-400 shrink-0" />
                        <span>{fl.facteur}</span>
                      </div>
                      <span className="font-bold">{fl.impact} pts</span>
                    </div>
                  ))}
                </div>
              )}

              {/* Export Buttons (Features F24, F25) */}
              <div className="pt-2 grid grid-cols-2 gap-2">
                <a
                  href={`/api/reports/pdf/${selectedZone.id}?secteur=${sector}`}
                  download
                  className="flex items-center justify-center space-x-1.5 bg-orange-600 hover:bg-orange-500 text-white text-xs font-semibold py-2 px-3 rounded-xl transition shadow-lg shadow-orange-600/20"
                >
                  <FileDown className="w-3.5 h-3.5" />
                  <span>Rapport PDF</span>
                </a>
                <a
                  href={`/api/reports/excel?zone_id=${selectedZone.id}&secteur=${sector}`}
                  download
                  className="flex items-center justify-center space-x-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold py-2 px-3 rounded-xl border border-slate-700 transition"
                >
                  <FileDown className="w-3.5 h-3.5" />
                  <span>Données Excel</span>
                </a>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Bottom Section: Time-Series Predictive Forecasting & Rankings Table */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Time-Series Forecasting Models Comparison (Features F07, F08, F09, F10) */}
        <div className="lg:col-span-7 bg-slate-900/60 border border-slate-800 rounded-2xl p-5 shadow-xl space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <div className="flex items-center space-x-2">
              <TrendingUp className="w-4 h-4 text-sky-400" />
              <h3 className="text-sm font-bold text-slate-100">
                Prévision Temporelle de Fréquentation (J+7) • {selectedZone?.nom_zone}
              </h3>
            </div>
            {/* Model switcher */}
            <div className="flex bg-slate-950 p-1 rounded-xl border border-slate-800 text-xs">
              {["NAIVE", "PROPHET", "XGBOOST"].map((m) => (
                <button
                  key={m}
                  onClick={() => setForecastModel(m)}
                  className={`px-2.5 py-1 rounded-lg font-medium transition ${
                    forecastModel === m
                      ? "bg-sky-500 text-white shadow-md shadow-sky-500/30"
                      : "text-slate-400 hover:text-slate-200"
                  }`}
                >
                  {m === "NAIVE" ? "Naïf J-7" : m}
                </button>
              ))}
            </div>
          </div>

          {/* Simple Clean SVG Visualizer of Forecast with Uncertainty Ribbons */}
          <div className="h-44 w-full bg-slate-950/80 rounded-xl border border-slate-800/80 p-4 flex flex-col justify-between">
            <div className="flex justify-between text-[11px] text-slate-400">
              <span>Projection sur les 7 prochains jours</span>
              <span className="text-sky-400 font-medium">
                Modèle actif : {forecastModel} (WAPE:{" "}
                {forecastModel === "NAIVE" ? "5.0%" : forecastModel === "PROPHET" ? "8.2%" : "7.2%"})
              </span>
            </div>

            {/* Bars of predictions */}
            <div className="flex items-end justify-between h-28 pt-2 px-2">
              {forecastData.map((pt, idx) => {
                const heightPct = Math.min(100, Math.max(20, (pt.valeur_estimee / 1800) * 100));
                return (
                  <div key={idx} className="flex flex-col items-center space-y-1 group">
                    <div className="text-[10px] text-slate-400 opacity-0 group-hover:opacity-100 transition">
                      {Math.round(pt.valeur_estimee)}
                    </div>
                    <div
                      style={{ height: `${heightPct}%` }}
                      className="w-7 rounded-t-lg bg-gradient-to-t from-sky-600 to-sky-400 relative group-hover:from-orange-500 group-hover:to-orange-400 transition"
                    >
                      {/* Uncertainty interval pip */}
                      <div className="absolute -top-1 left-1/2 -translate-x-1/2 w-2 h-2 rounded-full bg-white shadow-md" />
                    </div>
                    <div className="text-[10px] text-slate-500">J+{idx + 1}</div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>

        {/* Global Pilot Ranking Table (Feature F17) */}
        <div className="lg:col-span-5 bg-slate-900/60 border border-slate-800 rounded-2xl p-5 shadow-xl space-y-3">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <div className="flex items-center space-x-2">
              <BarChart3 className="w-4 h-4 text-emerald-400" />
              <h3 className="text-sm font-bold text-slate-100">
                Classement Territorial des Zones
              </h3>
            </div>
            <span className="text-[11px] text-slate-400">{zones.length} zones comparées</span>
          </div>

          <div className="space-y-1.5 max-h-52 overflow-y-auto pr-1">
            {zones.map((z) => (
              <div
                key={z.id}
                onClick={() => setSelectedZone(z)}
                className={`flex items-center justify-between p-2.5 rounded-xl border text-xs cursor-pointer transition ${
                  selectedZone?.id === z.id
                    ? "bg-orange-500/15 border-orange-500/40 text-orange-200"
                    : "bg-slate-950 border-slate-800 hover:bg-slate-800/50 text-slate-300"
                }`}
              >
                <div className="flex items-center space-x-2.5">
                  <span
                    className={`w-5 h-5 rounded-md flex items-center justify-center font-black text-[10px] ${
                      z.rang === 1
                        ? "bg-amber-400 text-slate-950"
                        : z.rang === 2
                        ? "bg-slate-300 text-slate-950"
                        : z.rang === 3
                        ? "bg-amber-700 text-white"
                        : "bg-slate-800 text-slate-400"
                    }`}
                  >
                    {z.rang}
                  </span>
                  <div>
                    <div className="font-semibold text-slate-200">{z.nom_zone}</div>
                    <div className="text-[10px] text-slate-500">{z.nom_commune}</div>
                  </div>
                </div>
                <div className="text-right">
                  <div className="font-bold text-emerald-400">{z.score_ipet} pts</div>
                  <div className="text-[10px] text-slate-500">
                    {z.population.toLocaleString()} hab.
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

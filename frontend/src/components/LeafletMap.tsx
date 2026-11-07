"use client";

import React, { useEffect, useRef, useState } from "react";
import type { Map as LeafletMapType, GeoJSON as LeafletGeoJSONType } from "leaflet";

interface ZoneData {
  id: string;
  nom_commune: string;
  nom_zone: string;
  type_zone: string;
  population: number;
  score_ipet: number;
  score_connectivite?: number;
  coordinates: [number, number][]; // [lon, lat]
  centroid: [number, number]; // [lon, lat]
}

interface POIData {
  id: string;
  nom_enseigne: string;
  type_activite: string;
  commune: string;
  geom: { type: string; coordinates: [number, number] };
}

interface LeafletMapProps {
  zones: ZoneData[];
  selectedZone: ZoneData | null;
  onSelectZone: (zone: ZoneData) => void;
  pois?: POIData[];
}

export default function LeafletMap({
  zones,
  selectedZone,
  onSelectZone,
  pois = [],
}: LeafletMapProps) {
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const mapInstanceRef = useRef<LeafletMapType | null>(null);
  const geojsonLayerRef = useRef<LeafletGeoJSONType | null>(null);
  const markersLayerRef = useRef<any>(null);

  const [tileLayerType, setTileLayerType] = useState<"dark" | "osm" | "voyager">("dark");
  const [showPOIs, setShowPOIs] = useState<boolean>(true);
  const [internalPOIs, setInternalPOIs] = useState<POIData[]>(pois);

  // Fetch POIs if not provided
  useEffect(() => {
    if (pois.length === 0) {
      fetch("/api/pois")
        .then((r) => r.json())
        .then((data) => {
          if (Array.isArray(data)) setInternalPOIs(data);
        })
        .catch((e) => console.error("Error loading POIs for Leaflet map:", e));
    } else {
      setInternalPOIs(pois);
    }
  }, [pois]);

  // Color gradient according to IPET score
  const getColor = (score: number) => {
    if (score >= 80) return "#22c55e"; // Green
    if (score >= 70) return "#f59e0b"; // Amber
    return "#ef4444"; // Red
  };

  // Initialize Leaflet Map
  useEffect(() => {
    if (typeof window === "undefined" || !mapContainerRef.current) return;

    let L: any;
    let map: LeafletMapType;

    const initMap = async () => {
      L = (await import("leaflet")).default;

      // Fix default Leaflet icon paths
      delete (L.Icon.Default.prototype as any)._getIconUrl;
      L.Icon.Default.mergeOptions({
        iconRetinaUrl:
          "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png",
        iconUrl:
          "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png",
        shadowUrl:
          "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
      });

      if (!mapContainerRef.current) return;

      // Center around Abidjan: 5.345, -4.01
      map = L.map(mapContainerRef.current, {
        center: [5.345, -4.01],
        zoom: 12,
        zoomControl: true,
        attributionControl: true,
      });

      mapInstanceRef.current = map;

      // Tile URLs
      const tileUrls = {
        dark: "https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
        osm: "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
        voyager: "https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png",
      };

      const baseTile = L.tileLayer(tileUrls[tileLayerType], {
        maxZoom: 19,
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors & CartoDB',
      });
      baseTile.addTo(map);

      // Layer groups for markers
      markersLayerRef.current = L.layerGroup().addTo(map);

      updatePolygons(L, map);
      updatePOIMarkers(L);
    };

    initMap();

    return () => {
      if (mapInstanceRef.current) {
        mapInstanceRef.current.remove();
        mapInstanceRef.current = null;
      }
    };
  }, []);

  // Update Tile Layer when tileLayerType changes
  useEffect(() => {
    if (!mapInstanceRef.current) return;
    const map = mapInstanceRef.current;

    import("leaflet").then(({ default: L }) => {
      map.eachLayer((layer) => {
        if (layer instanceof L.TileLayer) {
          map.removeLayer(layer);
        }
      });

      const tileUrls = {
        dark: "https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
        osm: "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
        voyager: "https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png",
      };

      L.tileLayer(tileUrls[tileLayerType], {
        maxZoom: 19,
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
      }).addTo(map);

      // Bring GeoJSON & Markers to front
      if (geojsonLayerRef.current) {
        geojsonLayerRef.current.bringToFront();
      }
    });
  }, [tileLayerType]);

  // Update Polygons on zones change
  const updatePolygons = (L: any, map: LeafletMapType) => {
    if (geojsonLayerRef.current) {
      map.removeLayer(geojsonLayerRef.current);
    }

    const geojsonData: any = {
      type: "FeatureCollection",
      features: zones.map((z) => ({
        type: "Feature",
        id: z.id,
        geometry: {
          type: "Polygon",
          coordinates: [z.coordinates],
        },
        properties: {
          ...z,
        },
      })),
    };

    const layer = L.geoJSON(geojsonData, {
      style: (feature: any) => {
        const isSelected = selectedZone?.id === feature.properties.id;
        const color = isSelected ? "#ff7900" : getColor(feature.properties.score_ipet);
        return {
          color: isSelected ? "#ffffff" : color,
          weight: isSelected ? 3.5 : 2,
          opacity: 0.9,
          fillColor: color,
          fillOpacity: isSelected ? 0.65 : 0.45,
        };
      },
      onEachFeature: (feature: any, featureLayer: any) => {
        const z = feature.properties;
        featureLayer.bindTooltip(
          `<strong>${z.nom_zone}</strong><br/>Commune: ${z.nom_commune}<br/>IPET: <span style="color:#f97316;font-weight:bold;">${z.score_ipet}/100</span>`,
          { sticky: true, className: "oemi-leaflet-tooltip" }
        );

        featureLayer.on({
          click: () => {
            onSelectZone(z);
          },
          mouseover: (e: any) => {
            const l = e.target;
            l.setStyle({ fillOpacity: 0.75, weight: 3 });
          },
          mouseout: (e: any) => {
            const l = e.target;
            const isSelected = selectedZone?.id === z.id;
            l.setStyle({
              fillOpacity: isSelected ? 0.65 : 0.45,
              weight: isSelected ? 3.5 : 2,
            });
          },
        });
      },
    }).addTo(map);

    geojsonLayerRef.current = layer;
  };

  // Update POI markers
  const updatePOIMarkers = (L: any) => {
    if (!markersLayerRef.current) return;
    markersLayerRef.current.clearLayers();

    if (!showPOIs) return;

    internalPOIs.forEach((poi) => {
      const coords = poi.geom?.coordinates;
      if (!coords || coords.length < 2) return;
      const [lon, lat] = coords;

      // Custom SVG supermarket icon
      const supermarketIcon = L.divIcon({
        className: "custom-poi-marker",
        html: `
          <div style="background-color: #f97316; border: 2px solid white; border-radius: 50%; width: 26px; height: 26px; display: flex; align-items: center; justify-content: center; box-shadow: 0 2px 8px rgba(0,0,0,0.4);">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
              <path d="m2 7 4.41-4.41A2 2 0 0 1 7.83 2h8.34a2 2 0 0 1 1.42.59L22 7"/>
              <path d="M4 12v8a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-8"/>
              <path d="M15 22v-4a2 2 0 0 0-2-2h-2a2 2 0 0 0-2 2v4"/>
              <path d="M2 7h20"/>
            </svg>
          </div>
        `,
        iconSize: [26, 26],
        iconAnchor: [13, 13],
      });

      const marker = L.marker([lat, lon], { icon: supermarketIcon });
      marker.bindPopup(`
        <div style="font-family: sans-serif; font-size: 12px; color: #0f172a;">
          <strong style="color: #ea580c; font-size: 13px;">${poi.nom_enseigne}</strong><br/>
          <span>Type: <b>Supermarché existant</b></span><br/>
          <span>Commune: <b>${poi.commune}</b></span>
        </div>
      `);
      markersLayerRef.current.addLayer(marker);
    });
  };

  // Re-run polygon & marker updates when zones, selectedZone or showPOIs changes
  useEffect(() => {
    if (!mapInstanceRef.current) return;
    import("leaflet").then(({ default: L }) => {
      updatePolygons(L, mapInstanceRef.current!);
      updatePOIMarkers(L);

      // Pan to selected zone if changed
      if (selectedZone) {
        mapInstanceRef.current!.panTo([
          selectedZone.centroid[1],
          selectedZone.centroid[0],
        ]);
      }
    });
  }, [zones, selectedZone, showPOIs, internalPOIs]);

  return (
    <div className="relative w-full h-[540px] rounded-2xl overflow-hidden border border-slate-800 bg-slate-950 shadow-2xl">
      {/* Real Map Container */}
      <div ref={mapContainerRef} className="w-full h-full z-0" />

      {/* Top Floating Controls */}
      <div className="absolute top-4 left-4 z-[500] flex flex-wrap items-center gap-2">
        {/* Layer style switcher */}
        <div className="flex bg-slate-900/90 backdrop-blur-md border border-slate-800 p-1 rounded-xl shadow-lg">
          <button
            onClick={() => setTileLayerType("dark")}
            className={`px-2.5 py-1 text-xs font-semibold rounded-lg transition ${
              tileLayerType === "dark"
                ? "bg-orange-500 text-white shadow-md shadow-orange-500/20"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            CartoDB Dark
          </button>
          <button
            onClick={() => setTileLayerType("osm")}
            className={`px-2.5 py-1 text-xs font-semibold rounded-lg transition ${
              tileLayerType === "osm"
                ? "bg-orange-500 text-white shadow-md shadow-orange-500/20"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            OpenStreetMap Réel
          </button>
          <button
            onClick={() => setTileLayerType("voyager")}
            className={`px-2.5 py-1 text-xs font-semibold rounded-lg transition ${
              tileLayerType === "voyager"
                ? "bg-orange-500 text-white shadow-md shadow-orange-500/20"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            Voyager / Rues
          </button>
        </div>

        {/* POI Toggle Button */}
        <button
          onClick={() => setShowPOIs(!showPOIs)}
          className={`px-3 py-1.5 rounded-xl border text-xs font-semibold backdrop-blur-md transition shadow-lg flex items-center space-x-1.5 ${
            showPOIs
              ? "bg-amber-500/20 border-amber-500/40 text-amber-300"
              : "bg-slate-900/80 border-slate-800 text-slate-400 hover:text-slate-200"
          }`}
        >
          <span className="w-2 h-2 rounded-full bg-amber-400" />
          <span>Supermarchés Existants ({internalPOIs.length})</span>
        </button>
      </div>

      {/* Floating Legend Bottom Right */}
      <div className="absolute bottom-4 right-4 z-[500] px-3.5 py-2.5 rounded-xl bg-slate-900/90 backdrop-blur-md border border-slate-800 text-[11px] text-slate-300 space-y-1.5 shadow-xl max-w-xs">
        <div className="font-semibold text-slate-200 border-b border-slate-800 pb-1 flex items-center justify-between">
          <span>Potentiel d&apos;Implantation (IPET)</span>
          <span className="text-[10px] text-orange-400 font-bold">Tuiles OSM</span>
        </div>
        <div className="flex items-center space-x-2">
          <span className="w-3 h-3 rounded bg-emerald-500 inline-block border border-white/20" />
          <span>Fort potentiel d&apos;implantation (≥ 80)</span>
        </div>
        <div className="flex items-center space-x-2">
          <span className="w-3 h-3 rounded bg-amber-500 inline-block border border-white/20" />
          <span>Potentiel intermédiaire (70 - 79)</span>
        </div>
        <div className="flex items-center space-x-2">
          <span className="w-3 h-3 rounded bg-rose-500 inline-block border border-white/20" />
          <span>Potentiel à consolider (&lt; 70)</span>
        </div>
        <div className="flex items-center space-x-2 pt-1 border-t border-slate-800 text-[10px] text-amber-400">
          <span className="w-2.5 h-2.5 rounded-full bg-orange-500 inline-block border border-white" />
          <span>Supermarchés / Supérettes existants</span>
        </div>
      </div>
    </div>
  );
}

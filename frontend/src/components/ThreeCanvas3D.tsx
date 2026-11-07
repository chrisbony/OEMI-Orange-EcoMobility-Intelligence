"use client";

import React, { useEffect, useRef, useState } from "react";
import * as THREE from "three";

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

interface ThreeCanvas3DProps {
  zones: ZoneData[];
  selectedZone: ZoneData | null;
  onSelectZone: (zone: ZoneData) => void;
  renderMode?: "3D_WEBGL" | "2D_CANVAS";
}

export default function ThreeCanvas3D({
  zones,
  selectedZone,
  onSelectZone,
  renderMode = "3D_WEBGL",
}: ThreeCanvas3DProps) {
  const mountRef = useRef<HTMLDivElement>(null);
  const [hoveredZone, setHoveredZone] = useState<ZoneData | null>(null);
  const [is2DFallback, setIs2DFallback] = useState(renderMode === "2D_CANVAS");

  // Center coordinate around Abidjan: lon -4.00, lat 5.34
  const CENTER_LON = -4.00;
  const CENTER_LAT = 5.34;
  const SCALE = 2800; // coordinate scaling for 3D units

  useEffect(() => {
    if (is2DFallback || !mountRef.current) return;

    const container = mountRef.current;
    const width = container.clientWidth;
    const height = container.clientHeight;

    // 1. Scene, Camera, Renderer
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x0a0f1d);
    scene.fog = new THREE.FogExp2(0x0a0f1d, 0.0012);

    const camera = new THREE.PerspectiveCamera(45, width / height, 1, 3000);
    camera.position.set(0, -220, 260);
    camera.lookAt(0, 0, 0);

    let renderer: THREE.WebGLRenderer;
    try {
      renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true, powerPreference: "high-performance" });
      renderer.setSize(width, height);
      renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
      renderer.shadowMap.enabled = true;
      container.appendChild(renderer.domElement);
    } catch (e) {
      console.warn("WebGL not available or context lost, falling back to 2D:", e);
      setIs2DFallback(true);
      return;
    }

    // 2. Lights
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.85);
    scene.add(ambientLight);

    const dirLight = new THREE.DirectionalLight(0xffaa44, 1.2);
    dirLight.position.set(100, -100, 250);
    dirLight.castShadow = true;
    scene.add(dirLight);

    const blueLight = new THREE.DirectionalLight(0x38bdf8, 0.7);
    blueLight.position.set(-150, 100, 150);
    scene.add(blueLight);

    // 3. Grid Ground / Lagoon Water effect
    const gridHelper = new THREE.GridHelper(600, 30, 0x1e293b, 0x0f172a);
    gridHelper.rotation.x = Math.PI / 2;
    gridHelper.position.z = -1;
    scene.add(gridHelper);

    // Group for interactable objects
    const interactiveGroup = new THREE.Group();
    scene.add(interactiveGroup);

    // Map zone id to Mesh
    const meshesByZoneId = new Map<string, THREE.Mesh>();

    // Helper: converts lon/lat to 3D X/Y
    const project = (lon: number, lat: number): [number, number] => {
      const x = (lon - CENTER_LON) * SCALE;
      const y = (lat - CENTER_LAT) * SCALE;
      return [x, y];
    };

    // Color gradient helper according to IPET score
    const getScoreColor = (score: number) => {
      if (score >= 80) return 0x22c55e; // Green
      if (score >= 70) return 0xf59e0b; // Amber
      return 0xef4444; // Red
    };

    // 4. Create 3D Extruded Polygons for each zone
    zones.forEach((z) => {
      const shape = new THREE.Shape();
      const coords = z.coordinates;
      if (coords.length > 0) {
        const [startX, startY] = project(coords[0][0], coords[0][1]);
        shape.moveTo(startX, startY);
        for (let i = 1; i < coords.length; i++) {
          const [px, py] = project(coords[i][0], coords[i][1]);
          shape.lineTo(px, py);
        }
      }

      // Height scaled to IPET score (Feature F20)
      const extrusionHeight = Math.max(6, (z.score_ipet / 100) * 22);

      const geom = new THREE.ExtrudeGeometry(shape, {
        depth: extrusionHeight,
        bevelEnabled: true,
        bevelSegments: 2,
        steps: 1,
        bevelSize: 0.8,
        bevelThickness: 0.8,
      });

      const isSelected = selectedZone?.id === z.id;
      const baseColor = isSelected ? 0xff7900 : getScoreColor(z.score_ipet);

      const mat = new THREE.MeshStandardMaterial({
        color: baseColor,
        roughness: 0.4,
        metalness: 0.25,
        transparent: true,
        opacity: isSelected ? 0.95 : 0.75,
      });

      const mesh = new THREE.Mesh(geom, mat);
      mesh.userData = { zone: z };
      interactiveGroup.add(mesh);
      meshesByZoneId.set(z.id, mesh);

      // Add wireframe edge outline for high-tech look
      const wireGeom = new THREE.EdgesGeometry(geom);
      const wireMat = new THREE.LineBasicMaterial({
        color: isSelected ? 0xffffff : 0x38bdf8,
        linewidth: 1,
        transparent: true,
        opacity: 0.6,
      });
      const wire = new THREE.LineSegments(wireGeom, wireMat);
      mesh.add(wire);

      // 5. 3D Density & IPET Pillars at centroid (Feature F21)
      const [cx, cy] = project(z.centroid[0], z.centroid[1]);
      const pillarHeight = Math.max(15, (z.score_ipet / 100) * 85);
      const pillarGeom = new THREE.CylinderGeometry(2.5, 3.5, pillarHeight, 16);
      pillarGeom.rotateX(Math.PI / 2); // vertical along Z
      pillarGeom.translate(0, 0, pillarHeight / 2 + extrusionHeight);

      const pillarMat = new THREE.MeshStandardMaterial({
        color: baseColor,
        emissive: baseColor,
        emissiveIntensity: isSelected ? 0.6 : 0.25,
        roughness: 0.2,
      });
      const pillar = new THREE.Mesh(pillarGeom, pillarMat);
      interactiveGroup.add(pillar);
    });

    // 6. 3D Mobility Flow Arcs with animated particles (Feature F22)
    // Draw arcs from Yopougon towards Cocody & Marcory
    const flowCurves: { curve: THREE.QuadraticBezierCurve3; particles: THREE.Points }[] = [];

    const flowPairs: [string, string][] = [
      ["ci-abidjan-yopougon-siporex", "ci-abidjan-cocody-angre"],
      ["ci-abidjan-yopougon-toitsrouges", "ci-abidjan-marcory-zone4"],
      ["ci-abidjan-cocody-deuxplateaux", "ci-abidjan-marcory-bietry"],
    ];

    flowPairs.forEach(([origId, destId]) => {
      const origZone = zones.find((z) => z.id === origId);
      const destZone = zones.find((z) => z.id === destId);
      if (!origZone || !destZone) return;

      const [ox, oy] = project(origZone.centroid[0], origZone.centroid[1]);
      const [dx, dy] = project(destZone.centroid[0], destZone.centroid[1]);

      const midX = (ox + dx) / 2;
      const midY = (oy + dy) / 2;
      const dist = Math.hypot(dx - ox, dy - oy);
      const midZ = Math.min(80, dist * 0.45); // Arc height curvature (F22)

      const start = new THREE.Vector3(ox, oy, 25);
      const control = new THREE.Vector3(midX, midY, midZ + 30);
      const end = new THREE.Vector3(dx, dy, 25);

      const curve = new THREE.QuadraticBezierCurve3(start, control, end);
      const points = curve.getPoints(50);
      const curveGeom = new THREE.BufferGeometry().setFromPoints(points);
      const curveMat = new THREE.LineBasicMaterial({ color: 0xff7900, transparent: true, opacity: 0.45 });
      const curveLine = new THREE.Line(curveGeom, curveMat);
      scene.add(curveLine);

      // Traveling particles along curve
      const particleCount = 12;
      const pGeom = new THREE.BufferGeometry();
      const pPositions = new Float32Array(particleCount * 3);
      pGeom.setAttribute("position", new THREE.BufferAttribute(pPositions, 3));
      const pMat = new THREE.PointsMaterial({ color: 0xffedd5, size: 4, transparent: true, opacity: 0.9 });
      const particles = new THREE.Points(pGeom, pMat);
      scene.add(particles);

      flowCurves.push({ curve, particles });
    });

    // 7. Raycasting for Click & Hover interactions
    const raycaster = new THREE.Raycaster();
    const mouse = new THREE.Vector2();

    const onPointerMove = (e: MouseEvent) => {
      const rect = container.getBoundingClientRect();
      mouse.x = ((e.clientX - rect.left) / rect.width) * 2 - 1;
      mouse.y = -((e.clientY - rect.top) / rect.height) * 2 + 1;

      raycaster.setFromCamera(mouse, camera);
      const intersects = raycaster.intersectObjects(interactiveGroup.children);
      if (intersects.length > 0) {
        const target = intersects[0].object;
        if (target.userData?.zone) {
          setHoveredZone(target.userData.zone);
          container.style.cursor = "pointer";
          return;
        }
      }
      setHoveredZone(null);
      container.style.cursor = "grab";
    };

    const onClick = (e: MouseEvent) => {
      const rect = container.getBoundingClientRect();
      mouse.x = ((e.clientX - rect.left) / rect.width) * 2 - 1;
      mouse.y = -((e.clientY - rect.top) / rect.height) * 2 + 1;

      raycaster.setFromCamera(mouse, camera);
      const intersects = raycaster.intersectObjects(interactiveGroup.children);
      if (intersects.length > 0) {
        const target = intersects[0].object;
        if (target.userData?.zone) {
          onSelectZone(target.userData.zone);
        }
      }
    };

    // Simple camera drag rotation
    let isDragging = false;
    let prevMouseX = 0;
    let prevMouseY = 0;

    const onMouseDown = (e: MouseEvent) => {
      isDragging = true;
      prevMouseX = e.clientX;
      prevMouseY = e.clientY;
      container.style.cursor = "grabbing";
    };

    const onMouseUp = () => {
      isDragging = false;
      container.style.cursor = "grab";
    };

    const onMouseMoveDrag = (e: MouseEvent) => {
      if (!isDragging) return;
      const dx = e.clientX - prevMouseX;
      const dy = e.clientY - prevMouseY;
      prevMouseX = e.clientX;
      prevMouseY = e.clientY;

      interactiveGroup.rotation.z += dx * 0.005;
      camera.position.z = Math.max(100, Math.min(450, camera.position.z - dy * 0.4));
      camera.lookAt(0, 0, 0);
    };

    container.addEventListener("mousemove", onPointerMove);
    container.addEventListener("click", onClick);
    container.addEventListener("mousedown", onMouseDown);
    window.addEventListener("mouseup", onMouseUp);
    window.addEventListener("mousemove", onMouseMoveDrag);

    // 8. Animation loop
    let reqId: number;
    let clock = new THREE.Clock();

    const animate = () => {
      reqId = requestAnimationFrame(animate);
      const elapsedTime = clock.getElapsedTime();

      // Gentle auto-rotation
      if (!isDragging) {
        interactiveGroup.rotation.z += 0.0008;
      }

      // Animate flow particles
      flowCurves.forEach(({ curve, particles }) => {
        const positions = particles.geometry.attributes.position.array as Float32Array;
        const count = positions.length / 3;
        for (let i = 0; i < count; i++) {
          const t = ((elapsedTime * 0.15 + i / count) % 1.0);
          const pt = curve.getPoint(t);
          positions[i * 3] = pt.x;
          positions[i * 3 + 1] = pt.y;
          positions[i * 3 + 2] = pt.z;
        }
        particles.geometry.attributes.position.needsUpdate = true;
      });

      renderer.render(scene, camera);
    };

    animate();

    // 9. Resize handler
    const onResize = () => {
      if (!container) return;
      const w = container.clientWidth;
      const h = container.clientHeight;
      camera.aspect = w / h;
      camera.updateProjectionMatrix();
      renderer.setSize(w, h);
    };
    window.addEventListener("resize", onResize);

    return () => {
      cancelAnimationFrame(reqId);
      window.removeEventListener("resize", onResize);
      container.removeEventListener("mousemove", onPointerMove);
      container.removeEventListener("click", onClick);
      container.removeEventListener("mousedown", onMouseDown);
      window.removeEventListener("mouseup", onMouseUp);
      window.removeEventListener("mousemove", onMouseMoveDrag);
      if (renderer.domElement && container.contains(renderer.domElement)) {
        container.removeChild(renderer.domElement);
      }
      renderer.dispose();
    };
  }, [zones, selectedZone, is2DFallback]);

  return (
    <div className="relative w-full h-[520px] rounded-2xl overflow-hidden border border-slate-800 bg-slate-950 shadow-2xl">
      {/* 2D Canvas Fallback View (F20.05) */}
      {is2DFallback ? (
        <div className="w-full h-full flex flex-col items-center justify-center p-6 text-center bg-slate-900">
          <div className="text-orange-500 font-bold mb-2">Mode Cartographique 2D de Secours</div>
          <p className="text-xs text-slate-400 max-w-md mb-6">
            Rendu 2D actif (contexte WebGL désactivé ou fallback sécurité). Sélection des zones par liste.
          </p>
          <div className="grid grid-cols-3 gap-3 max-w-lg w-full">
            {zones.map((z) => (
              <button
                key={z.id}
                onClick={() => onSelectZone(z)}
                className={`p-3 rounded-xl border text-left transition ${
                  selectedZone?.id === z.id
                    ? "border-orange-500 bg-orange-500/20 text-orange-200"
                    : "border-slate-800 bg-slate-800/60 hover:bg-slate-800 text-slate-200"
                }`}
              >
                <div className="text-xs font-semibold">{z.nom_zone}</div>
                <div className="text-[10px] text-slate-400">{z.nom_commune}</div>
                <div className="text-xs font-bold text-orange-400 mt-1">IPET {z.score_ipet}</div>
              </button>
            ))}
          </div>
          <button
            onClick={() => setIs2DFallback(false)}
            className="mt-6 px-4 py-2 text-xs bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg transition"
          >
            Tenter de réactiver le rendu 3D WebGL
          </button>
        </div>
      ) : (
        <div ref={mountRef} className="w-full h-full relative cursor-grab" />
      )}

      {/* Top Floating Controls */}
      <div className="absolute top-4 left-4 z-10 flex items-center space-x-2">
        <div className="px-3 py-1.5 rounded-lg bg-slate-900/80 backdrop-blur-md border border-slate-700/60 text-xs font-medium text-slate-200 flex items-center space-x-2 shadow-lg">
          <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-pulse" />
          <span>Three.js 3D WebGL</span>
        </div>
        <button
          onClick={() => setIs2DFallback(!is2DFallback)}
          className="px-3 py-1.5 rounded-lg bg-slate-900/80 backdrop-blur-md border border-slate-700/60 text-xs text-slate-400 hover:text-slate-200 hover:border-slate-500 transition shadow-lg"
        >
          {is2DFallback ? "Bascule 3D" : "Bascule 2D"}
        </button>
      </div>

      {/* 3D Legend & Controls Overlay */}
      <div className="absolute top-4 right-4 z-10 px-3 py-2 rounded-xl bg-slate-900/85 backdrop-blur-md border border-slate-800 text-[11px] text-slate-300 space-y-1.5 shadow-xl">
        <div className="font-semibold text-slate-200 mb-1">Potentiel Territorial (IPET)</div>
        <div className="flex items-center space-x-2">
          <span className="w-3 h-3 rounded bg-emerald-500 inline-block" />
          <span>Fort potentiel (IPET ≥ 80)</span>
        </div>
        <div className="flex items-center space-x-2">
          <span className="w-3 h-3 rounded bg-amber-500 inline-block" />
          <span>Potentiel modéré (70 - 79)</span>
        </div>
        <div className="flex items-center space-x-2">
          <span className="w-3 h-3 rounded bg-rose-500 inline-block" />
          <span>Potentiel à consolider (&lt; 70)</span>
        </div>
        <div className="flex items-center space-x-2 pt-1 border-t border-slate-800 text-[10px] text-orange-400">
          <span className="w-3 h-0.5 bg-orange-500 inline-block" />
          <span>Flux de mobilité pendulaire</span>
        </div>
      </div>

      {/* Hover Info Tooltip */}
      {hoveredZone && (
        <div className="absolute bottom-4 left-4 z-10 px-4 py-2.5 rounded-xl bg-slate-900/90 backdrop-blur-md border border-orange-500/50 shadow-2xl text-xs space-y-0.5 pointer-events-none">
          <div className="font-bold text-slate-100">{hoveredZone.nom_zone}</div>
          <div className="text-[11px] text-slate-400">
            Commune de {hoveredZone.nom_commune} • {hoveredZone.type_zone}
          </div>
          <div className="text-orange-400 font-semibold pt-1">
            Score IPET: {hoveredZone.score_ipet}/100 • Pop: {hoveredZone.population.toLocaleString()} hab.
          </div>
        </div>
      )}

      {/* Camera Guidance Notice */}
      <div className="absolute bottom-4 right-4 z-10 text-[10px] text-slate-500 pointer-events-none">
        Faites glisser pour pivoter • Cliquez sur une zone pour l&apos;inspecter
      </div>
    </div>
  );
}

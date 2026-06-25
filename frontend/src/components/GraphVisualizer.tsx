import React, { useEffect, useRef } from 'react';
import * as THREE from 'three';

interface GraphSource {
  source_type: string;
  source_node_name?: string;
  target_node_name?: string;
  name?: string;
  fact?: string;
}

interface GraphVisualizerProps {
  sources: GraphSource[];
  onNodeHover: (node: { name: string; type: string; fact: string } | null) => void;
  onStatsChange: (nodesCount: number, edgesCount: number) => void;
}

export const GraphVisualizer: React.FC<GraphVisualizerProps> = ({
  sources,
  onNodeHover,
  onStatsChange
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const sceneRef = useRef<THREE.Scene | null>(null);
  const cameraRef = useRef<THREE.PerspectiveCamera | null>(null);
  const rendererRef = useRef<THREE.WebGLRenderer | null>(null);
  const nodeGroupRef = useRef<THREE.Group | null>(null);
  const linkGroupRef = useRef<THREE.Group | null>(null);

  // Default demo graph if no graph sources are retrieved
  const initialDemoSources = [
    { source_node_name: "FPT Software", target_node_name: "NVIDIA", name: "PARTNER_OF", fact: "FPT Software hợp tác phát triển AI với NVIDIA" },
    { source_node_name: "NVIDIA", target_node_name: "AI Factory", name: "BUILDS", fact: "NVIDIA xây dựng nhà máy AI Factory tại Việt Nam" },
    { source_node_name: "FPT Software", target_node_name: "AI Factory", name: "OPERATES", fact: "FPT Software vận hành AI Factory" },
    { source_node_name: "Phạm Minh Tuấn", target_node_name: "FPT Software", name: "CEO_OF", fact: "Phạm Minh Tuấn là CEO của FPT Software" }
  ];

  useEffect(() => {
    if (!containerRef.current) return;

    const container = containerRef.current;
    const width = container.clientWidth || window.innerWidth;
    const height = container.clientHeight || window.innerHeight;

    const scene = new THREE.Scene();
    sceneRef.current = scene;

    const camera = new THREE.PerspectiveCamera(75, width / height, 0.1, 1000);
    camera.position.z = 7;
    cameraRef.current = camera;

    const renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true });
    renderer.setSize(width, height);
    renderer.setPixelRatio(window.devicePixelRatio || 1);
    container.appendChild(renderer.domElement);
    rendererRef.current = renderer;

    const nodeGroup = new THREE.Group();
    const linkGroup = new THREE.Group();
    scene.add(nodeGroup);
    scene.add(linkGroup);
    nodeGroupRef.current = nodeGroup;
    linkGroupRef.current = linkGroup;

    const ambientLight = new THREE.AmbientLight(0xffffff, 0.6);
    scene.add(ambientLight);

    const pointLight = new THREE.PointLight(0x22D3EE, 1, 100);
    pointLight.position.set(10, 10, 10);
    scene.add(pointLight);

    // Animation Loop
    let animationFrameId: number;
    const animate = () => {
      animationFrameId = requestAnimationFrame(animate);
      nodeGroup.rotation.y += 0.001;
      linkGroup.rotation.y += 0.001;
      renderer.render(scene, camera);
    };
    animate();

    // Resize Handler
    const handleResize = () => {
      if (!containerRef.current) return;
      const w = containerRef.current.clientWidth;
      const h = containerRef.current.clientHeight;
      camera.aspect = w / h;
      camera.updateProjectionMatrix();
      renderer.setSize(w, h);
    };
    window.addEventListener('resize', handleResize);

    // Raycaster for Hover detection
    const raycaster = new THREE.Raycaster();
    const mouse = new THREE.Vector2();

    const handleMouseMove = (event: MouseEvent) => {
      if (!rendererRef.current) return;
      const rect = rendererRef.current.domElement.getBoundingClientRect();
      mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
      mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;

      raycaster.setFromCamera(mouse, camera);
      const intersects = raycaster.intersectObjects(nodeGroup.children);

      if (intersects.length > 0) {
        document.body.style.cursor = 'pointer';
        const hoveredNode = intersects[0].object as THREE.Mesh;

        // Reset others
        nodeGroup.children.forEach((child: any) => {
          child.scale.set(1, 1, 1);
          if (child.material && 'emissiveIntensity' in child.material) {
            child.material.emissiveIntensity = 0.5;
          }
        });

        // Highlight hovered node
        hoveredNode.scale.set(1.4, 1.4, 1.4);
        const material = hoveredNode.material as THREE.MeshPhongMaterial;
        if (material && 'emissiveIntensity' in material) {
          material.emissiveIntensity = 1.2;
        }

        // Trigger callback with metadata
        onNodeHover(hoveredNode.userData as any);
      } else {
        document.body.style.cursor = 'default';
        nodeGroup.children.forEach((child: any) => {
          child.scale.set(1, 1, 1);
          if (child.material && 'emissiveIntensity' in child.material) {
            child.material.emissiveIntensity = 0.5;
          }
        });
        onNodeHover(null);
      }
    };
    container.addEventListener('mousemove', handleMouseMove);

    return () => {
      cancelAnimationFrame(animationFrameId);
      window.removeEventListener('resize', handleResize);
      container.removeEventListener('mousemove', handleMouseMove);
      if (rendererRef.current && rendererRef.current.domElement) {
        container.removeChild(rendererRef.current.domElement);
      }
    };
  }, [onNodeHover]);

  // Update graph on sources change
  useEffect(() => {
    const nodeGroup = nodeGroupRef.current;
    const linkGroup = linkGroupRef.current;
    if (!nodeGroup || !linkGroup) return;

    // Clear existing children
    while (nodeGroup.children.length > 0) {
      nodeGroup.remove(nodeGroup.children[0]);
    }
    while (linkGroup.children.length > 0) {
      linkGroup.remove(linkGroup.children[0]);
    }

    // Filter actual graph sources
    let actualSources = sources.filter(
      (src) => src.source_type === 'graph' && src.source_node_name
    );
    const hasGraphData = actualSources.length > 0;
    const displaySources = hasGraphData ? actualSources : initialDemoSources;

    const nodeNames = new Set<string>();
    const edges: Array<{ source: string; target: string; type: string; fact: string }> = [];

    displaySources.forEach((src) => {
      const sName = src.source_node_name || 'Unknown Source';
      const tName = src.target_node_name || 'Unknown Target';
      nodeNames.add(sName);
      nodeNames.add(tName);
      edges.push({
        source: sName,
        target: tName,
        type: src.name || 'RELATES_TO',
        fact: src.fact || '',
      });
    });

    const nodePositions: { [key: string]: THREE.Vector3 } = {};
    const nodeArray = Array.from(nodeNames);

    const nodeGeometry = new THREE.SphereGeometry(0.18, 32, 32);
    const cyanMaterial = new THREE.MeshPhongMaterial({
      color: 0x22d3ee,
      emissive: 0x22d3ee,
      emissiveIntensity: 0.5,
    });
    const emeraldMaterial = new THREE.MeshPhongMaterial({
      color: 0x10b981,
      emissive: 0x10b981,
      emissiveIntensity: 0.5,
    });

    nodeArray.forEach((name, index) => {
      const material = index % 2 === 0 ? cyanMaterial : emeraldMaterial;
      const nodeMesh = new THREE.Mesh(nodeGeometry, material);

      const angle = (index / nodeArray.length) * Math.PI * 2;
      const radius = 2.5 + Math.random() * 0.5;
      const x = Math.cos(angle) * radius;
      const y = (Math.random() - 0.5) * 3;
      const z = Math.sin(angle) * radius;

      nodeMesh.position.set(x, y, z);
      nodePositions[name] = nodeMesh.position;

      // Meta information
      nodeMesh.userData = {
        name,
        type: index % 2 === 0 ? 'Organization' : 'Person',
        fact: edges.find((e) => e.source === name || e.target === name)?.fact || `Thực thể: ${name}`,
      };

      nodeGroup.add(nodeMesh);
    });

    const linkMaterial = new THREE.LineBasicMaterial({
      color: 0x22d3ee,
      transparent: true,
      opacity: 0.3,
    });

    edges.forEach((edge) => {
      const startPos = nodePositions[edge.source];
      const endPos = nodePositions[edge.target];
      if (startPos && endPos) {
        const points = [startPos, endPos];
        const geometry = new THREE.BufferGeometry().setFromPoints(points);
        const line = new THREE.Line(geometry, linkMaterial);
        linkGroup.add(line);
      }
    });

    onStatsChange(nodeArray.length, edges.length);
  }, [sources, onStatsChange]);

  return <div ref={containerRef} className="w-full h-full" />;
};

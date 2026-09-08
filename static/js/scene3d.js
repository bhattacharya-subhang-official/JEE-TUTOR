/* 3D scene builder — renders the LLM "scene" JSON with three.js (r128) + labels + orbit */
(function () {
  /* ---- SimpleOrbit: minimal drag-rotate / wheel-zoom controls ---- */
  function SimpleOrbit(camera, dom) {
    this.camera = camera; this.dom = dom;
    this.target = new THREE.Vector3();
    this.sph = new THREE.Spherical().setFromVector3(camera.position.clone().sub(this.target));
    this._d = false; this._px = 0; this._py = 0;
    const self = this;
    dom.style.touchAction = 'none';
    dom.addEventListener('pointerdown', (e) => { self._d = true; self._px = e.clientX; self._py = e.clientY; });
    window.addEventListener('pointerup', () => { self._d = false; });
    window.addEventListener('pointermove', (e) => {
      if (!self._d) return;
      const dx = e.clientX - self._px, dy = e.clientY - self._py;
      self._px = e.clientX; self._py = e.clientY;
      self.sph.theta -= dx * 0.006;
      self.sph.phi = Math.max(0.05, Math.min(Math.PI - 0.05, self.sph.phi - dy * 0.006));
    });
    dom.addEventListener('wheel', (e) => {
      e.preventDefault();
      self.sph.radius = Math.max(0.3, Math.min(800, self.sph.radius * (e.deltaY > 0 ? 1.1 : 0.9)));
    }, { passive: false });
    this.update = function () {
      const p = new THREE.Vector3().setFromSpherical(this.sph).add(this.target);
      this.camera.position.copy(p);
      this.camera.lookAt(this.target);
    };
    this.update();
  }
  window.SimpleOrbit = SimpleOrbit;

  const PALETTE = { accent: 0x6ea8ff, gold: 0xffd166, green: 0x4ade80, red: 0xf87171, purple: 0xc084fc };

  function col(c, fallback) {
    if (!c) return fallback;
    try { return new THREE.Color(c); } catch (e) { return fallback; }
  }

  function v3(a) { return new THREE.Vector3(a[0] || 0, a[1] || 0, a[2] || 0); }

  function cylinderBetween(from, to, r, color, opacity) {
    const a = v3(from), b = v3(to);
    const dir = new THREE.Vector3().subVectors(b, a);
    const len = dir.length() || 0.0001;
    const geo = new THREE.CylinderGeometry(r, r, len, 24);
    const mat = new THREE.MeshStandardMaterial({ color, roughness: 0.45, metalness: 0.15, transparent: opacity < 1, opacity: opacity == null ? 1 : opacity });
    const mesh = new THREE.Mesh(geo, mat);
    mesh.position.copy(a).add(b).multiplyScalar(0.5);
    mesh.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), dir.clone().normalize());
    return mesh;
  }

  function coneBetween(from, to, r, color) {
    const a = v3(from), b = v3(to);
    const dir = new THREE.Vector3().subVectors(b, a);
    const len = dir.length() || 0.0001;
    const geo = new THREE.ConeGeometry(r, len, 28);
    const mesh = new THREE.Mesh(geo, new THREE.MeshStandardMaterial({ color, roughness: 0.4 }));
    mesh.position.copy(a).add(b).multiplyScalar(0.5);
    mesh.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), dir.clone().normalize());
    return mesh;
  }

  window.buildScene = function (container, scene) {
    scene = scene || {};
    const width = container.clientWidth || 640;
    const height = container.clientHeight || 440;

    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: false });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.setSize(width, height);
    renderer.setClearColor(col(scene.background, new THREE.Color('#0b0e1a')));
    container.appendChild(renderer.domElement);

    const labels = [];
    const camera = new THREE.PerspectiveCamera(50, width / height, 0.1, 2000);

    const world = new THREE.Group();
    // estimate scene radius for camera fit + label scale
    let maxR = 1;
    const objs = scene.objects || [];

    // first pass: extent
    objs.forEach((o) => {
      [['pos', 1], ['from', 1], ['to', 1]].forEach(([k]) => {
        if (o[k]) maxR = Math.max(maxR, v3(o[k]).length() + (o.r || 1));
      });
      if (o.type === 'box' && o.pos) maxR = Math.max(maxR, v3(o.pos).length() + 0.5 * Math.max(...(o.size || [1, 1, 1])));
    });
    camera.position.set(maxR * 1.9, maxR * 1.35, maxR * 2.3);

    // lights
    world.add(new THREE.AmbientLight(0xbfd0ff, 0.55));
    const dir = new THREE.DirectionalLight(0xffffff, 0.95);
    dir.position.set(maxR * 3, maxR * 5, maxR * 2);
    world.add(dir);
    const fill = new THREE.DirectionalLight(0x8b5cf6, 0.25);
    fill.position.set(-maxR * 3, maxR * 2, -maxR * 2);
    world.add(fill);

    if (scene.grid) {
      const grid = new THREE.GridHelper(maxR * 2.2, 14, 0x3a4270, 0x232a4d);
      grid.material.transparent = true; grid.material.opacity = 0.5;
      world.add(grid);
    }
    if (scene.axes !== false) {
      const L = maxR * 0.85;
      const mk = (d, c) => {
        const arr = new THREE.ArrowHelper(d, new THREE.Vector3(0, 0, 0), L, c, L * 0.09, L * 0.045);
        arr.line.material.transparent = true; arr.line.material.opacity = 0.8;
        return arr;
      };
      world.add(mk(new THREE.Vector3(1, 0, 0), 0xf87171));
      world.add(mk(new THREE.Vector3(0, 1, 0), 0x4ade80));
      world.add(mk(new THREE.Vector3(0, 0, 1), 0x6ea8ff));
      labels.push({ pos: new THREE.Vector3(L * 1.12, 0, 0), text: 'x', color: '#f8a5a5' });
      labels.push({ pos: new THREE.Vector3(0, L * 1.12, 0), text: 'y', color: '#9df0bd' });
      labels.push({ pos: new THREE.Vector3(0, 0, L * 1.12), text: 'z', color: '#a8c8ff' });
    }

    // objects
    objs.forEach((o) => {
      const opacity = o.opacity == null ? 1 : o.opacity;
      const base = { roughness: 0.45, metalness: 0.15, transparent: opacity < 1, opacity };
      switch (o.type) {
        case 'sphere': {
          const m = new THREE.Mesh(new THREE.SphereGeometry(o.r || 0.5, 40, 28),
            new THREE.MeshStandardMaterial({ color: col(o.color, PALETTE.accent), ...base }));
          m.position.copy(v3(o.pos)); world.add(m); break;
        }
        case 'box': {
          const s = o.size || [1, 1, 1];
          const m = new THREE.Mesh(new THREE.BoxGeometry(...s),
            new THREE.MeshStandardMaterial({ color: col(o.color, 0x4f8cff), ...base }));
          m.position.copy(v3(o.pos));
          if (o.rotation) m.rotation.set(o.rotation[0] || 0, o.rotation[1] || 0, o.rotation[2] || 0);
          world.add(m);
          // edges
          const eg = new THREE.EdgesGeometry(m.geometry);
          const edges = new THREE.LineSegments(eg, new THREE.LineBasicMaterial({ color: 0xdfe6f5, transparent: true, opacity: 0.35 }));
          m.add(edges); break;
        }
        case 'cylinder': {
          world.add(cylinderBetween(o.from, o.to, o.r == null ? 0.08 : o.r, col(o.color, PALETTE.gold), opacity)); break;
        }
        case 'cone': {
          world.add(coneBetween(o.from, o.to, o.r == null ? 0.3 : o.r, col(o.color, PALETTE.gold))); break;
        }
        case 'arrow': {
          const a = v3(o.from), b = v3(o.to);
          const d = new THREE.Vector3().subVectors(b, a);
          const len = d.length() || 0.0001;
          const arr = new THREE.ArrowHelper(d.clone().normalize(), a, len, col(o.color, PALETTE.red).getHex(), Math.min(len * 0.22, maxR * 0.12), Math.min(len * 0.1, maxR * 0.05));
          world.add(arr);
          if (o.label) labels.push({ pos: b.clone().add(new THREE.Vector3(0, maxR * 0.08, 0)), text: o.label }); break;
        }
        case 'line': {
          const pts = (o.points || []).map(v3);
          if (pts.length >= 2) {
            const g = new THREE.BufferGeometry().setFromPoints(pts);
            if (o.dashed) world.add(new THREE.Line(g, new THREE.LineDashedMaterial({ color: col(o.color, 0xffffff), dashSize: maxR * 0.05, gapSize: maxR * 0.035 })));
            else world.add(new THREE.Line(g, new THREE.LineBasicMaterial({ color: col(o.color, 0xffffff) })));
          } break;
        }
        case 'plane': {
          const size = o.size || 8;
          const m = new THREE.Mesh(new THREE.PlaneGeometry(size, size),
            new THREE.MeshStandardMaterial({ color: col(o.color, 0x1e2438), side: THREE.DoubleSide, transparent: true, opacity: opacity == null ? 0.6 : opacity, roughness: 0.9 }));
          m.position.copy(v3(o.pos || [0, 0, 0]));
          const n = v3(o.normal || [0, 1, 0]).normalize();
          m.quaternion.setFromUnitVectors(new THREE.Vector3(0, 0, 1), n);
          world.add(m); break;
        }
        case 'label': {
          labels.push({ pos: v3(o.pos), text: String(o.text || '') }); break;
        }
      }
    });

    scene.__autoRotate = /rotate/i.test(scene.camera_hint || '');
    const orbit = new SimpleOrbit(camera, renderer.domElement);
    if (orbit.target) orbit.target.set(0, maxR * 0.2, 0);

    // label DOM layer
    const labelLayer = document.createElement('div');
    labelLayer.style.cssText = 'position:absolute;inset:0;pointer-events:none;overflow:hidden';
    container.appendChild(labelLayer);
    labels.forEach((l) => {
      l.el = document.createElement('div');
      l.el.className = 'lbl3d';
      l.el.textContent = l.text;
      if (l.color) l.el.style.color = l.color;
      labelLayer.appendChild(l.el);
    });
    const hint = document.createElement('div');
    hint.className = 'hint';
    hint.textContent = '🖱 drag to rotate · scroll to zoom';
    container.appendChild(hint);

    // fit camera distance
    const dist = camera.position.length();
    if (dist < maxR * 1.2) camera.position.multiplyScalar(maxR * 2.1 / dist);
    orbit.sph.radius = camera.position.distanceTo(orbit.target || new THREE.Vector3());

    const proj = new THREE.Vector3();
    let t0 = performance.now();
    function animate() {
      requestAnimationFrame(animate);
      const t = (performance.now() - t0) / 1000;
      if (scene.__autoRotate) orbit.sph.theta += 0.0018;
      orbit.update();
      renderer.render(world, camera);
      const rect = renderer.domElement.getBoundingClientRect();
      labels.forEach((l) => {
        if (!l.el) return;
        proj.copy(l.pos).project(camera);
        const x = (proj.x * 0.5 + 0.5) * rect.width;
        const y = (-proj.y * 0.5 + 0.5) * rect.height;
        if (proj.z > 1 || x < -60 || y < -30 || x > rect.width + 60 || y > rect.height + 30) {
          l.el.style.display = 'none';
        } else {
          l.el.style.display = 'block';
          l.el.style.left = x + 'px';
          l.el.style.top = y + 'px';
        }
      });
    }
    animate();

    // resize
    const ro = new ResizeObserver(() => {
      const w = container.clientWidth, h = container.clientHeight;
      if (!w || !h) return;
      camera.aspect = w / h; camera.updateProjectionMatrix();
      renderer.setSize(w, h);
    });
    ro.observe(container);

    return { dispose: () => { ro.disconnect(); renderer.dispose(); container.innerHTML = ''; } };
  };
})();

/* Lunar surface imagery: NASA's Scientific Visualization Studio, CGI Moon Kit.
 * https://svs.gsfc.nasa.gov/4720/ — LRO / LROC, visualized by Ernie Wright.
 * A north-up rendering of the near side, with approximate phase lighting.
 */
(function (root) {
  "use strict";
  function createRenderer(source, target, status) {
    const size = 640, radius = size / 2 - 1;
    const canvas = document.createElement("canvas");
    canvas.width = canvas.height = size;
    const context = canvas.getContext("2d");
    const frame = context.createImageData(size, size);
    const surface = new Uint8ClampedArray(size * size * 3);
    const normals = new Float32Array(size * size * 2);
    const texture = new Image();
    let ready = false, phase = 0, lastPhase = null;

    function prepare() {
      const map = document.createElement("canvas");
      map.width = texture.naturalWidth; map.height = texture.naturalHeight;
      const mapContext = map.getContext("2d", {willReadFrequently:true});
      mapContext.drawImage(texture, 0, 0);
      const pixels = mapContext.getImageData(0, 0, map.width, map.height).data;
      // Project the geographic map onto the visible hemisphere once. The source
      // map is centered on 0° longitude; east is right and lunar north is up.
      for (let y = 0; y < size; y++) for (let x = 0; x < size; x++) {
        const nx = (x + .5 - size / 2) / radius;
        const ny = (y + .5 - size / 2) / radius;
        const r2 = nx * nx + ny * ny, i = y * size + x;
        if (r2 >= 1) continue;
        const nz = Math.sqrt(1 - r2);
        normals[i * 2] = nx; normals[i * 2 + 1] = nz;
        const u = (.5 + Math.atan2(nx, nz) / (2 * Math.PI)) * (map.width - 1);
        const v = (.5 + Math.asin(ny) / Math.PI) * (map.height - 1);
        const ux = Math.floor(u), vy = Math.floor(v), dx = u - ux, dy = v - vy;
        for (let c = 0; c < 3; c++) {
          const top = pixels[(vy * map.width + ux) * 4 + c] * (1 - dx)
            + pixels[(vy * map.width + ux + 1) * 4 + c] * dx;
          const bottom = pixels[((vy + 1) * map.width + ux) * 4 + c] * (1 - dx)
            + pixels[((vy + 1) * map.width + ux + 1) * 4 + c] * dx;
          surface[i * 3 + c] = top * (1 - dy) + bottom * dy;
        }
        // One-pixel antialiasing at the limb; no artificial glow or outline.
        frame.data[i * 4 + 3] = 255 * Math.min(1, (1 - Math.sqrt(r2)) * radius);
      }
      ready = true;
      draw(phase);
    }

    function draw(value) {
      phase = ((value % 1) + 1) % 1;
      if (!ready || phase === lastPhase) return;
      lastPhase = phase;
      const angle = phase * 2 * Math.PI;
      const sunX = Math.sin(angle), sunZ = -Math.cos(angle);
      for (let i = 0; i < size * size; i++) {
        if (!frame.data[i * 4 + 3]) continue;
        const x = normals[i * 2], z = normals[i * 2 + 1];
        const sunlight = Math.max(0, x * sunX + z * sunZ);
        // A lunar-style scattering approximation keeps the limb from looking
        // like a matte ball. This does not model terrain shadows or eclipses.
        const scattering = .08 * sunlight + .92 * 2 * sunlight / (sunlight + z);
        const light = .035 + .965 * Math.min(1.12, Math.pow(scattering, .6));
        for (let c = 0; c < 3; c++) frame.data[i * 4 + c] = surface[i * 3 + c] * light;
      }
      context.putImageData(frame, 0, 0);
      target.setAttribute("href", canvas.toDataURL("image/png"));
      status.style.display = "none";
    }

    texture.onload = () => {
      try { prepare(); }
      catch (_) { status.textContent = "Moon image unavailable"; }
    };
    texture.onerror = () => { status.textContent = "Moon image unavailable"; };
    texture.src = source;
    return {draw};
  }
  root.DraiochtMoon = {createRenderer};
})(window);

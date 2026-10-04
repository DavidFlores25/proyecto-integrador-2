document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('.carrusel').forEach((carrusel) => {
    const track = carrusel.querySelector('.track');
    const dotsContainer = carrusel.querySelector('.dots');

    if (!track || !dotsContainer) return;

    const slides = Array.from(track.children);
    const dots = [];
    let index = 0;
    let intervalId;

    slides.forEach((_, j) => {
      const dot = document.createElement('button');
      dot.className = 'dot' + (j === 0 ? ' active' : '');
      dot.type = 'button';
      dot.addEventListener('click', () => ir(j));
      dotsContainer.appendChild(dot);
      dots.push(dot);
    });

    function ir(n) {
      index = (n + slides.length) % slides.length;
      track.style.transform = `translateX(-${index * 100}%)`;
      dots.forEach((dot, j) => dot.classList.toggle('active', j === index));
      resetInterval();
    }

    function resetInterval() {
      clearInterval(intervalId);
      intervalId = window.setInterval(() => ir(index + 1), 4000);
    }

    let x0 = 0;
    track.addEventListener('touchstart', (e) => {
      x0 = e.touches[0].clientX;
    }, { passive: true });

    track.addEventListener('touchend', (e) => {
      const deltaX = e.changedTouches[0].clientX - x0;
      if (Math.abs(deltaX) > 40) {
        ir(index + (deltaX < 0 ? 1 : -1));
      }
    });

    resetInterval();
  });
});


const spans = document.querySelectorAll('.frase-dishoom .reveal');

const observer = new IntersectionObserver((entries) => {
  entries.forEach((entry) => {
    if (entry.isIntersecting) {
      // aparecen en cadena, una tras otra
      spans.forEach((span, i) => {
        setTimeout(() => {
          span.classList.add('visible');
        }, i * 730); // 150ms de diferencia entre cada bloque
      });
      observer.unobserve(entry.target);
    }
  });
}, { threshold: 0.3 });

observer.observe(document.querySelector('.frase-dishoom'));

// ===== MAPA DE UBICACIÓN =====
(function () {
  const LAT = 12.660924267396462, LNG = -87.16636347863243;

  const mapa = L.map('mapa', { scrollWheelZoom: false }).setView([LAT, LNG], 14);

  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '© OpenStreetMap'
  }).addTo(mapa);

  const icono = L.divIcon({
    className: '',
    html: '<div class="pin-pulso"></div>',
    iconSize: [22, 22]
  });

  L.marker([LAT, LNG], { icon: icono }).addTo(mapa)
    .bindPopup(`<b>Don Bigote Parrilla</b><br>El Viejo<br>
      <a target="_blank" href="https://www.google.com/maps/dir/?api=1&destination=${LAT},${LNG}">Cómo llegar</a>`)
    .openPopup();

  // Zoom animado al llegar a la sección
  new IntersectionObserver(([e]) => {
    if (e.isIntersecting) mapa.flyTo([LAT, LNG], 17, { duration: 2.5 });
  }, { threshold: 0.5 }).observe(document.getElementById('mapa'));

  // La rueda del mouse solo hace zoom después de hacer clic en el mapa
  mapa.on('click', () => mapa.scrollWheelZoom.enable());
  mapa.on('mouseout', () => mapa.scrollWheelZoom.disable());
})();

// ===== MENÚ =====
(function () {
  const seccion = document.getElementById('menu');
  if (!seccion) return;

  const tabs = seccion.querySelectorAll('.mn-tab');
  const paneles = seccion.querySelectorAll('.mn-panel');

  // retraso escalonado para que las tarjetas entren una tras otra
  paneles.forEach(p =>
    p.querySelectorAll('.mn-anim').forEach((el, i) => el.style.setProperty('--i', i))
  );

  function mostrar(id) {
    tabs.forEach(t => t.setAttribute('aria-selected', t.dataset.panel === id));
    paneles.forEach(p => {
      const activo = p.id === id;
      p.hidden = !activo;
      if (activo) {
        const items = p.querySelectorAll('.mn-anim');
        items.forEach(el => el.classList.remove('mn-in'));
        void p.offsetWidth; // reinicia la animación
        requestAnimationFrame(() => items.forEach(el => el.classList.add('mn-in')));
      }
    });
  }

  tabs.forEach(t => t.addEventListener('click', () => mostrar(t.dataset.panel)));

  // aparecer al hacer scroll
  const io = new IntersectionObserver((entradas) => {
    entradas.forEach(e => {
      if (e.isIntersecting) {
        e.target.classList.add('mn-in');
        io.unobserve(e.target);
      }
    });
  }, { threshold: 0.15 });

  seccion.querySelectorAll('.mn-anim').forEach(el => io.observe(el));
})();

// ===== APARECER AL HACER SCROLL (resto de la página) =====
(function () {
  const obs = new IntersectionObserver((entradas) => {
    entradas.forEach(e => {
      if (e.isIntersecting) {
        e.target.classList.add('visible');
        obs.unobserve(e.target);
      }
    });
  }, { threshold: 0.1 });

  // cada grupo entra escalonado, uno tras otro
  const grupos = [
    '.vot > *',             // foto + texto de "nuestra historia"
    '.servicios > div',     // los 4 servicios
    '.contactos > .contac', // texto de ubicación
    '.sobre > div',         // sobre nosotros / horarios / fotos
    '.Foo'                  // footer
  ];

  grupos.forEach(sel => {
    document.querySelectorAll(sel).forEach((el, i) => {
      el.classList.add('aparece');
      el.style.setProperty('--i', i);
      obs.observe(el);
    });
  });
})();
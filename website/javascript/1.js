document.addEventListener('DOMContentLoaded', () => {
  const track = document.getElementById('track');
  const dotsContainer = document.getElementById('dots');

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


const spans = document.querySelectorAll('.frase-dishoom .reveal');

const observer = new IntersectionObserver((entries) => {
  entries.forEach((entry) => {
    if (entry.isIntersecting) {
      // aparecen en cadena, una tras otra
      spans.forEach((span, i) => {
        setTimeout(() => {
          span.classList.add('visible');
        }, i * 450); // 150ms de diferencia entre cada bloque
      });
      observer.unobserve(entry.target);
    }
  });
}, { threshold: 0.3 });

observer.observe(document.querySelector('.frase-dishoom'));
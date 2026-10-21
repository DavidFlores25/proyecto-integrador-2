// ===== RESERVAS WEB (se conecta con Flask: /api/mesas y /api/reservas) =====
(function () {
  const form = document.getElementById('rs-form');
  if (!form) return;

  const DIAS_ADELANTE = 60;
  const $ = (id) => document.getElementById(id);

  const campos = {
    nombre: $('rs-nombre'), correo: $('rs-correo'), telefono: $('rs-telefono'),
    personas: $('rs-personas'), fecha: $('rs-fecha'), inicio: $('rs-inicio'), fin: $('rs-fin')
  };
  const btnMesas = $('rs-ver-mesas');
  const btnEnviar = $('rs-enviar');
  const gridMesas = $('rs-mesas');
  const msg = $('rs-msg');

  let mesasElegidas = new Set();

  // ---------- helpers ----------
  function fechaLocal(d) {
    // toISOString usaría UTC y podría mostrar el día anterior/siguiente
    const p = (n) => String(n).padStart(2, '0');
    return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())}`;
  }

  function etiquetaHora(min) {
    const h = Math.floor(min / 60), m = min % 60;
    const h12 = h % 12 || 12;
    return `${h12}:${String(m).padStart(2, '0')} ${h < 12 ? 'AM' : 'PM'}`;
  }

  function valorHora(min) {
    return `${String(Math.floor(min / 60)).padStart(2, '0')}:${String(min % 60).padStart(2, '0')}`;
  }

  function mostrarMensaje(texto, tipo) {
    msg.textContent = texto;
    msg.className = 'rs-msg' + (tipo ? ' rs-msg--' + tipo : '');
  }

  async function pedir(url, opciones) {
    let resp;
    try {
      resp = await fetch(url, opciones);
    } catch (e) {
      throw new Error('No se pudo conectar con el servidor. Intente de nuevo.');
    }
    let datos = {};
    try { datos = await resp.json(); } catch (e) { /* respuesta sin JSON */ }
    if (!resp.ok) throw new Error(datos.error || `Error ${resp.status}: abra la página desde http://127.0.0.1:5000 con "python app.py" en marcha.`);
    return datos;
  }

  // ---------- valores iniciales ----------
  const hoy = new Date();
  const max = new Date(); max.setDate(max.getDate() + DIAS_ADELANTE);
  campos.fecha.min = fechaLocal(hoy);
  campos.fecha.max = fechaLocal(max);
  const inicial = new Date();
  if (inicial.getDay() === 1) inicial.setDate(inicial.getDate() + 1); // lunes cerrado
  campos.fecha.value = fechaLocal(inicial);

  for (let min = 8 * 60; min <= 23 * 60; min += 15) {
    [campos.inicio, campos.fin].forEach((sel) => {
      const op = document.createElement('option');
      op.value = valorHora(min);
      op.textContent = etiquetaHora(min);
      sel.appendChild(op);
    });
  }
  campos.inicio.value = '12:00';
  campos.fin.value = '14:00';

  // ---------- mesas ----------
  function limpiarMesas() {
    mesasElegidas = new Set();
    gridMesas.replaceChildren();
    btnEnviar.disabled = true;
  }

  // si cambia fecha u horario, la disponibilidad mostrada ya no sirve
  [campos.fecha, campos.inicio, campos.fin].forEach((c) => c.addEventListener('change', limpiarMesas));

  function validarAntesDeVerMesas() {
    if (!campos.fecha.value) return 'Elija una fecha.';
    const [a, m, d] = campos.fecha.value.split('-').map(Number);
    if (new Date(a, m - 1, d).getDay() === 1) return 'El restaurante está cerrado los lunes. Elija otra fecha.';
    if (campos.inicio.value >= campos.fin.value) return 'La hora de fin debe ser mayor que la de inicio.';
    return '';
  }

  btnMesas.addEventListener('click', async () => {
    const problema = validarAntesDeVerMesas();
    if (problema) { mostrarMensaje(problema, 'error'); return; }

    mostrarMensaje('Buscando mesas disponibles...', '');
    limpiarMesas();
    btnMesas.disabled = true;
    try {
      const q = new URLSearchParams({
        fecha: campos.fecha.value, inicio: campos.inicio.value, fin: campos.fin.value
      });
      const { mesas } = await pedir('/api/mesas?' + q);

      mesas.forEach((m) => {
        const b = document.createElement('button');
        b.type = 'button';
        b.className = 'rs-mesa' + (m.libre ? '' : ' rs-mesa--ocupada');
        b.disabled = !m.libre;
        b.setAttribute('aria-pressed', 'false');
        b.innerHTML = '<strong></strong><small></small>';
        b.querySelector('strong').textContent = 'Mesa ' + m.numero;
        b.querySelector('small').textContent = m.libre ? 'Libre' : 'Ocupada';
        b.addEventListener('click', () => {
          const activa = !mesasElegidas.has(m.numero);
          activa ? mesasElegidas.add(m.numero) : mesasElegidas.delete(m.numero);
          b.classList.toggle('rs-mesa--elegida', activa);
          b.setAttribute('aria-pressed', String(activa));
          btnEnviar.disabled = mesasElegidas.size === 0;
        });
        gridMesas.appendChild(b);
      });

      if (mesas.some((m) => m.libre)) {
        mostrarMensaje('Toque las mesas que desea reservar.', '');
      } else {
        mostrarMensaje('No hay mesas disponibles en ese horario. Pruebe otro.', 'error');
      }
    } catch (e) {
      mostrarMensaje(e.message, 'error');
    } finally {
      btnMesas.disabled = false;
    }
  });

  // ---------- enviar reserva ----------
  form.addEventListener('submit', async (ev) => {
    ev.preventDefault();
    if (mesasElegidas.size === 0) { mostrarMensaje('Debe seleccionar al menos una mesa.', 'error'); return; }

    btnEnviar.disabled = true;
    mostrarMensaje('Enviando solicitud...', '');
    try {
      const r = await pedir('/api/reservas', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          nombre: campos.nombre.value, correo: campos.correo.value, telefono: campos.telefono.value,
          personas: campos.personas.value, fecha: campos.fecha.value,
          inicio: campos.inicio.value, fin: campos.fin.value,
          mesas: Array.from(mesasElegidas)
        })
      });
      mostrarMensaje(r.mensaje, 'ok');
      limpiarMesas();
      form.reset();
      campos.fecha.value = fechaLocal(inicial);
      campos.inicio.value = '12:00';
      campos.fin.value = '14:00';
    } catch (e) {
      mostrarMensaje(e.message, 'error');
      btnEnviar.disabled = mesasElegidas.size === 0;
    }
  });
})();
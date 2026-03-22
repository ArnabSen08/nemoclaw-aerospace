// Tab switching
function showTab(id) {
  document.querySelectorAll('.demo-panel').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
  document.getElementById(id).classList.add('active');
  event.target.classList.add('active');
}

// Fetch live stats for hero counters
async function loadLiveStats() {
  // Upcoming launches count
  try {
    const r = await fetch('https://api.spacexdata.com/v4/launches/upcoming');
    const data = await r.json();
    document.getElementById('launches-count').textContent = data.length;
  } catch { document.getElementById('launches-count').textContent = '5+'; }

  // People in space
  try {
    const r = await fetch('https://api.open-notify.org/astros.json');
    const data = await r.json();
    document.getElementById('crew-count').textContent = data.number;
  } catch { document.getElementById('crew-count').textContent = '7'; }

  // Active natural events
  try {
    const r = await fetch('https://eonet.gsfc.nasa.gov/api/v3/events?status=open&limit=100');
    const data = await r.json();
    document.getElementById('events-count').textContent = data.events.length;
  } catch { document.getElementById('events-count').textContent = '40+'; }
}

// Animate stat numbers counting up
function animateCount(el, target) {
  let current = 0;
  const step = Math.ceil(target / 30);
  const timer = setInterval(() => {
    current = Math.min(current + step, target);
    el.textContent = current;
    if (current >= target) clearInterval(timer);
  }, 40);
}

document.addEventListener('DOMContentLoaded', () => {
  loadLiveStats();

  // Animate the static "4" agents counter
  const staticStat = document.querySelector('.hero-stats .stat:last-child .stat-num');
  if (staticStat) animateCount(staticStat, 4);
});

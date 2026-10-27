const fs = require('fs');
const path = require('path');

let index = null;

function loadIndex() {
  if (index) return index;
  const p = path.join(process.cwd(), 'search_index.json');
  index = JSON.parse(fs.readFileSync(p, 'utf8'));
  return index;
}

module.exports = (req, res) => {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Content-Type', 'application/json');

  const q = (req.query.q || '').trim().toLowerCase();
  const limit = Math.min(parseInt(req.query.limit || '50'), 100);

  if (q.length < 2) {
    return res.status(200).json([]);
  }

  try {
    const data = loadIndex();
    const results = [];
    for (const person of data) {
      const full = `${person.fn} ${person.ln}`.toLowerCase();
      if (full.includes(q)) {
        results.push(person);
        if (results.length >= limit) break;
      }
    }
    results.sort((a, b) => (b.s || 0) - (a.s || 0));
    res.status(200).json(results);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
};

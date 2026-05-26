/**
 * commands.js
 * Parser dan handler semua perintah bot NTE
 *
 * Daftar perintah:
 *   /bantuan              → daftar semua perintah
 *   /laporan              → semua laporan hari ini (ZIP/JPG semua operator-area)
 *   /laporan [op] [area]  → laporan 1 operator-area hari ini
 *   /laporan [op] [area] [tgl] → laporan tanggal tertentu
 *   /stok                 → ringkasan teks semua stok hari ini
 *   /stok [op]            → ringkasan teks per operator
 *   /tanggal              → daftar tanggal yang ada datanya
 *   /status               → cek koneksi API
 */

const axios = require('axios');
const fs    = require('fs');
const path  = require('path');
const os    = require('os');

const API = process.env.API_BASE_URL || 'http://localhost:8502';

// ── Normalisasi input pengguna ─────────────────────────────────────────────
const OP_ALIAS = {
  'telkomsel': 'TELKOMSEL', 'tsel': 'TELKOMSEL', 'ts': 'TELKOMSEL',
  'telkom':    'TELKOM',    'tlk':  'TELKOM',
  'tif':       'TIF',
};
const AREA_ALIAS = {
  'bandung':  'BANDUNG',  'bdg': 'BANDUNG',
  'soreang':  'SOREANG',  'srg': 'SOREANG',
};

function normalizeOp(s)   { return OP_ALIAS[s?.toLowerCase()]   || s?.toUpperCase(); }
function normalizeArea(s) { return AREA_ALIAS[s?.toLowerCase()] || s?.toUpperCase(); }

// ── Download file ke tmp, return path ──────────────────────────────────────
async function downloadFile(url, filename) {
  const tmpPath = path.join(os.tmpdir(), filename);
  const res     = await axios.get(url, { responseType: 'arraybuffer', timeout: 30000 });
  fs.writeFileSync(tmpPath, Buffer.from(res.data));
  return tmpPath;
}

// ── Format pesan error ─────────────────────────────────────────────────────
function errMsg(e) {
  const code = e?.response?.status;
  const msg  = e?.response?.data?.detail || e?.message || 'Unknown error';
  if (code === 404) return `❌ Data tidak ditemukan: ${msg}`;
  if (code === 422) return `❌ Format perintah salah. Ketik */bantuan* untuk panduan.`;
  return `❌ Error: ${msg}`;
}

// ══════════════════════════════════════════════════════════════════════════════
// HANDLER FUNCTIONS
// ══════════════════════════════════════════════════════════════════════════════

async function handleBantuan() {
  return {
    type:    'text',
    content: `🤖 *NTE Stock Bot — Daftar Perintah*

📋 *Laporan PDF/JPG:*
• \`/laporan\` — semua laporan hari ini (semua operator & area)
• \`/laporan telkomsel bandung\` — 1 laporan
• \`/laporan telkom soreang 2025-05-19\` — tanggal tertentu
• \`/laporan tif bandung jpg\` — format JPG
• \`/laporan semua pdf\` — ZIP berisi semua PDF

📊 *Ringkasan Teks:*
• \`/stok\` — ringkasan stok hari ini semua operator
• \`/stok telkomsel\` — ringkasan per operator
• \`/stok telkom bandung\` — ringkasan per area

📅 *Informasi:*
• \`/tanggal\` — daftar tanggal yang ada datanya
• \`/status\` — cek koneksi server

💡 *Alias yang bisa dipakai:*
• Operator: \`tsel\`, \`telkomsel\`, \`telkom\`, \`tif\`
• Area: \`bdg\` = Bandung, \`srg\` = Soreang
• Format: \`pdf\` atau \`jpg\`

_Bot NTE v1.0 · Telkom Indonesia_`,
  };
}

async function handleStatus() {
  try {
    const res = await axios.get(`${API}/health`, { timeout: 5000 });
    const d   = res.data;
    return {
      type: 'text',
      content: `✅ *Server NTE Dashboard*\n\n`
             + `📡 Status   : Online\n`
             + `📅 Data terbaru: ${d.tanggal_terbaru || '-'}\n`
             + `🗓️  Total tanggal: ${d.total_tanggal} hari\n`
             + `🕐 Timestamp: ${new Date(d.timestamp).toLocaleString('id-ID')}`,
    };
  } catch (e) {
    return { type: 'text', content: `❌ Server tidak dapat dihubungi.\n${e.message}` };
  }
}

async function handleTanggal() {
  try {
    const res   = await axios.get(`${API}/tanggal/tersedia`, { timeout: 8000 });
    const dates = res.data.tanggal || [];
    if (!dates.length) return { type: 'text', content: '📭 Belum ada data tersimpan.' };
    const list  = dates.slice(0, 14).map((d, i) => `${i+1}. ${d}`).join('\n');
    return {
      type: 'text',
      content: `📅 *Tanggal yang ada data stok:*\n\n${list}`
             + (dates.length > 14 ? `\n_...dan ${dates.length-14} lainnya_` : ''),
    };
  } catch (e) { return { type: 'text', content: errMsg(e) }; }
}

async function handleStok(args) {
  // /stok [op] [area]
  const op   = args[0] ? normalizeOp(args[0])   : undefined;
  const area = args[1] ? normalizeArea(args[1]) : undefined;

  const params = new URLSearchParams();
  if (op)   params.append('operator', op);
  if (area) params.append('area', area);

  try {
    const res = await axios.get(`${API}/stok/ringkas?${params}`, { timeout: 10000 });
    return { type: 'text', content: res.data.pesan };
  } catch (e) { return { type: 'text', content: errMsg(e) }; }
}

async function handleLaporanSatu(op, area, tanggal, fmt) {
  /**
   * Unduh 1 laporan PDF atau JPG untuk 1 operator-area.
   * Return object { type: 'media', path, caption, mimetype, filename }
   */
  const endpoint  = fmt === 'jpg' ? '/laporan/jpg' : '/laporan';
  const params    = `operator=${op}&area=${area}${tanggal ? `&tanggal=${tanggal}` : ''}`;
  const url       = `${API}${endpoint}?${params}`;
  const tgl       = tanggal || 'hari-ini';
  const ext       = fmt === 'jpg' ? 'jpg' : 'pdf';
  const filename  = `STOCK_NTE_${op}_${area}_${tgl}.${ext}`;

  try {
    const tmpPath = await downloadFile(url, filename);
    return {
      type:     'media',
      path:     tmpPath,
      filename,
      mimetype: fmt === 'jpg' ? 'image/jpeg' : 'application/pdf',
      caption:  `📊 *STOCK NTE ${op} ${area}*\n📅 ${tgl}`,
    };
  } catch (e) { return { type: 'text', content: errMsg(e) }; }
}

async function handleLaporanSemua(tanggal, opFilter, fmt) {
  /**
   * Unduh ZIP berisi semua PDF, atau kirim JPG satu per satu.
   */
  if (fmt === 'jpg') {
    // Kirim JPG satu per satu untuk setiap kombinasi
    const results = [];
    const AREA_CONFIG_KEYS = [
      ['TELKOMSEL','BANDUNG'], ['TELKOMSEL','SOREANG'],
      ['TELKOM','BANDUNG'],    ['TELKOM','SOREANG'],
      ['TIF','BANDUNG'],       ['TIF','SOREANG'],
    ];
    for (const [op, area] of AREA_CONFIG_KEYS) {
      if (opFilter && op !== opFilter) continue;
      const r = await handleLaporanSatu(op, area, tanggal, 'jpg');
      results.push(r);
    }
    return { type: 'multi', items: results };
  }

  // Default: ZIP semua PDF
  const params = new URLSearchParams();
  if (tanggal)  params.append('tanggal', tanggal);
  if (opFilter) params.append('operator', opFilter);
  const url      = `${API}/laporan/semua?${params}`;
  const tgl      = tanggal || 'hari-ini';
  const filename = `STOCK_NTE_SEMUA_${tgl}.zip`;

  try {
    const tmpPath = await downloadFile(url, filename);
    return {
      type:     'media',
      path:     tmpPath,
      filename,
      mimetype: 'application/zip',
      caption:  `📦 *STOCK NTE — Semua Laporan*\n📅 ${tgl}\n_ZIP berisi semua PDF_`,
    };
  } catch (e) { return { type: 'text', content: errMsg(e) }; }
}

// ══════════════════════════════════════════════════════════════════════════════
// MAIN PARSER
// ══════════════════════════════════════════════════════════════════════════════

async function processCommand(rawText) {
  const text  = rawText.trim();
  const lower = text.toLowerCase();

  // Tidak dimulai /
  if (!lower.startsWith('/')) return null;

  const [cmd, ...args] = text.slice(1).split(/\s+/);

  switch (cmd.toLowerCase()) {

    case 'bantuan':
    case 'help':
    case 'menu':
      return handleBantuan();

    case 'status':
    case 'ping':
      return handleStatus();

    case 'tanggal':
    case 'dates':
      return handleTanggal();

    case 'stok':
    case 'stock':
    case 'ringkasan':
      return handleStok(args);

    case 'laporan':
    case 'report':
    case 'lap': {
      // Parse: /laporan [op] [area] [tanggal] [format]
      // Contoh variasi:
      //   /laporan
      //   /laporan semua
      //   /laporan semua pdf
      //   /laporan semua jpg
      //   /laporan telkomsel
      //   /laporan telkomsel bandung
      //   /laporan telkomsel bandung jpg
      //   /laporan telkomsel bandung 2025-05-19
      //   /laporan telkomsel bandung 2025-05-19 jpg

      const cleaned = args.map(a => a.toLowerCase());

      // Deteksi format di args mana saja
      const fmtIdx  = cleaned.findIndex(a => a === 'jpg' || a === 'pdf' || a === 'zip');
      const fmt     = fmtIdx >= 0 ? cleaned[fmtIdx] : 'pdf';
      const rest    = args.filter((_, i) => i !== fmtIdx);

      // Deteksi tanggal (pola YYYY-MM-DD)
      const dateIdx = rest.findIndex(a => /^\d{4}-\d{2}-\d{2}$/.test(a));
      const tanggal = dateIdx >= 0 ? rest[dateIdx] : null;
      const parts   = rest.filter((_, i) => i !== dateIdx);

      // Cek "semua" / "all"
      if (!parts.length || parts[0].toLowerCase() === 'semua' || parts[0].toLowerCase() === 'all') {
        const opFilter = parts[1] ? normalizeOp(parts[1]) : null;
        return handleLaporanSemua(tanggal, opFilter, fmt === 'zip' ? 'pdf' : fmt);
      }

      const op   = normalizeOp(parts[0]);
      const area = parts[1] ? normalizeArea(parts[1]) : null;

      // Hanya operator tanpa area → kirim semua area operator itu
      if (!area) {
        return handleLaporanSemua(tanggal, op, fmt === 'zip' ? 'pdf' : fmt);
      }

      // Spesifik 1 laporan
      return handleLaporanSatu(op, area, tanggal, fmt === 'zip' ? 'pdf' : fmt);
    }

    default:
      return {
        type:    'text',
        content: `❓ Perintah */${cmd}* tidak dikenal.\nKetik */bantuan* untuk daftar perintah.`,
      };
  }
}

module.exports = { processCommand };

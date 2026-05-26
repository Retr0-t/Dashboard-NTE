/**
 * bot.js — NTE WhatsApp Bot
 * Menggunakan whatsapp-web.js (scan QR sekali, lalu auto-reconnect)
 *
 * Cara pakai:
 *   1. npm install
 *   2. cp .env.example .env  → isi konfigurasi
 *   3. node bot.js
 *   4. Scan QR code yang muncul di terminal
 *   5. Bot siap menerima perintah!
 */

require('dotenv').config();

const { Client, LocalAuth, MessageMedia } = require('whatsapp-web.js');
const qrcode  = require('qrcode-terminal');
const cron    = require('node-cron');
const axios   = require('axios');
const fs      = require('fs');
const path    = require('path');

const { processCommand } = require('./commands');

// ── Konfigurasi ───────────────────────────────────────────────────────────────
const API             = process.env.API_BASE_URL    || 'http://localhost:8502';
const ALLOWED_NUMBERS = (process.env.ALLOWED_NUMBERS || '')
  .split(',').map(n => n.trim()).filter(Boolean);
const REPORT_TARGET   = process.env.REPORT_TARGET   || '';
const CRON_SCHEDULE   = process.env.CRON_SCHEDULE   || '0 7 * * *';
const AUTO_FORMAT     = (process.env.AUTO_REPORT_FORMAT || 'jpg').toLowerCase();

// ── WhatsApp Client ───────────────────────────────────────────────────────────
const client = new Client({
  authStrategy: new LocalAuth({ clientId: 'nte-bot' }),
  puppeteer: {
    args: [
      '--no-sandbox',
      '--disable-setuid-sandbox',
      '--disable-dev-shm-usage',
      '--disable-gpu',
    ],
  },
});

// ── QR Code ───────────────────────────────────────────────────────────────────
client.on('qr', (qr) => {
  console.log('\n📱 Scan QR code berikut dengan WhatsApp:\n');
  qrcode.generate(qr, { small: true });
  console.log('\n⏳ Menunggu scan...\n');
});

// ── Ready ─────────────────────────────────────────────────────────────────────
client.on('ready', () => {
  const info = client.info;
  console.log('✅ Bot WhatsApp NTE siap!');
  console.log(`📱 Terhubung sebagai: ${info.pushname} (${info.wid.user})`);
  console.log(`🔑 Nomor yang diizinkan: ${ALLOWED_NUMBERS.join(', ') || 'SEMUA'}`);
  console.log(`📋 Target laporan: ${REPORT_TARGET || 'belum diset'}`);
  console.log(`⏰ Jadwal otomatis: ${CRON_SCHEDULE}\n`);
});

// ── Auth failure ───────────────────────────────────────────────────────────────
client.on('auth_failure', (msg) => {
  console.error('❌ Autentikasi gagal:', msg);
  console.log('💡 Hapus folder .wwebjs_auth dan jalankan ulang untuk scan QR baru.');
});

// ── Disconnected ──────────────────────────────────────────────────────────────
client.on('disconnected', (reason) => {
  console.log('⚠️  Bot terputus:', reason);
  console.log('🔄 Mencoba reconnect...');
  setTimeout(() => client.initialize(), 5000);
});

// ── Helper: kirim balasan ─────────────────────────────────────────────────────
async function sendResult(chatId, result) {
  if (!result) return;

  if (result.type === 'text') {
    await client.sendMessage(chatId, result.content);

  } else if (result.type === 'media') {
    if (!fs.existsSync(result.path)) {
      await client.sendMessage(chatId, '❌ File tidak dapat dibuat.');
      return;
    }
    const media = MessageMedia.fromFilePath(result.path);
    await client.sendMessage(chatId, media, {
      caption:  result.caption  || '',
      sendMediaAsDocument: result.mimetype === 'application/pdf' ||
                           result.mimetype === 'application/zip',
    });
    // Hapus file temp setelah dikirim
    try { fs.unlinkSync(result.path); } catch (_) {}

  } else if (result.type === 'multi') {
    // Kirim satu per satu
    let sent = 0;
    for (const item of result.items) {
      try {
        await sendResult(chatId, item);
        sent++;
        // Jeda kecil agar tidak di-rate-limit
        await new Promise(r => setTimeout(r, 1500));
      } catch (e) {
        console.error('Error kirim item:', e.message);
      }
    }
    await client.sendMessage(chatId,
      `✅ Selesai mengirim *${sent}* laporan dari *${result.items.length}*.`
    );
  }
}

// ── Message handler ───────────────────────────────────────────────────────────
client.on('message', async (msg) => {
  const chat   = await msg.getChat();
  const sender = msg.from; // format: 628xxx@c.us
  const body   = (msg.body || '').trim();

  // Abaikan pesan dari diri sendiri
  if (msg.fromMe) return;

  // Cek izin: hanya nomor terdaftar yang bisa pakai bot
  if (ALLOWED_NUMBERS.length > 0) {
    const senderNum = sender.replace('@c.us', '').replace('@g.us', '');
    const allowed   = ALLOWED_NUMBERS.some(n =>
      senderNum.includes(n) || n.includes(senderNum)
    );
    if (!allowed) {
      console.log(`⛔ Pesan dari nomor tidak diizinkan: ${sender}`);
      return;
    }
  }

  // Abaikan bukan perintah
  if (!body.startsWith('/')) return;

  console.log(`📩 [${new Date().toLocaleString('id-ID')}] ${sender}: ${body}`);

  // Kirim "sedang memproses..."
  await chat.sendStateTyping();

  try {
    const result = await processCommand(body);
    await sendResult(sender, result);
    console.log(`✅ Perintah "${body}" berhasil diproses`);
  } catch (e) {
    console.error('❌ Error memproses perintah:', e);
    await client.sendMessage(sender,
      `❌ Terjadi kesalahan saat memproses perintah.\nError: ${e.message}`
    );
  }
});

// ── Scheduled auto-report ─────────────────────────────────────────────────────
if (REPORT_TARGET && CRON_SCHEDULE) {
  cron.schedule(CRON_SCHEDULE, async () => {
    console.log(`\n⏰ [${new Date().toLocaleString('id-ID')}] Menjalankan laporan otomatis...`);

    if (!client.info) {
      console.log('⚠️  Bot belum siap, skip laporan otomatis.');
      return;
    }

    try {
      // 1. Kirim pesan pembuka
      await client.sendMessage(REPORT_TARGET,
        `🌅 *Laporan Stok Harian NTE*\n`
      + `📅 ${new Date().toLocaleDateString('id-ID', {
          weekday:'long', year:'numeric', month:'long', day:'numeric'
        })}\n\n`
      + `⏳ Sedang menyiapkan laporan...`
      );

      // 2. Ambil ringkasan teks
      const res = await axios.get(`${API}/stok/ringkas`, { timeout: 15000 });
      await client.sendMessage(REPORT_TARGET, res.data.pesan);

      // 3. Kirim laporan visual (JPG atau PDF)
      const cmd = AUTO_FORMAT === 'jpg'
        ? `/laporan semua jpg`
        : `/laporan semua pdf`;

      const result = await processCommand(cmd);
      await sendResult(REPORT_TARGET, result);

      console.log('✅ Laporan otomatis berhasil dikirim.');
    } catch (e) {
      console.error('❌ Error laporan otomatis:', e.message);
      try {
        await client.sendMessage(REPORT_TARGET,
          `❌ Gagal mengirim laporan otomatis.\nError: ${e.message}`
        );
      } catch (_) {}
    }
  }, { timezone: process.env.TZ || 'Asia/Jakarta' });

  console.log(`⏰ Laporan otomatis terjadwal: ${CRON_SCHEDULE}`);
}

// ── Start bot ─────────────────────────────────────────────────────────────────
console.log('🚀 Memulai NTE WhatsApp Bot...');
console.log(`🔌 API URL: ${API}`);
client.initialize();

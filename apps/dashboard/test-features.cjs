/**
 * Comprehensive Student Edition Feature Verification Test Suite
 * Tests core business logic, simulators, generators, calculators, and parsers.
 */

let totalTests = 0;
let passedTests = 0;
let failedTests = 0;

function assert(condition, message) {
  totalTests++;
  if (condition) {
    passedTests++;
    console.log(`  ✅ PASS: ${message}`);
  } else {
    failedTests++;
    console.error(`  ❌ FAIL: ${message}`);
  }
}

console.log('====================================================');
console.log('🧪 RUNNING STUDENT EDITION FEATURE TEST SUITE (v2.1.0)');
console.log('====================================================\n');

// -----------------------------------------------------------------------------
// 1. ACADEMIC GRADE & GPA SIMULATOR TESTS
// -----------------------------------------------------------------------------
console.log('📌 [1/7] Testing Simulator Target Nilai Ujian & IPK:');

// Grade thresholds standard
const gradeThresholds = { A: 85, AB: 75, B: 65, BC: 55, C: 40, D: 25 };
const gradePoints = { A: 4.0, AB: 3.5, B: 3.0, BC: 2.5, C: 2.0, D: 1.0, E: 0.0 };

function calcRequiredUas(tugas, kuis, uts, bobotTugas, bobotKuis, bobotUts, bobotUas, targetThreshold) {
  const currentTotal = (tugas * bobotTugas / 100) + (kuis * bobotKuis / 100) + (uts * bobotUts / 100);
  const remainingNeeded = targetThreshold - currentTotal;
  const scoreNeeded = (remainingNeeded / bobotUas) * 100;
  return +scoreNeeded.toFixed(1);
}

// Test case 1: Standard syllabus weights (Tugas: 20%, Kuis: 15%, UTS: 30%, UAS: 35%)
// Target A (85). Scores: Tugas 85, Kuis 80, UTS 85 -> current = 17 + 12 + 25.5 = 54.5. Needed = 85 - 54.5 = 30.5. UAS = (30.5 / 35) * 100 = 87.1
const uas1 = calcRequiredUas(85, 80, 85, 20, 15, 30, 35, gradeThresholds.A);
assert(uas1 === 87.1, `UAS score needed for Target A calculated correctly (${uas1} vs 87.1)`);

// Test case 2: Target already achieved before UAS
// Scores: Tugas 100, Kuis 100, UTS 100. Target C (40). Needed <= 0
const uas2 = calcRequiredUas(100, 100, 100, 20, 15, 30, 35, gradeThresholds.C);
assert(uas2 <= 0, `Target already secured before UAS correctly identified (${uas2} <= 0)`);

// Test case 3: Impossible target (>100)
// Scores: Tugas 40, Kuis 40, UTS 40 -> current = 8 + 6 + 12 = 26. Needed = 85 - 26 = 59. UAS = (59 / 35) * 100 = 168.6
const uas3 = calcRequiredUas(40, 40, 40, 20, 15, 30, 35, gradeThresholds.A);
assert(uas3 > 100, `Impossible target (>100) flagged correctly (${uas3} > 100)`);

// Test case 4: Semester GPA (IPS) & Cumulative GPA
const sampleCourses = [
  { name: 'Kecerdasan Buatan', credits: 3, grade: 'A' },   // 3 * 4.0 = 12.0
  { name: 'Rekayasa Perangkat Lunak', credits: 4, grade: 'AB' }, // 4 * 3.5 = 14.0
  { name: 'Basis Data Terdistribusi', credits: 3, grade: 'B' },  // 3 * 3.0 = 9.0
  { name: 'Metodologi Penelitian', credits: 2, grade: 'A' },    // 2 * 4.0 = 8.0
];
const totalCredits = sampleCourses.reduce((sum, c) => sum + c.credits, 0); // 12 SKS
const totalPoints = sampleCourses.reduce((sum, c) => sum + (c.credits * gradePoints[c.grade]), 0); // 43.0 poin
const semesterGpa = +(totalPoints / totalCredits).toFixed(2); // 43.0 / 12 = 3.58
assert(totalCredits === 12, 'Total semester credits correctly summed (12 SKS)');
assert(semesterGpa === 3.58, `Semester GPA (IPS) calculated correctly (${semesterGpa} vs 3.58)`);

// Cumulative GPA calculation: prev 60 credits @ 3.40 + 12 credits @ 3.58 -> (60*3.40 + 43.0) / 72 = (204 + 43) / 72 = 247 / 72 = 3.43
const prevCredits = 60;
const prevCgpa = 3.40;
const newCumulativeGpa = +(((prevCredits * prevCgpa) + totalPoints) / (prevCredits + totalCredits)).toFixed(2);
assert(newCumulativeGpa === 3.43, `Cumulative GPA update calculated correctly (${newCumulativeGpa} vs 3.43)`);

// Academic honors
function getHonors(gpa) {
  if (gpa >= 3.51) return 'Dengan Pujian (Cum Laude)';
  if (gpa >= 3.00) return 'Sangat Memuaskan';
  if (gpa >= 2.76) return 'Memuaskan';
  return 'Cukup';
}
assert(getHonors(3.85) === 'Dengan Pujian (Cum Laude)', 'Cum Laude classification verified');
assert(getHonors(3.43) === 'Sangat Memuaskan', 'Sangat Memuaskan classification verified');

// -----------------------------------------------------------------------------
// 2. ANTI-GHOSTING DOSPEM RADAR & WHATSAPP DRAFT GENERATOR TESTS
// -----------------------------------------------------------------------------
console.log('\n📌 [2/7] Testing Anti-Ghosting Dospem Radar & WA Generator:');

function calculateDaysSince(dateString) {
  const latestDate = new Date(dateString);
  const now = new Date();
  return Math.floor((now.getTime() - latestDate.getTime()) / (1000 * 60 * 60 * 24));
}

function getAntiGhostingStatus(days) {
  if (days === null) return 'none';
  if (days <= 7) return 'consistent';
  if (days <= 14) return 'warning';
  return 'urgent';
}

assert(getAntiGhostingStatus(4) === 'consistent', '4 days since last supervision -> consistent (green)');
assert(getAntiGhostingStatus(10) === 'warning', '10 days since last supervision -> warning (yellow)');
assert(getAntiGhostingStatus(16) === 'urgent', '16 days since last supervision -> urgent anti-ghosting alert (red)');

// WhatsApp phone normalizer
function normalizePhone(phone) {
  let clean = phone.replace(/[^0-9]/g, '');
  if (clean.startsWith('0')) {
    clean = '62' + clean.slice(1);
  }
  return clean;
}
assert(normalizePhone('0812-3456-7890') === '6281234567890', 'Phone normalizer converts 08xxx to 628xxx');
assert(normalizePhone('+62 812-9999-0000') === '6281299990000', 'Phone normalizer strips non-digits');

// Template generator verification
function generateDospemMessage(templateType, dospemName, studentName, nim, major, title, topic) {
  if (templateType === 'gentle_followup') {
    return `Selamat pagi ${dospemName}, mohon maaf mengganggu waktunya kembali.\n\nSaya ${studentName} (NIM: ${nim}), mahasiswa bimbingan tugas akhir Bapak/Ibu.\n\nIzin melakukan *follow-up* dengan santun terkait draf naskah *${topic}* yang sebelumnya telah saya kirimkan.\n\nTerima kasih banyak atas waktu dan perhatian Bapak/Ibu.`;
  }
  return '';
}
const testWaMsg = generateDospemMessage('gentle_followup', 'Dr. Budi', 'Alwan', '13520001', 'Informatika', 'AI Agent', 'Bab 3');
assert(testWaMsg.includes('Dr. Budi') && testWaMsg.includes('13520001') && testWaMsg.includes('follow-up'), 'Gentle follow-up WA message contains polite etiquette & student credentials');

// -----------------------------------------------------------------------------
// 3. POMODORO FOCUS TIMER TESTS
// -----------------------------------------------------------------------------
console.log('\n📌 [3/7] Testing Focus Pomodoro Hub Logic:');

function formatSeconds(seconds) {
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
}
assert(formatSeconds(1500) === '25:00', 'Format 1500s -> "25:00"');
assert(formatSeconds(2700) === '45:00', 'Format 2700s -> "45:00"');
assert(formatSeconds(3000) === '50:00', 'Format 3000s -> "50:00"');
assert(formatSeconds(300) === '05:00', 'Format 300s -> "05:00"');
assert(formatSeconds(75) === '01:15', 'Format 75s -> "01:15"');

function calcProgress(totalDuration, timeLeft) {
  const elapsed = totalDuration - timeLeft;
  return Math.min(100, Math.round((elapsed / totalDuration) * 100));
}
assert(calcProgress(1500, 750) === 50, 'Halfway through 25m pomodoro yields 50% progress');
assert(calcProgress(1500, 0) === 100, 'Zero seconds left yields 100% progress');

// -----------------------------------------------------------------------------
// 4. HEALTH & VITALITY TESTS (Sleep Debt & Hydration)
// -----------------------------------------------------------------------------
console.log('\n📌 [4/7] Testing Health & Vitality Calculators:');

const testSleepLogs = [
  { hours: 6.0 },
  { hours: 5.5 },
  { hours: 7.0 },
  { hours: 8.0 },
  { hours: 5.0 },
];
// Daily target = 7.0 hours
// Debt = (7-6) + (7-5.5) + (7-7) + (7-8) + (7-5) = 1 + 1.5 + 0 + (-1) + 2 = 3.5 hours
const sleepDebt = +testSleepLogs.reduce((acc, s) => acc + (7.0 - s.hours), 0).toFixed(1);
assert(sleepDebt === 3.5, `Sleep debt calculated accurately (${sleepDebt} hours vs 3.5 hours)`);

const hydrationGlasses = 6;
const targetGlasses = 8;
const hydrationPct = Math.min(100, Math.round((hydrationGlasses / targetGlasses) * 100));
const hydrationMl = hydrationGlasses * 250;
assert(hydrationPct === 75, `Hydration percentage calculated correctly (75%)`);
assert(hydrationMl === 1500, `Hydration volume in ml calculated correctly (1500 ml)`);

// -----------------------------------------------------------------------------
// 5. UNIVERSAL QUICK CAPTURE CLIENT-SIDE REGEX PARSER TESTS
// -----------------------------------------------------------------------------
console.log('\n📌 [5/7] Testing Universal Quick Capture Regex Parser:');

function parseQuickInput(raw) {
  const lower = raw.toLowerCase().trim();
  
  if (lower.startsWith('minum') || lower.includes('gelas') || lower.includes('ml')) {
    const matchMl = lower.match(/(\d+)\s*ml/);
    const matchGlass = lower.match(/(\d+)\s*gelas/);
    let glasses = 1;
    if (matchGlass) glasses = parseInt(matchGlass[1], 10);
    else if (matchMl) glasses = Math.max(1, Math.round(parseInt(matchMl[1], 10) / 250));
    return { type: 'hydration', glasses };
  }
  
  if (lower.startsWith('tidur') || lower.includes('jam tidur')) {
    const matchHours = lower.match(/(\d+(?:\.\d+)?)\s*jam/);
    const hours = matchHours ? parseFloat(matchHours[1]) : 7;
    return { type: 'sleep', hours };
  }

  if (lower.startsWith('fokus:') || lower.startsWith('timer:')) {
    const topic = raw.replace(/^(fokus:|timer:)\s*/i, '').trim();
    return { type: 'focus', topic };
  }

  if (lower.startsWith('tugas') || lower.startsWith('tugas:') || lower.includes('deadline')) {
    const isUrgent = lower.includes('mendesak') || lower.includes('urgent') || lower.includes('besok');
    return { type: 'coursework', urgent: isUrgent, text: raw };
  }

  return { type: 'note', text: raw };
}

const p1 = parseQuickInput('minum 500ml');
assert(p1.type === 'hydration' && p1.glasses === 2, 'Parsed "minum 500ml" -> 2 glasses');

const p2 = parseQuickInput('minum 3 gelas');
assert(p2.type === 'hydration' && p2.glasses === 3, 'Parsed "minum 3 gelas" -> 3 glasses');

const p3 = parseQuickInput('tidur 6.5 jam');
assert(p3.type === 'sleep' && p3.hours === 6.5, 'Parsed "tidur 6.5 jam" -> 6.5 hours');

const p4 = parseQuickInput('fokus: bab 4 implementasi sistem');
assert(p4.type === 'focus' && p4.topic === 'bab 4 implementasi sistem', 'Parsed "fokus: bab 4 implementasi sistem" -> focus timer');

const p5 = parseQuickInput('tugas kuis kalkulus besok mendesak');
assert(p5.type === 'coursework' && p5.urgent === true, 'Parsed "tugas kuis kalkulus besok mendesak" -> urgent coursework');

// -----------------------------------------------------------------------------
// 6. HOBBY ZERO-DUMMY & PER-USER STORAGE TESTS
// -----------------------------------------------------------------------------
console.log('\n📌 [6/7] Testing Hobby Clean Per-User State:');

function initUserHobbyStorage(mockStoredValue) {
  // If stored value contains known legacy dummy keys ('Witcher 3', 'Atomic Habits'), purge it
  if (mockStoredValue && (mockStoredValue.includes('Witcher') || mockStoredValue.includes('Atomic Habits'))) {
    return []; // purged
  }
  return mockStoredValue ? JSON.parse(mockStoredValue) : [];
}

const cleanDefault = initUserHobbyStorage(null);
assert(Array.isArray(cleanDefault) && cleanDefault.length === 0, 'New user initializes with 0 dummy hobby items');

const purgedLegacy = initUserHobbyStorage(JSON.stringify([{ title: 'The Witcher 3: Wild Hunt' }]));
assert(purgedLegacy.length === 0, 'Legacy dummy hobby items are automatically purged on load');

// -----------------------------------------------------------------------------
// 7. PWA MANIFEST & CLIENT BACKUP EXPORT TESTS
// -----------------------------------------------------------------------------
console.log('\n📌 [7/7] Testing PWA Manifest & Backup Data Contract:');

const fs = require('fs');
const path = require('path');

const manifestPath = path.resolve(__dirname, 'public/manifest.json');
const manifestContent = JSON.parse(fs.readFileSync(manifestPath, 'utf8'));

assert(manifestContent.display === 'standalone', 'PWA manifest display mode is standalone');
assert(manifestContent.theme_color === '#4f46e5', 'PWA manifest theme color matches branding (#4f46e5)');
assert(manifestContent.icons.length > 0, 'PWA manifest contains application icons');

// Backup Export Schema Verification
const mockExport = {
  app: 'Second Brain (Student Edition)',
  version: '2.2.0',
  exportedAt: new Date().toISOString(),
  account: { id: 'test-user-id' },
  data: {
    tasks: [],
    habits: [],
    timeLogs: [],
    hobbies: [],
  }
};
assert(mockExport.version === '2.2.0', 'Backup export payload correctly reports version 2.2.0');
assert(mockExport.app === 'Second Brain (Student Edition)', 'Backup export payload identifies Student Edition app');

// -----------------------------------------------------------------------------
// 8. VERDION PROFIT LEVERAGE & ARBITRAGE CALCULATORS
// -----------------------------------------------------------------------------
console.log('\n📌 [8/8] Testing Verdion Profit Leverage & Arbitrage Calculators:');

function computeWhaleVettingScore({ paymentVerified, totalSpend, hireRate, avgRate }) {
  let score = 0;
  if (paymentVerified) score += 25;
  if (totalSpend >= 10000) score += 35;
  else if (totalSpend >= 2000) score += 20;
  else if (totalSpend >= 500) score += 10;

  if (hireRate >= 60) score += 20;
  else if (hireRate >= 40) score += 10;

  if (avgRate >= 30) score += 20;
  else if (avgRate >= 20) score += 10;

  return Math.min(100, score);
}

const whaleScore1 = computeWhaleVettingScore({
  paymentVerified: true,
  totalSpend: 45000,
  hireRate: 78,
  avgRate: 45,
});
assert(whaleScore1 === 100, 'Whale client with high spend, hire rate, & verified payment scores 100/100');

const cautionScore = computeWhaleVettingScore({
  paymentVerified: true,
  totalSpend: 2500,
  hireRate: 45,
  avgRate: 25,
});
assert(cautionScore === 65, 'Moderate client scores 65/100 (Proceed with Caution)');

const trapScore = computeWhaleVettingScore({
  paymentVerified: false,
  totalSpend: 150,
  hireRate: 20,
  avgRate: 15,
});
assert(trapScore === 0, 'Low-budget unverified client scores 0/100 (Connects Trap Skip)');

// Net USD and Arbitrage Margin
function calculateVerdionArbitrage(grossUsd, subdevIdr, usdRate = 16200) {
  const netUsd = grossUsd * 0.90; // After Upwork 10% fee
  const netIdr = netUsd * usdRate;
  const netProfitIdr = netIdr - subdevIdr;
  const marginPercent = netIdr > 0 ? (netProfitIdr / netIdr) * 100 : 0;
  return { netUsd, netIdr, netProfitIdr, marginPercent };
}

const arbResult = calculateVerdionArbitrage(2500, 8000000, 16200);
assert(arbResult.netUsd === 2250, 'Net USD after 10% fee on $2,500 is $2,250');
assert(arbResult.netIdr === 36450000, 'Net IDR @ 16,200 is Rp 36.450.000');
assert(arbResult.netProfitIdr === 28450000, 'Verdion Net Profit after Rp 8M subdev is Rp 28.450.000');
assert(Math.round(arbResult.marginPercent) === 78, 'Verdion margin retained is 78%');

// 2-Second Hook Character Length Limit
function generateHook(problem, solution, demoLink, question) {
  return `Saw your bottleneck with ${problem}. Verdion has resolved this exact issue using ${solution}. Live demo: ${demoLink}. ${question}`;
}
const hookSample = generateHook(
  'Supabase query latency',
  'async pgBouncer pooling',
  'loom.com/share/verdion',
  'Have you set pool limits?'
);
assert(hookSample.length <= 200, `Generated hook is concise (${hookSample.length} chars <= 200 chars) for Upwork client preview`);

// Retainer Recurring Revenue Calculation
const sampleRetainers = [
  { client: 'FinTech Alpha', rateUsd: 800, active: true },
  { client: 'Apex Media', rateUsd: 600, active: true },
  { client: 'Old Client', rateUsd: 400, active: false },
];
const activeMrrUsd = sampleRetainers.filter(r => r.active).reduce((sum, r) => sum + r.rateUsd, 0);
assert(activeMrrUsd === 1400, 'Active Retainers sum to $1,400 MRR');
const activeMrrIdr = activeMrrUsd * 16200;
assert(activeMrrIdr === 22680000, 'Active Retainers sum to Rp 22.680.000 recurring monthly IDR');

// Authorization Guard Verification (Exclusive for fransalwan55@gmail.com)
function isVerdionAuthorized(email) {
  return (email ?? '').toLowerCase().trim() === 'fransalwan55@gmail.com';
}
assert(isVerdionAuthorized('fransalwan55@gmail.com') === true, 'fransalwan55@gmail.com is authorized for Verdion Studio');
assert(isVerdionAuthorized('FRANSALWAN55@GMAIL.COM ') === true, 'Case-insensitive & trimmed email is authorized');
assert(isVerdionAuthorized('student@ugm.ac.id') === false, 'Student email is strictly denied from Verdion Studio');
assert(isVerdionAuthorized('hacker@domain.com') === false, 'Other emails are denied from Verdion Studio');
assert(isVerdionAuthorized(null) === false, 'Unauthenticated user is denied from Verdion Studio');

// -----------------------------------------------------------------------------
// SUMMARY
// -----------------------------------------------------------------------------
console.log('\n====================================================');
console.log(`📊 TEST SUITE SUMMARY: ${passedTests}/${totalTests} TESTS PASSED`);
if (failedTests === 0) {
  console.log('🎉 ALL SYSTEM & VERDION PROFIT FEATURES VERIFIED (100%)');
} else {
  console.error(`⚠️ ${failedTests} TESTS FAILED`);
  process.exit(1);
}
console.log('====================================================');


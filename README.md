# Radhu Industries — Auto Tyre Stock Portal

Bhot hi simple Django + Tailwind stock management portal, jo aapki
`Auto_Tyre_Daly_Stock` Excel file ke fields pe based hai.

## Fields (jaisa file mai the)
- **TYRE**, **PATTERN**, **TYPE**
- **Monthly Curing** → is mahine ki total production (automatic, entries se calculate hota hai)
- **Repair Tyre Stock**
- **RFM OK Tyre** (return from market — good hai, bika nahi)
- **2025 Old Tyres**
- **STOCK**
- **On hold for Export / OR**
- **TOTAL STOCK** (= Stock + Repair + RFM OK + Old Tyres + On Hold, automatic)
- **Monthly Despatch** → is mahine ki total dispatch (automatic)

Data pehle se load hai — aapki file ki sabse latest sheet (12/07/2026 wali,
jisme RFM OK Tyre bhi tha) se 52 tyre items already daale hue hain.

## Kaise chalayen (local computer par)

1. Python 3.10+ install hona chahiye.
2. Terminal mai:
   ```
   cd radhu
   pip install django
   python manage.py runserver
   ```
3. Browser mai kholein: **http://127.0.0.1:8000/**

## Login

| Username | Password   | Role |
|----------|-----------|------|
| admin    | radhu@2026 | Admin (Django admin panel `/admin/` bhi access hai) |
| staff1   | radhu123   | Normal staff login |

Naye users banane ke liye `/admin/` mai jaake "Users" mai add kar sakte ho,
ya command se:
```
python manage.py createsuperuser
```
Har entry (production / dispatch / adjustment) ke saath us waqt login kiye
hue user ka naam automatic save ho jata hai, remark ke saath.

## Portal mai kya kya hai

1. **Stock (Dashboard)** — sabhi tyres ka current stock, search bhi kar sakte ho.
2. **+ Production** — daily production entry, quantity seedha "STOCK" mai add
   ho jati hai. Neeche recent entries bhi dikhti hain.
3. **+ Dispatch** — daily dispatch entry. Dropdown se batana hota hai kis
   bucket se maal gaya (STOCK / Repair / RFM OK / 2025 Old / On Hold-Export),
   wahi bucket automatic minus ho jata hai.
4. **Adjust** — Repair / RFM OK / 2025 Old / On Hold buckets ko manually
   (+/-) theek karne ke liye, jab koi tyre repair hoke aaye, market se
   return aaye, hold pe rakha jaye, waghera.
5. **Entries** — date wise ya month wise saari entries dekhne ke liye,
   type (production/dispatch/adjustment) se filter bhi ho sakta hai.
6. **Monthly Report** — kisi bhi mahine ka Monthly Curing (production) aur
   Monthly Despatch total, tyre-wise.
7. **+ New Tyre** — naya tyre (TYRE + PATTERN + TYPE) master list mai add
   karne ke liye.

## Note
- Yeh development server hai (`runserver`), sirf local / office network
  use ke liye theek hai. Agar internet par hamesha ke liye chalana ho
  (sab jagah se access), to bata dena — proper deployment (VPS/hosting)
  ka setup bhi kar denge.
- Database `db.sqlite3` mai hai, already seeded hai. Isko delete mat
  karna warna data chala jayega.

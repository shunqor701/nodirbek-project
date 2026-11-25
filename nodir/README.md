# Print navbati

> **Universitet yakuniy loyihasi**  
> **Talaba:** Ergashov Nodirbek O‘tkirjon o‘g‘li  
> **Fan:** Dasturlash  
> **Mavzu:** Nusxa ko‘paytirish markazi buyurtmalarini boshqarish tizimi

## Loyiha nima haqida?

**Print navbati** — talabalar PDF hujjatlarini markazga oldindan yuborishi, chop etish parametrlarini tanlashi va buyurtma narxini darhol bilishi uchun yaratilgan web-axborot tizimi.

An’anaviy jarayonda talaba markazga boradi, navbat kutadi, faylni operatorga beradi va narxni joyida hisoblatadi. Ushbu tizimda esa:

1. talaba tizimga kiradi;
2. PDF faylni yuklaydi;
3. betlar oralig‘i, nusxalar soni, rang turi, bir/ikki tomonlama chop etish va muqova turini tanlaydi;
4. tizim PDF sahifalarini tekshiradi va narxni avtomatik hisoblaydi;
5. buyurtmaga yagona olish kodi beriladi;
6. operator buyurtmalarni navbat asosida chop etadi;
7. buyurtma tayyor bo‘lganda talaba kod orqali navbatsiz olib ketadi.

Loyiha kichik nusxa ko‘paytirish markazi uchun mo‘ljallangan. U murakkab mikroservislar yoki alohida frontend frameworklarisiz, tushunarli Flask monoliti sifatida qurilgan. Shu sababli kodni himoyada tushuntirish, o‘zgartirish va kengaytirish oson.

## Asosiy imkoniyatlar

### Talaba

- ro‘yxatdan o‘tish va tizimga kirish;
- PDF fayl yuklash;
- PDF sahifalar sonini avtomatik aniqlash;
- betlar oralig‘ini tanlash;
- nusxalar sonini belgilash;
- oq-qora yoki rangli chop etishni tanlash;
- bir tomonlama yoki ikki tomonlama chop etishni tanlash;
- muqovasiz, oddiy yoki spiral muqovani tanlash;
- oddiy yoki shoshilinch buyurtma yaratish;
- buyurtma narxini ko‘rish;
- olish kodini olish;
- o‘z buyurtmalarini kuzatish va ruxsat etilgan holatda bekor qilish.

### Operator

- buyurtmalar navbatini ko‘rish;
- shoshilinch buyurtmalarni ustuvor ko‘rish;
- buyurtmani **Chop etilmoqda** holatiga o‘tkazish;
- buyurtmani **Tayyor** holatiga o‘tkazish;
- PDF faylni himoyalangan route orqali yuklab olish;
- olish kodini tekshirish;
- tayyor buyurtmani topshirilgan deb belgilash.

### Markaz egasi

- buyurtmalar haqida umumiy ma’lumotni ko‘rish;
- oq-qora va rangli bet narxlarini sozlash;
- oddiy va spiral muqova narxlarini sozlash;
- shoshilinch buyurtma ustamasini sozlash;
- maksimal fayl hajmini belgilash.

## Buyurtma holatlari

```text
Yangi → Chop etilmoqda → Tayyor → Topshirildi
  └──────────────────────────────→ Bekor qilindi
```

Buyurtma yaratilgan paytdagi narx va parametrlar alohida saqlanadi. Keyinchalik markaz egasi narxlarni o‘zgartirsa ham, avvalgi buyurtmalar narxi o‘zgarmaydi.

## Texnologiyalar

| Qism | Texnologiya |
|---|---|
| Backend | Python 3.10+, Flask |
| Ma’lumotlar bazasi | SQLite, Flask-SQLAlchemy |
| Autentifikatsiya | Flask-Login |
| Form validation | Flask-WTF, WTForms, CSRF |
| PDF tahlili | pypdf |
| Parol xavfsizligi | Werkzeug password hashing |
| Frontend | Jinja2, Bootstrap 5, Bootstrap Icons |
| Testlar | pytest, pytest-flask |
| Konfiguratsiya | python-dotenv |

## Loyiha tuzilmasi

```text
nodir/
├── app/
│   ├── __init__.py          # Application factory, extension va error handlerlar
│   ├── extensions.py        # db, login_manager, csrf
│   ├── models.py            # User, Order va boshqa modellar
│   ├── utils.py             # Narx, PDF, kod va fayl yordamchilari
│   ├── decorators.py        # role_required dekoratori
│   ├── auth/routes.py       # Login va ro‘yxatdan o‘tish
│   ├── student/routes.py    # Talaba funksiyalari
│   ├── operator/routes.py   # Operator funksiyalari
│   ├── owner/routes.py      # Egasi funksiyalari
│   └── main/routes.py       # Bosh sahifa
├── base.html                # Umumiy Jinja2 layout
├── index.html               # Bosh sahifa
├── auth/                    # Kirish va ro‘yxatdan o‘tish sahifalari
├── errors/                  # Xato sahifalari
├── operator/                # Operator sahifalari
├── owner/                   # Egasi sahifalari
├── student/                 # Talaba sahifalari
├── static/css/style.css     # Umumiy UI dizayn
├── tests/                   # Avtomatik testlar
├── uploads/                 # Yuklangan PDF fayllar
├── instance/                # SQLite bazasi
├── config.py
├── run.py
├── seed.py
├── cleanup_files.py
├── ER_DIAGRAM.md
└── requirements.txt
```

## O‘rnatish va ishga tushirish

### 1. Virtual muhit yaratish

Linux/macOS:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Windows:

```powershell
py -m venv .venv
.venv\Scripts\activate
```

### 2. Kutubxonalarni o‘rnatish

```bash
pip install -r requirements.txt
```

### 3. Test hisoblari va boshlang‘ich sozlamalarni yaratish

```bash
python seed.py
```

Seed skripti quyidagi hisoblarni yaratadi:

| Rol | Login | Parol |
|---|---|---|
| Operator | `operator` | `Operator123!` |
| Markaz egasi | `owner` | `Owner123!` |

Oddiy ro‘yxatdan o‘tish orqali faqat `student` roli beriladi. Foydalanuvchi o‘zini operator yoki owner qilib ro‘yxatdan o‘tkaza olmaydi.

### 4. Serverni ishga tushirish

```bash
flask --app run.py run --debug
```

Brauzerda [http://127.0.0.1:5000](http://127.0.0.1:5000) manzilini oching.

Serverni to‘xtatish:

```text
Ctrl + C
```

## Testlarni ishga tushirish

```bash
python -m pytest -q tests
```

Testlar autentifikatsiya, rol cheklovi va narx hisoblashni tekshiradi.

## Xavfsizlik

- parollar bazada oddiy matn ko‘rinishida saqlanmaydi;
- barcha formalar CSRF token bilan himoyalangan;
- rollar backend decoratorlari bilan tekshiriladi;
- talaba faqat o‘z buyurtmalarini ko‘ra oladi;
- fayl nomlari `secure_filename` va tasodifiy prefiks bilan saqlanadi;
- faqat PDF kengaytmali fayllar qabul qilinadi;
- PDF fayllar bevosita public papkadan emas, himoyalangan route orqali beriladi;
- fayl hajmi `MAX_CONTENT_LENGTH` bilan cheklanadi;
- 403, 404, 413 va 500 xatolari uchun alohida sahifalar mavjud;
- operator va owner rollari faqat `seed.py` orqali beriladi.

## Fayllarni tozalash

30 kundan eski yuklangan fayllarni o‘chirish uchun:

```bash
python cleanup_files.py
```

Buyurtma va uning bazadagi ma’lumotlari saqlanadi, faqat server diskidagi PDF fayl o‘chiriladi.

## Muhim arxitektura qarorlari

- **Application Factory:** testlar uchun alohida konfiguratsiya va SQLite in-memory bazasidan foydalanish imkonini beradi.
- **Blueprint:** autentifikatsiya, talaba, operator va owner kodlarini ajratadi.
- **Decimal/Numeric:** pul hisoblarida `float` xatolarini oldini oladi.
- **Snapshot narx:** buyurtma yaratilganda hisoblangan summa va tarkibiy narxlar `PrintParameter` jadvalida saqlanadi.
- **Hashlangan olish kodi:** olish kodi bazada oddiy matn sifatida saqlanmaydi.
- **Role-based access control:** frontenddagi tugmalarni yashirishdan tashqari, har bir protected route server tomonida ham tekshiriladi.

## Kelajakdagi kengaytirishlar

- real onlayn to‘lov integratsiyasi;
- email yoki Telegram xabarnomalari;
- tayyor bo‘lish vaqtini taxminiy ko‘rsatish;
- statistikalar va Chart.js grafiklari;
- administrator audit jurnali;
- PostgreSQL ga migratsiya;
- Flask-Migrate bilan versiyali migratsiyalar.

## Mualliflik

Ushbu loyiha o‘quv maqsadida, universitetning “Dasturlash” fanidan yakuniy loyiha sifatida ishlab chiqilgan.

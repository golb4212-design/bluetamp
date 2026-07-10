# BlueTamp — قالب اختصاصی صفحه اشتراک پاسارگارد

قالب فارسی، تک‌فایلی و واکنش‌گرا برای صفحه اشتراک کاربران PasarGuard؛ مناسب موبایل، تبلت و دسکتاپ.

## تغییرات نسخه ۲

- اضافه‌شدن فونت متغیر فارسی Vazirmatn
- ساخت خودکار QR اشتراک، بدون دکمه «ساخت QR»
- حذف کامل بخش و دانلود WireGuard
- دریافت اطلاعات از مسیر جدید `/raw` با پشتیبانی از مسیرهای قدیمی `/info`، `/apps` و `/links`
- اصلاح دریافت و نمایش اپلیکیشن‌های پاسارگارد
- نمایش آیکن، توضیحات، لینک‌های دانلود و دکمه Import اپلیکیشن‌ها
- جلوگیری از بیرون‌زدن متن‌ها، لینک اشتراک و کانفیگ‌ها در موبایل
- دریافت خودکار `support-url` بر اساس مدیر یا نماینده مالک کاربر

## تنظیم پشتیبانی هر نماینده

در قسمت ویرایش مدیر یا نماینده، داخل فیلد **آدرس پشتیبانی** لینک کامل وارد شود:

```text
https://t.me/BlueTampSupport
```

یا:

```text
https://wa.me/491234567890
```

قالب آدرس پشتیبانی را خودکار از پاسارگارد دریافت می‌کند؛ بنابراین نیازی به قرار دادن لینک نمایندگان داخل کد نیست.

## فایل‌های مخزن

این سه فایل را در شاخه `main` مخزن قرار دهید:

```text
index.html
README.md
install.sh
```

مخزن تنظیم‌شده:

```text
https://github.com/golb4212-design/bluetamp
```

## نصب یا به‌روزرسانی خودکار

بعد از آپلود فایل‌های جدید در GitHub، روی سرور اجرا کنید:

```bash
curl -4 -fsSL https://raw.githubusercontent.com/golb4212-design/bluetamp/main/install.sh | sudo bash
```

این اسکریپت قبل از جایگزینی قالب و ویرایش `.env` نسخه پشتیبان می‌سازد.

## به‌روزرسانی دستی

```bash
sudo mkdir -p /var/lib/pasarguard/templates/subscription/

sudo curl -4 -fL --connect-timeout 20 --retry 3 \
-o /var/lib/pasarguard/templates/subscription/index.html \
https://raw.githubusercontent.com/golb4212-design/bluetamp/main/index.html
```

فایل تنظیمات را باز کنید:

```bash
sudo nano /opt/pasarguard/.env
```

این مقادیر باید وجود داشته باشند:

```env
CUSTOM_TEMPLATES_DIRECTORY="/var/lib/pasarguard/templates/"
SUBSCRIPTION_PAGE_TEMPLATE="subscription/index.html"
```

سپس:

```bash
sudo pasarguard restart
```

## تنظیم برند

در انتهای `index.html` بخش زیر قابل ویرایش است:

```js
const BRAND = {
  name: 'BLUETAMP',
  mark: 'B',
  tagline: 'FAST • STABLE • SECURE',
  primary: '#7357ff',
  secondary: '#23a7ff',
  statusUrl: '#',
  rulesUrl: '#',
  copyright: '© 2026 BlueTamp. تمام حقوق محفوظ است.'
};
```

آدرس پشتیبانی را داخل `BRAND` قرار ندهید؛ این مقدار برای هر نماینده از پاسارگارد دریافت می‌شود.

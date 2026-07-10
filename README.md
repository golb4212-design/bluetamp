# BlueTamp — قالب اختصاصی صفحه اشتراک پاسارگارد

قالب فارسی، واکنش‌گرا و تک‌فایلی برای صفحه اشتراک کاربران PasarGuard. این نسخه برای موبایل، تبلت و دسکتاپ طراحی شده و اطلاعات پشتیبانی هر مدیر یا نماینده را به‌صورت خودکار از خود پنل دریافت می‌کند.

## امکانات

- طراحی تیره و حرفه‌ای با چیدمان واکنش‌گرا
- نمایش وضعیت حساب، حجم، مصرف، باقی‌مانده، تاریخ پایان و محدودیت دستگاه
- نمودار مصرف ۲۴ ساعت، ۷ روز و ۳۰ روز
- دریافت خودکار اپلیکیشن‌ها و کانفیگ‌ها از پاسارگارد
- کپی لینک اشتراک و تمام کانفیگ‌ها
- QR Code و دانلود کانفیگ WireGuard
- دریافت خودکار `support-url` بر اساس مدیر/نماینده مالک کاربر
- بدون نیاز به واردکردن لینک تلگرام یا واتساپ داخل کد

## تنظیم پشتیبانی هر نماینده

در پنل پاسارگارد، هنگام ایجاد یا ویرایش مدیر/نماینده، داخل فیلد **آدرس پشتیبانی** یک لینک کامل وارد کنید؛ برای نمونه:

```text
https://t.me/BlueTampSupport
```

یا:

```text
https://wa.me/491234567890
```

قالب مقدار `support-url` را از پاسخ `/info` دریافت می‌کند. اگر لینک مربوط به تلگرام یا واتساپ باشد، عنوان و رنگ دکمه نیز به‌صورت خودکار تنظیم می‌شود.

> فیلد «شناسه تلگرام» برای ارتباط ربات و اعلان‌های داخلی پنل است. برای نمایش دکمه ارتباط مشتری باید فیلد «آدرس پشتیبانی» تکمیل شود.

## نصب سریع از GitHub

ابتدا فایل‌های این پروژه را در شاخه `main` مخزن زیر قرار دهید:

```text
https://github.com/golb4212-design/bluetamp
```

سپس روی سرور پاسارگارد اجرا کنید:

```bash
sudo mkdir -p /var/lib/pasarguard/templates/subscription/

sudo wget -N -O /var/lib/pasarguard/templates/subscription/index.html \
https://raw.githubusercontent.com/golb4212-design/bluetamp/main/index.html
```

فایل تنظیمات را باز کنید:

```bash
sudo nano /opt/pasarguard/.env
```

این مقادیر باید داخل فایل باشند:

```env
CUSTOM_TEMPLATES_DIRECTORY="/var/lib/pasarguard/templates/"
SUBSCRIPTION_PAGE_TEMPLATE="subscription/index.html"
```

در پایان پنل را ری‌استارت کنید:

```bash
sudo pasarguard restart
```

## نصب خودکار

بعد از آپلود فایل `install.sh` در مخزن، می‌توانید این دستور را اجرا کنید:

```bash
curl -fsSL https://raw.githubusercontent.com/golb4212-design/bluetamp/main/install.sh | sudo bash
```

اسکریپت قبل از تغییر فایل‌ها، از قالب و فایل `.env` نسخه پشتیبان می‌گیرد.

## تغییر نام و رنگ برند

در انتهای فایل `index.html` بخش `BRAND` را ویرایش کنید:

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

آدرس پشتیبانی را در این بخش قرار ندهید؛ قالب آن را برای هر نماینده از پاسارگارد می‌گیرد.

## به‌روزرسانی قالب

پس از جایگزین‌کردن `index.html` در GitHub، روی سرور دوباره اجرا کنید:

```bash
sudo wget -N -O /var/lib/pasarguard/templates/subscription/index.html \
https://raw.githubusercontent.com/golb4212-design/bluetamp/main/index.html

sudo pasarguard restart
```

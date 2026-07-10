# BlueTamp PasarGuard Template v6

## تغییرات نسخه ۶

- نام ثابت قالب حذف شده و عنوان بالای صفحه از **عنوان پروفایل ادمین** دریافت می‌شود.
- عنوان فرمت‌شده از هدر `profile-title` و همچنین `headers` پاسخ `/raw` خوانده می‌شود.
- وضعیت حساب هر ۱۵ ثانیه از `/info` تازه‌سازی می‌شود و نشانگر زنده دارد.
- QR برای لینک اشتراک و هر کانفیگ فعال است.
- اپلیکیشن‌ها از داده Jinja، `/raw` و `/apps` دریافت می‌شوند و در صورت خالی‌بودن دو بار تلاش مجدد انجام می‌شود.
- لینک پشتیبانی نماینده از `support-url` خوانده می‌شود.
- WireGuard نمایش داده نمی‌شود.

## نصب

فایل‌های `index.html` و `install.sh` را در ریشه مخزن `golb4212-design/bluetamp` جایگزین کنید و سپس اجرا کنید:

```bash
curl -4 -fsSL https://raw.githubusercontent.com/golb4212-design/bluetamp/main/install.sh | sudo bash
```

یا فقط قالب را به‌روزرسانی کنید:

```bash
sudo curl -4 -fL --connect-timeout 20 --retry 3 \
  -H "Cache-Control: no-cache" \
  "https://raw.githubusercontent.com/golb4212-design/bluetamp/main/index.html?v=6" \
  -o /var/lib/pasarguard/templates/subscription/index.html

sudo pasarguard restart
```

بررسی نسخه:

```bash
grep -n "BlueTamp PasarGuard Subscription Template v6.0.0" \
  /var/lib/pasarguard/templates/subscription/index.html
```

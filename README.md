# BlueTamp PasarGuard Template v4

قالب تک‌فایلی و واکنش‌گرا برای صفحه اشتراک PasarGuard.

## ویژگی‌ها

- دریافت اولیه `user`، `links` و `apps` مستقیماً از Jinja پاسارگارد
- fallback از `/info`، `/apps` و `/raw`
- دریافت خودکار `support-url` هر نماینده
- تب‌های حساب، کانفیگ‌ها و اپلیکیشن‌ها
- تشخیص سیستم‌عامل و گروه‌بندی برنامه‌ها
- نمودار مصرف ۱ روز و ۷ روز
- هشدار کمبود حجم و زمان
- نمایش HWID
- تم تاریک و روشن
- بدون QR و بدون WireGuard
- عدم ذخیره توکن و کانفیگ در LocalStorage

## نصب

فایل `index.html` را در ریشه مخزن زیر جایگزین کنید:

```text
golb4212-design/bluetamp
```

سپس روی سرور اجرا کنید:

```bash
curl -4 -fsSL https://raw.githubusercontent.com/golb4212-design/bluetamp/main/install.sh | sudo bash
```

یا نصب دستی:

```bash
sudo mkdir -p /var/lib/pasarguard/templates/subscription/
sudo curl -4 -fL --connect-timeout 20 --retry 3 \
  -H "Cache-Control: no-cache" \
  "https://raw.githubusercontent.com/golb4212-design/bluetamp/main/index.html?v=4" \
  -o /var/lib/pasarguard/templates/subscription/index.html
```

در `/opt/pasarguard/.env`:

```env
CUSTOM_TEMPLATES_DIRECTORY="/var/lib/pasarguard/templates/"
SUBSCRIPTION_PAGE_TEMPLATE="subscription/index.html"
```

سپس:

```bash
sudo pasarguard restart
```

بررسی نسخه:

```bash
grep -n "BlueTamp PasarGuard Subscription Template v4.0.0" \
  /var/lib/pasarguard/templates/subscription/index.html
```

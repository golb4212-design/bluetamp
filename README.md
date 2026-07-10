# BlueTamp PasarGuard Template v7

## امکانات جدید

- نمایش لوکیشن و گره‌های موجود در کانفیگ‌های همان کاربر در صفحه حساب
- تشخیص کشور از پرچم، نام فارسی/انگلیسی یا کد کشور داخل نام کانفیگ
- نمایش پرچم، نوع پروتکل، دامنه و پورت هر گره
- تست زنده TCP از سرور پنل تا هر گره و نمایش Latency
- رنگ‌بندی پینگ: سبز کمتر از ۱۰۰ms، زرد ۱۰۰ تا ۲۰۰ms، قرمز بیشتر از ۲۰۰ms یا آفلاین
- بروزرسانی خودکار هر ۶۰ ثانیه و دکمه «تست مجدد»
- Cache سمت سرور برای جلوگیری از فشار زیاد روی گره‌ها
- سرویس پینگ فقط توکن اشتراک را می‌گیرد؛ کانفیگ خام را به مرورگر برنمی‌گرداند
- QR سابسکریپشن و کانفیگ‌ها، عنوان پروفایل ادمین و وضعیت زنده حساب همچنان فعال‌اند

## فایل‌های لازم در GitHub

این فایل‌ها را در ریشه مخزن `golb4212-design/bluetamp` قرار دهید:

```text
index.html
install.sh
bluetamp_nodes.py
bluetamp-nodes.service
uninstall-ping-service.sh
README.md
```

## نصب کامل

```bash
curl -4 -fsSL https://raw.githubusercontent.com/golb4212-design/bluetamp/main/install.sh | sudo bash
```

اسکریپت موارد زیر را انجام می‌دهد:

1. قالب v7 را نصب می‌کند.
2. سرویس `bluetamp-nodes` را روی پورت `2087` راه‌اندازی می‌کند.
3. گواهی TLS تنظیم‌شده در `/opt/pasarguard/.env` را برای سرویس پینگ استفاده می‌کند.
4. در صورت فعال‌بودن UFW، پورت TCP/2087 را باز می‌کند.
5. پاسارگارد را ری‌استارت می‌کند.

## بررسی سرویس

```bash
sudo systemctl status bluetamp-nodes --no-pager
sudo journalctl -u bluetamp-nodes -n 50 --no-pager
```

در نصب مستقیم HTTPS:

```bash
curl -k https://127.0.0.1:2087/health
```

خروجی سالم:

```json
{"ok":true,"tls":true,"port":2087}
```

## نکات فنی پینگ

- عدد نمایش‌داده‌شده ICMP Ping نیست؛ زمان اتصال TCP از سرور پنل به `host:port` کانفیگ است.
- برای دامنه‌های پشت CDN، زمان اتصال به لبه CDN اندازه‌گیری می‌شود، نه الزاماً سرور نهایی.
- هر توکن حداکثر ۳۶ گره را بررسی می‌کند.
- نتایج ۴۵ ثانیه Cache می‌شوند.
- صفحه هر ۶۰ ثانیه اطلاعات را تازه می‌کند.
- اگر سرویس در دسترس نباشد، لوکیشن‌ها و پرچم‌ها همچنان نمایش داده می‌شوند و فقط پینگ «—» خواهد بود.

## وقتی گواهی TLS خودکار پیدا نشد

فایل زیر را باز کنید:

```bash
sudo nano /etc/bluetamp-nodes.env
```

مسیر گواهی دامنه را وارد کنید:

```env
BT_SSL_CERTFILE=/var/lib/pasarguard/certs/example.com/fullchain.pem
BT_SSL_KEYFILE=/var/lib/pasarguard/certs/example.com/key.pem
```

سپس:

```bash
sudo systemctl restart bluetamp-nodes
```

## بررسی نسخه قالب

```bash
grep -n "BlueTamp PasarGuard Subscription Template v7.0.0" \
  /var/lib/pasarguard/templates/subscription/index.html
```

## حذف سرویس پینگ

```bash
curl -4 -fsSL https://raw.githubusercontent.com/golb4212-design/bluetamp/main/uninstall-ping-service.sh | sudo bash
```

## امنیت

- سرویس فقط Origin هم‌نام با دامنه خودش را قبول می‌کند.
- آدرس گره‌ها را از `/raw` پاسارگارد می‌خواند و مقصد دلخواه مرورگر را قبول نمی‌کند.
- محدودیت درخواست، Cache، Timeout و سقف تعداد گره دارد.
- کانفیگ کامل در پاسخ سرویس برگردانده نمی‌شود.

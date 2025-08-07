FROM python:3.11-slim

# نصب وابستگی‌ها
RUN apt-get update && apt-get install -y \
    openjdk-17-jre \
    openjdk-17-jdk \
    && apt-get clean

# تنظیم محیط
WORKDIR /app
COPY . .

# نصب پکیج‌های Python
RUN pip install --no-cache-dir python-telegram-bot==20.7 requests

ENV PORT=5000
ENV KEYSTORE_PATH=/app/my.keystore
ENV KEYSTORE_PASSWORD=123456
ENV KEY_ALIAS=mykey
ENV KEY_PASSWORD=123456

CMD ["python", "bot.py"]

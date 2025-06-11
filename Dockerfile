FROM python:3.9-slim

# 非 root ユーザーの作成
RUN useradd --create-home botuser
WORKDIR /home/botuser/app
USER botuser

# システム依存＆ロケール整備
USER root
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
    chromium chromium-driver \
    locales tzdata vim less curl wget unzip jq gnupg ca-certificates \
 && localedef -f UTF-8 -i ja_JP ja_JP.UTF-8 \
 && ln -fs /usr/share/zoneinfo/Asia/Tokyo /etc/localtime \
 && dpkg-reconfigure -f noninteractive tzdata \
 && rm -rf /var/lib/apt/lists/*

ENV CHROME_BIN=/usr/bin/chromium
ENV CHROMEDRIVER_PATH=/usr/bin/chromedriver

# Python環境：requirements.txt を使う
USER botuser
COPY --chown=botuser:botuser requirements.txt .
RUN pip install --no-cache-dir --upgrade pip setuptools \
 && pip install --no-cache-dir -r requirements.txt

# アプリコードをコピー
COPY --chown=botuser:botuser . .

# デフォルトのCMD
CMD ["python", "-m", "bot.main"]

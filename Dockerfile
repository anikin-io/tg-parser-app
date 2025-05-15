FROM python:3.12

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        git \
        build-essential \
        python3-dev \
        libssl-dev \
        libffi-dev \
        pkg-config \
        gcc \
        speedtest-cli \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

RUN git clone https://github.com/xtekky/gpt4free.git ./gpt4free

RUN pip3 install --no-cache-dir -r ./gpt4free/requirements.txt

COPY requirements.txt .
RUN pip3 install --no-cache-dir -r ./requirements.txt \
    && pip3 install --no-cache-dir git+https://github.com/thedemons/opentele.git

COPY . .

ENV PYTHONPATH=/app

CMD ["python3", "-u", "main.py"]
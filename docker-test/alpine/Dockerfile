FROM alpine:3.18

ENV PYTHONUNBUFFERED=1
ENV ZENMON_AGENT_VERSION=2.0.0

# Install dependencies
RUN apk add --no-cache \
    python3 \
    py3-pip \
    supervisor \
    curl \
    procps \
    shadow \
    gcc \
    python3-dev \
    musl-dev \
    linux-headers \
    && rm -rf /var/cache/apk/*

WORKDIR /app

# Install Python packages
RUN pip3 install --no-cache-dir \
    requests==2.31.0 \
    psutil==5.9.5

# Create zenmon user
RUN adduser -D -s /bin/false -h /app zenmon \
    && chown -R zenmon:zenmon /app

# Create log directory
RUN mkdir -p /var/log/zenmon /var/log/supervisor \
    && chown -R zenmon:zenmon /var/log/zenmon

# Copy files - FIXED: using correct agent filename
COPY docker-test/alpine/supervisord.conf /etc/supervisor/supervisord.conf
COPY zenmon-agent-python-v2.0.py /app/zenmon_agent.py
COPY docker-test/health_server.py /app/health_server.py
RUN chmod +x /app/zenmon_agent.py /app/health_server.py \
    && chown zenmon:zenmon /app/zenmon_agent.py /app/health_server.py

EXPOSE 8080

USER root
CMD ["/usr/bin/supervisord", "-n", "-c", "/etc/supervisor/supervisord.conf"]

LABEL maintainer="ZenMon Development Team"
LABEL description="ZenMon Agent v2.0 for Alpine Linux"
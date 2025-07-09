FROM rockylinux:9

ENV PYTHONUNBUFFERED=1
ENV ZENMON_AGENT_VERSION=2.0.0

# Install dependencies (added gcc and python3-devel for psutil compilation)
RUN dnf install -y epel-release \
    && dnf install -y \
    python3 \
    python3-pip \
    python3-devel \
    gcc \
    supervisor \
    procps-ng \
    && dnf clean all

WORKDIR /app

# Install Python packages
RUN pip3 install --no-cache-dir \
    requests==2.31.0 \
    psutil==5.9.5

# Create zenmon user
RUN useradd -r -s /sbin/nologin -d /app zenmon \
    && chown -R zenmon:zenmon /app

# Create log directory
RUN mkdir -p /var/log/zenmon /var/log/supervisor \
    && chown -R zenmon:zenmon /var/log/zenmon

# Copy files - FIXED: using correct agent filename and supervisor path
COPY docker-test/rocky/supervisord.conf /etc/supervisor/supervisord.conf
COPY zenmon-agent-python-v2.0.py /app/zenmon_agent.py
COPY docker-test/health_server.py /app/health_server.py
RUN chmod +x /app/zenmon_agent.py /app/health_server.py \
    && chown zenmon:zenmon /app/zenmon_agent.py /app/health_server.py

EXPOSE 8080

USER root
CMD ["/usr/bin/supervisord", "-n", "-c", "/etc/supervisor/supervisord.conf"]

LABEL maintainer="ZenMon Development Team"
LABEL description="ZenMon Agent v2.0 for Rocky Linux 9"
FROM python:3.13-alpine
LABEL org.opencontainers.image.source=https://github.com/saveweb/komodo-tg-relay
LABEL org.opencontainers.image.description="Komodo Custom Alerter to Telegram relay"
COPY app.py /app.py
USER nobody
EXPOSE 8080
CMD ["python3", "-u", "/app.py"]

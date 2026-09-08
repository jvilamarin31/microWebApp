FROM python:3.10-slim

WORKDIR /app

# Dependencias del sistema (compilacion de mysqlclient)
RUN apt-get update && apt-get install -y --no-install-recommends \
        gcc \
        python3-dev \
        default-libmysqlclient-dev \
        pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Dependencias de Python
RUN pip install --no-cache-dir \
        Flask==2.3.3 \
        Flask-Cors==4.0.0 \
        Flask-SQLAlchemy==3.1.1 \
        mysqlclient==2.2.4 \
        PyMySQL==1.1.0 \
        requests==2.31.0 \
        python-dotenv==1.0.1

COPY . .

EXPOSE 5002

CMD ["python", "run.py"]

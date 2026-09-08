FROM python:3.10-slim

WORKDIR /app

# Dependencias de Python
RUN pip install --no-cache-dir \
        Flask==2.3.3 \
        Flask-Cors==4.0.0 \
        requests==2.31.0 \
        python-dotenv==1.0.1

COPY . .

EXPOSE 5001

CMD ["python", "run.py"]

FROM python:3.11

ENV FQDN="127.0.0.1:5000"

# Install Printer Driver
RUN apt-get update && apt-get install -y \
    cups-client \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /requirements.txt
RUN pip install -r /requirements.txt

COPY src/ /app
WORKDIR /app

EXPOSE 5000/tcp

CMD ["python", "app.py"]

FROM python:3.11

ENV FQDN="127.0.0.1:5000"

# Install Printer Driver
RUN apt-get update && apt-get install -y \
    cups \
    printer-driver-all \
    cups-pdf \
    cups-client \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /requirements.txt
RUN pip install -r /requirements.txt

COPY src/ /app
WORKDIR /app

EXPOSE 5000/tcp

RUN echo "service cups start && python app.py" > entrypoint.sh

CMD ["sh", "entrypoint.sh"]

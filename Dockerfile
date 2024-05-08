FROM python:3.11

# Install Printer Driver
RUN apt-get update && apt-get install -y \
    cups \
    printer-driver-all \
    cups-pdf \
    && rm -rf /var/lib/apt/lists/* && \
    service cups start && \
    cupsctl --remote-admin --remote-any --share-printers && \
    service cups restart

COPY requirements.txt /requirements.txt
RUN pip install -r /requirements.txt

COPY src/ /app
WORKDIR /app

EXPOSE 5000/tcp
EXPOSE 631
CMD ["python", "app.py"]

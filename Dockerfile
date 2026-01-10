FROM python:3.11-slim

WORKDIR /usr/src/app


COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt


COPY templates/ ./templates/
COPY static/ ./static/
COPY app.py ./


RUN useradd -m capstone
USER capstone

EXPOSE 5000

CMD ["gunicorn", "--worker-class", "gevent", "--timeout", "120", "--bind", "0.0.0.0:5000", "app:app"]
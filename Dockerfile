FROM python:3.9-alpine

WORKDIR /srv

COPY requirements.txt /srv
RUN python -m pip install -r requirements.txt

CMD ["python", "-OO", "main.py"]
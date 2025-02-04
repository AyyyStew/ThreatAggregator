
FROM python:3.13.1-slim

WORKDIR /code

COPY ./requirements.txt /code/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

COPY ./app /code/app

# Set up a volume for persistent storage
VOLUME ["/code/app/data"]

WORKDIR /code/app

CMD ["fastapi", "run", "main.py", "--port", "80"]
FROM python:3.11.2

WORKDIR /code

COPY ./requirements.txt /code/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

COPY ./.env.prod /code/.env.prod

COPY ./src /code/src

EXPOSE 80
CMD ["ENV=prod", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "80"]
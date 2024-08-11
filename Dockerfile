FROM python:3.12.5-bookworm

WORKDIR /qseer

COPY ./requirements.txt ./requirements.txt

RUN pip install --no-cache-dir --upgrade -r ./requirements.txt

COPY ./app ./app

CMD ["fastapi", "run", "app", "--port", "8000"]
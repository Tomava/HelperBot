FROM python:3.14

# Uncomment everything below if not running rootless Docker

# RUN useradd -u 1000 discord
# RUN mkdir /home/discord
# RUN chown -R discord /home/discord

#USER discord

WORKDIR /app

COPY .env ./
COPY *.py ./
COPY requirements.txt ./

RUN pip3.14 install -r requirements.txt

CMD ["python3", "HelperBot.py"]

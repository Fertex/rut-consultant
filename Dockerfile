# Base on docker image https://nander.cc/using-selenium-within-a-docker-container
FROM python:3.7
LABEL name="Api with selenium" \
	version="1.0" 

WORKDIR /usr/app

COPY . .

RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add -
RUN sh -c 'echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list'

# Install deps + add Chrome Stable
RUN apt-get -y update \
	&& apt-get install -y \
	google-chrome-stable \
	unzip 

RUN wget -O /tmp/chromedriver.zip http://chromedriver.storage.googleapis.com/87.0.4280.20/chromedriver_linux64.zip \
	&& unzip /tmp/chromedriver.zip chromedriver -d /usr/local/bin/

RUN apt-get install -y apt-utils && apt-get -y install libzbar0

RUN pip install --upgrade pip \
	&& pip install -r requirements.txt

# Add python user
RUN addgroup --gid 1024 pyuser \
	&& adduser --disabled-password --gecos "" --force-badname --gid 1024 pyuser \
	&& chown -R pyuser /usr/app/ 
USER pyuser

# Expose port 4000
EXPOSE 4000

# Autorun app
CMD [ "python", "./src/app.py"]

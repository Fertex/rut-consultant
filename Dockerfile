# Base on docker image Justin Ribeiro <justin@justinribeiro.com>
FROM debian:buster-slim
LABEL name="Api with selenium" \
	version="1.0" 

WORKDIR /usr/app

COPY . .

# Install deps + add Chrome Stable + purge all the things
RUN apt-get update && apt-get install -y \
	python3.7 \
	python3-pip \
	python3-setuptools \
	apt-transport-https \
	ca-certificates \
	curl \
	gnupg \
	--no-install-recommends \
	&& curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py \
	&& curl -sSL https://dl.google.com/linux/linux_signing_key.pub | apt-key add - \
	&& echo "deb https://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list \
	&& apt-get update && apt-get install -y \
	google-chrome-beta \
	fontconfig \
	fonts-ipafont-gothic \
	fonts-wqy-zenhei \
	fonts-thai-tlwg \
	fonts-kacst \
	fonts-symbola \
	fonts-noto \
	fonts-freefont-ttf \
	--no-install-recommends \
	&& apt-get purge --auto-remove -y curl gnupg \
	&& rm -rf /var/lib/apt/lists/* 

RUN pip3 install --upgrade pip \
	&& pip3 install -r requirements.txt

# Add Chrome as a user
RUN groupadd -r chrome && useradd -r -g chrome -G audio,video chrome \
	&& mkdir -p /home/chrome && chown -R chrome:chrome /home/chrome \
	&& mkdir -p /opt/google/chrome-beta && chown -R chrome:chrome /opt/google/chrome-beta

# Add python user
RUN addgroup --gid 1024 pyuser \
	&& adduser --disabled-password --gecos "" --force-badname --gid 1024 pyuser 
USER pyuser

# Expose port 80
EXPOSE 80

# Autorun app
CMD [ "python3", "./src/app.py"]
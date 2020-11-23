# Base on docker image Justin Ribeiro <justin@justinribeiro.com>
FROM debian:buster-slim
LABEL name="Api with selenium" \
	version="1.0" 

WORKDIR /src

COPY . .

# Install deps + add Chrome Stable + purge all the things
RUN apt-get update && apt-get install -y \
	apt-get install python \
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

RUN python get-pip.py \
	&& pip install -r requirements.txt

# Add Chrome as a user
RUN groupadd -r chrome && useradd -r -g chrome -G audio,video chrome \
	&& mkdir -p /home/chrome && chown -R chrome:chrome /home/chrome \
	&& mkdir -p /opt/google/chrome-beta && chown -R chrome:chrome /opt/google/chrome-beta
# Run Chrome non-privileged
USER chrome

# Expose port 4000
EXPOSE 4000

# Autorun app
CMD [ "python", "app.py"]
FROM python:3.7.11

ARG PORT_NUMBER
ARG DATA_PATH
ARG LOG_PATH
ARG STATE_PATH
ARG EXTERNAL_URL

# Add the script to the Docker Image
ADD scripts/harvester.sh /root/harvester.sh
# Copy the shell script to the container
ADD scripts/start.sh /start.sh
# Set execute permissions on the shell script
RUN chmod +x /start.sh
# Give execution rights on the cron scripts
RUN chmod 0644 /root/harvester.sh

RUN apt-get update && \
    apt-get install -y libjs-jquery libjs-autosize cron && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*


# Setup cronjob
RUN crontab -l | { cat; echo "* * * * * bash /root/harvester.sh"; } | crontab -
RUN cron

RUN touch /var/log/cron.log && \
    chmod 666 /var/log/cron.log && \
    ln -sf /dev/stdout /var/log/cron.log

WORKDIR /app

COPY ./setup.py ./deps.txt /app/
COPY ./meresco /app/meresco
COPY ./usr-share/controlpanel /usr/share/meresco-harvester/controlpanel/

RUN pip install -r deps.txt
RUN python setup.py install

CMD ["/start.sh"]
EXPOSE 8888
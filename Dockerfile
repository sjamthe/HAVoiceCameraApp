ARG BUILD_FROM
FROM $BUILD_FROM

# Install Python and dependencies
RUN apk add --no-cache \
    python3 \
    py3-pip \
    py3-numpy

# Install Python packages with --break-system-packages flag
RUN pip3 install --no-cache-dir --break-system-packages \
    aiohttp==3.9.3

# Copy application files
COPY run.sh /
COPY voice_camera_assistant.py /

RUN chmod a+x /run.sh

CMD [ "/run.sh" ]

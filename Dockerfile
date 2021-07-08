FROM fedora:33

RUN dnf install -y \
    python3 \
    python3-pip \
    && dnf clean all

COPY ./ /app

WORKDIR /app

RUN pip3 install -r req.txt

CMD ["/usr/bin/python3.9", "/app/app.py"]
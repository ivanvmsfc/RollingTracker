FROM python:3.10

COPY requirements.txt /tmp/

# Install necessary packages
RUN apt-get update && apt-get -y install libc-dev gcc libpq-dev

# Upgrade pip
RUN pip install --upgrade pip

# Create a virtual environment
RUN python -m venv /opt/venv

# Install dependencies in the virtual environment
RUN /opt/venv/bin/pip install -r /tmp/requirements.txt

# Set environment variables for the virtual environment
ENV VIRTUAL_ENV=/opt/venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

WORKDIR /code
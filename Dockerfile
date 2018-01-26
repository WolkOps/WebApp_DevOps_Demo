# SOS
#
# Version       latest
FROM library/python:2.7.9
LABEL maintainer "mo.maldonado@gmail.com"

# Adding all files.
ADD requirements.txt /home/python/
ADD app.py /home/python/
ADD templates/ /home/python/templates/
ADD static/ /home/python/static/

# Installing all requirements
RUN pip install -q --upgrade pip
RUN pip install -q -r /home/python/requirements.txt
RUN mkdir -p /var/lib/sqlite

# Expose Volume
VOLUME ['/var/lib/sqlite']

# Exposing port 80
EXPOSE 80

# Entry point
WORKDIR /home/python
ENTRYPOINT ["python", "app.py"]
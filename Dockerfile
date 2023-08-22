FROM python:3.9.5

# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE=1

# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED=1
 
WORKDIR /porepy
COPY . /porepy

RUN apt-get update
# Install missing packages
RUN apt-get install -y wget vim bzip2 git libglu1-mesa libxrender1 libxcursor1 libxft2 libxinerama1 ffmpeg libgl1-mesa-glx libsm6 libxext6

# Update pip
RUN pip install --upgrade pip

# Install dependencies
RUN pip install -r ./requirements.txt
RUN pip install -r ./requirements-dev.txt
RUN pip install mkl==2023.0.0
RUN pip install psutil

# Install PorePy
RUN pip install -e .

CMD ["/bin/bash","-i"]
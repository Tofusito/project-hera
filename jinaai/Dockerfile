FROM jinaai/jina:3-py38-perf

# make sure the files are copied into the image
COPY . /executor_root/

WORKDIR /executor_root

RUN pip install -r requirements.txt

ENTRYPOINT ["jina", "executor", "--uses", "config.yml"]
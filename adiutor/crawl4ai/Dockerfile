ARG LAMBDA_TASK_ROOT="/var/task"

# Use the official Playwright Docker image as the base image
FROM mcr.microsoft.com/playwright/python:v1.41.0-jammy AS build-image

# Re-declare ARG so it's available in this stage
ARG LAMBDA_TASK_ROOT
RUN mkdir -p ${LAMBDA_TASK_ROOT}
WORKDIR ${LAMBDA_TASK_ROOT}

# Install aws-lambda-cpp build dependencies
RUN apt-get update && apt-get install -y g++ make cmake unzip libcurl4-openssl-dev

# Install the runtime interface client
RUN pip install --target ${LAMBDA_TASK_ROOT} awslambdaric

# ==== MULTI STAGE BUILD ====

# Use multi-stage build, to keep the final image cleaner
FROM mcr.microsoft.com/playwright/python:v1.41.0-jammy

# Re-declare ARG so it's available in this stage
ARG LAMBDA_TASK_ROOT
WORKDIR ${LAMBDA_TASK_ROOT}

# Copy in the build image dependencies
COPY --from=build-image ${LAMBDA_TASK_ROOT} ${LAMBDA_TASK_ROOT}

# Copy requirements.txt
COPY requirements.txt ${LAMBDA_TASK_ROOT}

# Install the specified packages
RUN pip install -r requirements.txt

RUN mkdir ${LAMBDA_TASK_ROOT}/src
COPY src/app.py ${LAMBDA_TASK_ROOT}/src
COPY src/__init__.py ${LAMBDA_TASK_ROOT}/src

ENV CRAWL4_AI_BASE_DIRECTORY=/tmp
RUN playwright install chromium


# Set the entry point
ENTRYPOINT [ "/usr/bin/python", "-m", "awslambdaric" ]
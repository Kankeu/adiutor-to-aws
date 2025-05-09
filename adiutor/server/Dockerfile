FROM public.ecr.aws/lambda/python:3.12

# Copy requirements.txt
COPY requirements.txt ${LAMBDA_TASK_ROOT}

# Install the specified packages
RUN pip install -r requirements.txt

# Copy all files in ./src
RUN mkdir ${LAMBDA_TASK_ROOT}/src
COPY src/app.py ${LAMBDA_TASK_ROOT}/src
COPY src/__init__.py ${LAMBDA_TASK_ROOT}/src
COPY src/llm ${LAMBDA_TASK_ROOT}/src/llm
COPY src/utils ${LAMBDA_TASK_ROOT}/src/utils
COPY src/database ${LAMBDA_TASK_ROOT}/src/database
COPY src/web_search ${LAMBDA_TASK_ROOT}/src/web_search

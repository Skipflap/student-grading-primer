FROM python:3.11-slim
WORKDIR /check
RUN pip install requests psycopg2-binary
COPY sanity_check.py autotest.py run_tests.sh ./
RUN chmod +x run_tests.sh
CMD ["./run_tests.sh"]

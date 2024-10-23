FROM apache/airflow:2.9.3
COPY requirements.txt /
RUN pip install --upgrade pip
RUN pip install xgboost
RUN pip install scikit-learn
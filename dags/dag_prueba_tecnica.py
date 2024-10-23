from datetime import datetime
import pandas as pd
import numpy as np

import pickle
import xgboost as xgb

from airflow.models import DAG
from airflow.operators.empty import EmptyOperator
from airflow.operators.python import PythonOperator

from airflow.providers.postgres.hooks.postgres import PostgresHook

from sklearn.preprocessing import MinMaxScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score, accuracy_score


default_args = {
    'owner': 'miguel_guimarey',
    'retries': 5,
    'start_date': datetime(2024, 8, 7, 14, 11, 0)
}

pg_hook = PostgresHook(
        postgres_conn_id='postgres_localhost',
        schema='airflow'
    )

def ingestaDatos(**context):
    # Leemos los datos del csv   
    df = pd.read_csv('/opt/airflow/dags/dataset.csv', delimiter=';').to_json(orient='records')
    print('Se lee el dataset de datos')
    ti = context['task_instance']
    # Guardamos en el contexto el datafreame extraido del csv
    ti.xcom_push(key='DataFrame', value=df)

def limpiezaDatos(**context):
    ti = context['task_instance']
    # Recuperamos del contexto el dataframe y hacemos la conversión de json a dataframe
    data = ti.xcom_pull(key="DataFrame", task_ids="ingesta")
    df = pd.read_json(data, orient='records')
    # Eliminamos columnas no necesarias para el análisis
    df = df.drop(['Customer_ID'], axis=1)
    # Añadimos columnas extras para aumentar la capacidad de análisis de los datos
    # Añadimos una columna que indique si un usuario es padre en base a las columnas kids
    df['isParent'] = np.where(np.logical_or(np.logical_or(np.logical_or(df['kid0_2']=='Y',df['kid3_5']=='Y'), np.logical_or(df['kid6_10']=='Y',df['kid11_15']=='Y')), df['kid16_17']=='Y'), 1, 0)

    # Corregimos el formato de los números en las tablas
    df = df.replace(',', '.', regex=True)
    df = df.fillna(0)

    # Seleccionamos las columnas con valores no numericos
    # y procedemos a cambiar su valor por un número que indique su frecuencia de aparición
    cat_col =['area', 'new_cell', 'crclscod', 'asl_flag', 'prizm_social_one', 'dualband', 'refurb_new', 'hnd_webcap', 'ownrent', 'dwlltype', 'marital', 'infobase', 'HHstatin', 'dwllsize', 'ethnic', 'kid0_2', 'kid3_5', 'kid6_10', 'kid11_15', 'kid16_17', 'creditcd']
    for cat in cat_col:
        df[cat] = df.groupby(cat)[cat].transform('count')
    
    # Normalizamos los datos numéricos
    escala = MinMaxScaler(feature_range=(0,1))
    normado = escala.fit_transform(df)
    df_normado = pd.DataFrame(data=normado, columns=df.columns)
    
    # Guardamos en base de datos el dataframe
    df_normado.to_sql('customers', pg_hook.get_sqlalchemy_engine(), if_exists='replace')


def entrenamientoDatos(**context):
    df_normado =  pd.read_sql('customers', pg_hook.get_sqlalchemy_engine()) 
    print('Entrenamos el modelo')
    # Seleccionamos la variable dependiente y preparamos el conjunto de datos de prueba
    X= df_normado.drop("churn", axis=1)
    # Resto de columnas para preveer la variable dependiente
    y=df_normado["churn"]
    # Variables que generaremos para el entrenamiento
    X_entrena, X_prueba, y_entrena, y_prueba = train_test_split(X,y,train_size=0.75, random_state=50)
    # Dividimos los datos restantes en datos de validación y prueba
    X_validacion, X_prueba, y_validacion, y_prueba = train_test_split(X_prueba,y_prueba,train_size=0.75, random_state=50)
    # Configuramos el modelo de entrenamiento y lo entrenamos con los datos generados
    xgb_model = xgb.XGBClassifier(objective="binary:logistic", random_state=42, eval_metric="auc")
    xgb_model.fit(X_entrena, y_entrena, eval_set=[(X_prueba, y_prueba)])
   
    # Guardamos el modelo en un pickle
    model_xgb = open("modelo_xgb", "wb")
    pickle.dump(xgb_model, model_xgb)
    #Cerramos el archivo Binario
    model_xgb.close()

    #Evaluamos el modelo
    y_validacion_pred = xgb_model.predict(X_validacion)
    y_prueba_pred = xgb_model.predict(X_prueba)
    print("\nAUC Train: {:.4f}\nAUC Valid: {:.4f}".format(roc_auc_score(y_validacion, y_validacion_pred),roc_auc_score(y_prueba, y_prueba_pred)))
    print("\nAccuracy: {:.4f}".format(accuracy_score(y_validacion, y_validacion_pred)))




with DAG('dag_prueba_tecnica',
         default_args=default_args,
         schedule_interval='@daily') as dag:
    start = EmptyOperator(task_id='start')

    ingesta = PythonOperator(task_id='ingesta',
                                   python_callable=ingestaDatos,
                                   provide_context=True)
    limpieza = PythonOperator(task_id='limpieza',
                                   python_callable=limpiezaDatos,
                                   provide_context=True)
    entrenamiento = PythonOperator(task_id='entrenamiento',
                                   python_callable=entrenamientoDatos,
                                   provide_context=True)


start >> ingesta >> limpieza >> entrenamiento
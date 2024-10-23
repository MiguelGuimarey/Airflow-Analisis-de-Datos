<h1>Data Analysis Project with Apache Airflow</h1>
<div><p>This project consisted of 4 phases:</p></div>
  <div>
    <ul>
      <li><strong>Analysis:</strong> Phase in which the relevant ETL operations are performed on the dataset. </li>
        <ul>
          <li>The learning algorithm used is XGBoost</li>
          <li>The cleaning used consisted of comma elimination by dots and data normalisation.</li>
          <li>Columns with non-numeric values were replaced by their frequency of occurrence within the document.</li>
          <li>"Customer_ID" column was removed as it did not add value to the data analysis.</li>
          <li>Added "isParent" column reflecting a binary value in case the client has children or not.</li>
        </ul> 
      <li><strong>Deployment: Phase in which the ETL process was divided into three different dags and deployed using Docker.</strong> </li>
      <li><strong>Bonus Points: Phase in which improvements to deployment were added</strong> </li>
        <ul>
          <li>Addition of a database in PostgresSQL that would store the future dataset.</li>
        </ul> 
        <ul>
          <li>Addition of monitoring applications with Statsd, Prometheus and Grafana to display it.</li>
        </ul>
    </ul>
  </div>

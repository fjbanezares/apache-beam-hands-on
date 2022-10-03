
```shell
python --version
pip --version
pip install --upgrade pip
# create a Virtual environment
python -m venv environment
. environment/activate
pip install apache-beam
pip install 'apache-beam[gcp]'
```

With the following execution we use the Beam DirectRunner to word count this file and output in the output folder within a file called contador, Beam will add a sufix -0000-of-0001.
```shell
python -m apache_beam.examples.wordcount \
--input README.md \
--output output/contador
```

Now we run the same example, but using Spark.
```shell
python -m apache_beam.examples.wordcount \
--input README.md \
--output output/contador \
--runner SparkRunner
```

Take into account that Spark uses Scala and Java under the hood, Beam has some local Spark Runner with version 2.4 as you can see below it launches Spark with 4 threads to simulate a parallelization ot 4.

```shell
.apache_beam/cache/jars/beam-runners-spark-job-server-2.41.0.jar' 
'--spark-master-url' 'local[4]' 
'--artifacts-dir' '/var/folders/fq/bp19g0v965gfsz0z0cpgl43m0000gn/T/beam-temp77zlr7xm/artifactsljqywi6f' 
'--job-port' '61345' 
'--artifact-port' '0'
'--expansion-port' '0']
```
It can happen that if you have Java 11 installed you get some error
*ERROR:root:java.lang.IllegalArgumentException: Unsupported class file major version 55*

To solve this make sure Java 8 is the active version to be compatible with Spark 2.4.

```shell
export JAVA_HOME=$(/usr/libexec/java_home -v 1.8)
java --version
```

### Use Google

Dataflow is about unifying frameworks and make life easier, but as always this means have to suffer a little at the beginning with the specifics.

You can see that as of 2022 Dataflow has 9 different runners and each one has its characteristics.

Now let's set up what we need to use Google Dataproc where the runner uploads your executable code and dependencies to a **Google Cloud Storage bucket** and creates a Cloud Dataflow job.
It is very handy as Google takes care of all the autoscaling but we have to make sure the buckets are there and so on...
```shell
your_account=XXX
gcloud config set account $your-account
gcloud auth login $your-account
gcloud projects list
PROJECT_ID=ufv-javi-beam-dataflow
gcloud projects list
gcloud projects create $PROJECT_ID
gcloud config set project $PROJECT_ID
```

##### Enable billing
```shell
gcloud alpha billing accounts list
BILLING_ACCOUNT=`gcloud alpha billing accounts list | grep True | awk '{print $1}' `
# check we have it
echo $BILLING_ACCOUNT 
# enable
gcloud alpha billing projects link $PROJECT_ID --billing-account $BILLING_ACCOUNT
```

Enable the Dataflow, Compute Engine, Cloud Logging, Cloud Storage, Google Cloud Storage JSON, BigQuery, Cloud Pub/Sub, Cloud Datastore, and Cloud Resource Manager APIs
```shell
gcloud services enable dataflow compute_component logging storage_component storage_api bigquery pubsub datastore.googleapis.com cloudresourcemanager.googleapis.com
```

Create authentication credentials for your Google Account: As a developer, I want my code to interact with GCP via SDK.
```shell
gcloud auth application-default login

```

Grant roles to your Google Account. Run the following command once for each of the following IAM roles: roles/iam.serviceAccountUser
```shell
gcloud beta iam roles list --project=$PROJECT_ID 

gcloud projects add-iam-policy-binding $PROJECT_ID \
--member="user:`echo $your-account`" \
--role=roles/iam.serviceAccountUser
```

```shell
gsutil mb -c STANDARD -l US gs://$PROJECT_ID
gcloud alpha storage ls
BUCKET_NAME=gs://$PROJECT_ID
gcloud alpha storage cp README.md $BUCKET_NAME
gsutil ls $BUCKET_NAME
```

Grant roles to your Compute Engine default service account.
Run the following command once for each of the following IAM roles: 
* roles/dataflow.admin
* roles/dataflow.worker
* roles/storage.objectAdmin

```shell
gcloud alpha projects describe $PROJECT_ID 
PROJECT_NUMBER=`gcloud alpha projects describe $PROJECT_ID | grep projectNumber | awk -F ':' '{print $2}'`
# We need to extract the number, let me correct:
PROJECT_NUMBER=`gcloud alpha projects describe $PROJECT_ID | grep projectNumber | awk -F ':' '{print $2}' | awk -F'[^0-9]*' '{print $2}'`

gcloud projects add-iam-policy-binding $PROJECT_ID \
--member="serviceAccount:`echo $PROJECT_NUMBER`-compute@developer.gserviceaccount.com" 
--role=SERVICE_ACCOUNT_ROLE

gcloud projects add-iam-policy-binding $PROJECT_ID \
--member="serviceAccount:`echo $PROJECT_NUMBER`-compute@developer.gserviceaccount.com" \
--role=roles/dataflow.admin

gcloud projects add-iam-policy-binding $PROJECT_ID \
--member="serviceAccount:`echo $PROJECT_NUMBER`-compute@developer.gserviceaccount.com" \
--role=roles/dataflow.worker

gcloud projects add-iam-policy-binding $PROJECT_ID \
--member="serviceAccount:`echo $PROJECT_NUMBER`-compute@developer.gserviceaccount.com" \
--role=roles/storage.objectAdmin
```

```shell
python -m apache_beam.examples.wordcount \
    --region US \
    --input $BUCKET_NAME/README.md \
    --output $BUCKET_NAME/results/outputs \
    --runner DataflowRunner \
    --project $PROJECT_ID \
    --temp_location $BUCKET_NAME/tmp
```

```shell
# As part of the initial setup, install Google Cloud Platform specific extra components. Make sure you
# complete the setup steps at /documentation/runners/dataflow/#setup
GOOGLE-ZONE:
GOOGLE-PROJECT:

pip install apache-beam[gcp]
python -m apache_beam.examples.wordcount --input gs://dataflow-samples/shakespeare/kinglear.txt \
                                         --output gs://<your-gcs-bucket>/counts \
                                         --runner DataflowRunner \
                                         --project $PROJECT \
                                         --region $REGION \
                                         --temp_location gs://<your-gcs-bucket>/tmp/
```


### Deletion of the GCP projectgcloud auth revoke <your_account>

```shell

gcloud projects delete $PROJECT_ID
```
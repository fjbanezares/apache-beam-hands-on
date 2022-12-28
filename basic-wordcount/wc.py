from apache_beam.options.pipeline_options import PipelineOptions

input_file = 'gs://dataflow-samples/shakespeare/kinglear.txt'
output_path = 'gs://my-bucket/counts.txt'

beam_options = PipelineOptions(
    runner='DataflowRunner',
    project='my-project-id',
    job_name='unique-job-name',
    temp_location='gs://my-bucket/temp',
)
import json
import boto3

def lambda_handler(event, context):
    # TODO implement
    s3 = boto3.client('s3')
    if event:
        fileobj = event["Records"][0]
        audio_file_name = str(fileobj['s3']['object']['key'])
        print ("Filename ",audio_file_name)
        
        transcribe = boto3.client('transcribe')
        output_bucket_name = "video-translation-output"
        
        job_name = str(audio_file_name.split('.')[0])
        original_language_code = job_name.rsplit('__', 2)[-2]
        
        print ("Job Name: ",job_name)
        print ("original_language_code: ",original_language_code)
        
        job_uri = "https://s3.amazonaws.com/video-translation/"+audio_file_name
       
        
        transcribe.start_transcription_job(
        TranscriptionJobName=job_name,
        Media={'MediaFileUri': job_uri},
        MediaFormat='wav',
        LanguageCode=original_language_code,
        OutputBucketName=output_bucket_name
        )
        
        
    return {
        "statusCode": 200,
        "body": json.dumps('Hello from S3-trigger-transcription!')
    }

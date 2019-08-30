import json
import boto3
import pysrt
from datetime import datetime, timedelta
import os

s3 = boto3.client('s3')
translate = boto3.client(service_name='translate')
bucket_name_original_srt = "video-translation-output-original-srt"
bucket_name_translated_srt = "video-translation-output-translated-srt"

# time duration threshold to split transcribed text to subtitles. 0.05 is 50 milliseconds
time_duration_threshold = 0.2

# Pass in seconds with millisecond value. Eg: 73.045 and output is in 00:01:13,045 (SRT format)
def format_time(seconds):
    sec = timedelta(seconds=seconds)
    d = datetime(1,1,1) + sec
    s = d.strftime("%H:%M:%S,%f")
    return str(s[:-3])

def translate_text(text,source_language_code,target_language_code):
    if source_language_code == target_language_code:
        return text
    else:
        result = translate.translate_text(Text=text, 
            SourceLanguageCode=source_language_code, TargetLanguageCode=target_language_code)
        return result.get('TranslatedText')

def save_original_and_translated(json_file_name,source_language_code,target_language_code):
    with open(json_file_name) as f:
        data = json.load(f)
    
    Tuple_list=[]
        
    for word in data['results']['items']:
        if word['type'] != 'punctuation':
            current_word = str(word['alternatives'][0]['content'])
            start_time = float(word['start_time'])
            end_time = float(word['end_time'])
            confidence_value = float(word['alternatives'][0]['confidence'])
            if len(Tuple_list)==0:
                Tuple_list.append([current_word,start_time,end_time])
            else:
                last_item = Tuple_list.pop()
                old_word = last_item[0]
                old_start_time = last_item[1]
                old_end_time = last_item[2]
                old_duration = old_end_time - old_start_time
                
                if (start_time - old_end_time) > time_duration_threshold or old_word.endswith('.') :
                    Tuple_list.append(last_item)
                    Tuple_list.append([current_word,start_time,end_time])
                else:
                    current_word = old_word+' '+current_word
                    start_time = old_start_time
                    Tuple_list.append([current_word,start_time,end_time])
        else:
            last_item = Tuple_list.pop()
            old_word = last_item[0]+str(word['alternatives'][0]['content'])
            old_start_time = last_item[1]
            old_end_time = last_item[2]
            Tuple_list.append([old_word,old_start_time,old_end_time])
                    
    srt_filename_original = json_file_name.replace(".json","_original.srt")
    srt_filename_translated = json_file_name.replace(".json","_translated.srt")
    
    index=1
    with open(srt_filename_original,"w") as f1,open(srt_filename_translated,"w") as f2 :
        for item in Tuple_list:
            start = item[1]
            end = item[2]
            text = item[0]
            # file 1
            f1.write(str(index))
            f1.write("\n")
            f1.write(format_time(start))
            f1.write(' --> '),
            f1.write(format_time(end))
            f1.write("\n")
            f1.write(text)
            f1.write("\n\n")
            # file 2
            f2.write(str(index))
            f2.write("\n")
            f2.write(format_time(start))
            f2.write(' --> '),
            f2.write(format_time(end))
            f2.write("\n")
            translated_text = translate_text(text,source_language_code,target_language_code)
            f2.write(translated_text)
            f2.write("\n\n")
            
            index = index+1
            print(text)
            print(translated_text)
    
    basefilename_original = os.path.basename(srt_filename_original)
    s3.upload_file(srt_filename_original, bucket_name_original_srt, basefilename_original)
    
    print("uploaded original: ",basefilename_original)

    basefilename_translated = os.path.basename(srt_filename_translated)
    s3.upload_file(srt_filename_translated, bucket_name_translated_srt, basefilename_translated)
    
    print("uploaded translated: ",basefilename_translated)

def lambda_handler(event, context):

    fileobj = event["Records"][0]
    json_file_name = str(fileobj['s3']['object']['key'])
    output_file_path = '/tmp/'+json_file_name
    print ("Filename ",json_file_name)
    s3.download_file("video-translation-output",json_file_name, output_file_path)

    base_filename_json = json_file_name.rsplit('.',1)[0]
    language_string = base_filename_json.rsplit("__",2)
    source_language_code = language_string[-2].split('-')[0].lower()
    target_language_code= language_string[-1].lower()
    
    print("source_language_code: ",source_language_code)
    print("target_language_code: ",target_language_code)
    
    # Convert transcribed json to a subtitle (srt) file.
    save_original_and_translated(output_file_path,source_language_code,target_language_code)
    # save_translated(output_file_path)
    
    return {
        "statusCode": 200,
        "body": json.dumps('Hello from Lambda!')
    }

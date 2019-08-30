import json
import os
import stat
import pysrt
from pysrt import srtitem
from datetime import datetime, timedelta
import boto3
from pyssml.AmazonSpeech import AmazonSpeech
import shutil


s3 = boto3.client('s3')
polly = boto3.client("polly")
lambda_tmp_dir = '/tmp' # Lambda fuction can use this directory.
# ffmpeg is stored with this script.
# When executing ffmpeg, execute permission is requierd.
# But Lambda source directory do not have permission to change it.
# So move ffmpeg binary to `/tmp` and add permission.
print ("Files before ",os.listdir(lambda_tmp_dir))

ffmpeg_bin = "{0}/ffmpeg.linux64".format(lambda_tmp_dir)
shutil.copyfile('/var/task/ffmpeg.linux64', ffmpeg_bin)
os.environ['IMAGEIO_FFMPEG_EXE'] = ffmpeg_bin
os.chmod(ffmpeg_bin, os.stat(ffmpeg_bin).st_mode | stat.S_IEXEC)

print ("Files after ",os.listdir(lambda_tmp_dir))

from moviepy.config import change_settings
change_settings({"FFMPEG_BINARY": ffmpeg_bin})


from moviepy.audio.io.AudioFileClip import AudioFileClip



voiceid_list = {
    
    "en" : "Aditi",
    "fr" : "Mathieu",
    "es" : "Miguel",
    "ru" : "Maxim",
    "zh" : "Zhiyu",
    "ja" : "izuki",
    "pt" : "Ricardo",
    "de" : "Marlene",
    "it" : "carla",
    "tr" : "Filiz"
}

from pydub import AudioSegment
AudioSegment.converter = ffmpeg_bin



def get_milli_seconds(timecode):
    return (timecode.hours * 3600000 + timecode.minutes * 60000 \
    + timecode.seconds * 1000 + timecode.milliseconds)



def write_mp3_files(filename_translated,voice_id):
    
    translated_subs = pysrt.open(filename_translated,encoding='utf-8')

    for index,each in enumerate(translated_subs):
        subtitle_index = index+1
        content = each.text
        print (subtitle_index)
        print (content)
        
        time_duration = each.duration
        time_duration_milliseconds = get_milli_seconds(time_duration)
        # Add some buffer to time duration just to accomodate beginning and end
        time_duration_milliseconds = time_duration_milliseconds + 250
        time_duration_string = str(time_duration_milliseconds)+"ms"
        
        s = AmazonSpeech()
        s.max_duration(time_duration_string,content)
        text = s.ssml()
        del s
        
        response = polly.synthesize_speech(
            OutputFormat='mp3',
            Text=text,
            TextType ='ssml',
            VoiceId=voice_id,     
        )

        # Voices https://docs.aws.amazon.com/polly/latest/dg/voicelist.html
        body = response['AudioStream'].read()
        append_string = '__'+str(subtitle_index)+'.mp3'
        mp3filename = filename_translated.replace('.srt',append_string)
        wavfilename = mp3filename.replace('.mp3','.wav')
        
        with open(mp3filename,'wb') as file:
            file.write(body)
            file.close()
            
        translated_wavfilename = AudioFileClip(mp3filename)
        translated_wavfilename.write_audiofile(wavfilename,ffmpeg_params=['-ac','1'])
        
        os.remove(mp3filename)    


def save_voice_muted_audio_file(filename_translated,original_audio):
    translated_subs = pysrt.open(filename_translated,encoding='utf-8')
    for index,each in enumerate(translated_subs):
        subtitle_index = index+1
        content = each.text
        current_start = get_milli_seconds(each.start)
        current_end = get_milli_seconds(each.end)
        previous_end = get_milli_seconds(translated_subs[index-1].end)

        if subtitle_index ==1:
            voice_muted_original_audio = original_audio[:current_start]+ (original_audio[current_start:current_end]-80)
        else:
            voice_muted_original_audio = voice_muted_original_audio + original_audio[previous_end:current_start]+\
                                        (original_audio[current_start:current_end]-80)

    last_end = get_milli_seconds(translated_subs[-1].end)
    voice_muted_original_audio = voice_muted_original_audio +original_audio[last_end:]
    
    return voice_muted_original_audio

def save_final_audio(filename_translated,voice_muted_original_audio,final_audio_name):
    counter = 0
    translated_subs = pysrt.open(filename_translated,encoding='utf-8')
    for index,each in enumerate(translated_subs):
        subtitle_index = index+1
        content = each.text
        current_start = get_milli_seconds(each.start)
        current_end = get_milli_seconds(each.end)
        append_string = '__'+str(subtitle_index)+'.wav'
        wavfilename = filename_translated.replace('.srt',append_string)
        temp = AudioSegment.from_wav(wavfilename)
        start_timecode = current_start - 100
        start_timecode = max(start_timecode,0)
        voice_muted_original_audio = voice_muted_original_audio.overlay(temp,position=start_timecode)
        orig_duration = current_end-current_start
        translated_duration = len(temp)
        difference = abs(translated_duration-orig_duration)
        if (difference > 300):
            print (content)
            counter = counter + 1
        print (content)
        print ("original duration in millisecs: ",orig_duration, 'Translated duration: ',translated_duration,"difference: ",difference, "index ",subtitle_index)

    voice_muted_original_audio.export(final_audio_name, format="wav")

def lambda_handler(event, context):
    fileobj = event["Records"][0]
    srt_file_name = str(fileobj['s3']['object']['key'])
    output_file_path = '/tmp/'+srt_file_name
    print ("Filename ",srt_file_name)
    bucket_name = "video-translation-output-translated-srt" 
    s3.download_file(bucket_name,srt_file_name, output_file_path)

    base_filename_json = srt_file_name.rsplit('.',1)[0]
    language_string = base_filename_json.rsplit("__",2)
    source_language_code = language_string[-2].split('-')[0].lower()
    target_language_code= language_string[-1].lower().split('_')[0]

    voice_id = voiceid_list[target_language_code]
    
    write_mp3_files(output_file_path,voice_id)
    print (" Finished - write_mp3_files")

    audio_file_name = srt_file_name.replace("_translated.srt",".wav")
    audio_output_path = '/tmp/'+audio_file_name
    bucket_name_audio = "video-translation" 
    s3.download_file(bucket_name_audio,audio_file_name, audio_output_path)
    
    original_audio = AudioSegment.from_wav(audio_output_path)
    

    voice_muted_original_audio = save_voice_muted_audio_file(output_file_path,original_audio)
    print (" Finished - save_voice_muted_audio_file")

    final_audio_path =  audio_output_path.replace(".wav","_final.wav")
    save_final_audio(output_file_path,voice_muted_original_audio,final_audio_path)
    print ("Saved original audio")

    print ("Uploading to S3")
    final_audio_bucket = "video-translation-final-audio-output"
    s3.upload_file(final_audio_path, final_audio_bucket, os.path.basename(final_audio_path))
    print ("Finished Uploading to S3")

    
    return {
        "statusCode": 200,
        "body": json.dumps('Hello from Lambda!')
    }

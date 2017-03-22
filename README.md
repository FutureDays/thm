# thm
video post-processing for The History Makers

# makevideos

this script takes the raw video captures delivered by THM personnel and:

1. concatenates the < 4GB files into 1 long file

2. transcodes that file to flv, mp4, and mpeg

3. embeds timecode and watermarks where appropriate

4. hashmoves (see below) them to their destiantions

5. triggers script to embed those hashes into a Filemaker db named PBCore_Catalog 

makevideos also checks to make sure that everything is plugged in and that all necessary files (like watermarks) are in their expected locations.

makevideos is triggered every 15minutes, M-F, 7am-9pm local time by cron

makevideos can also be run manually by cd'ing into the repo directory (look for that in the config.txt file) and running "python makevideos.py"

# hashmove
better file movement

**General Usage**

python hashmove.py [source file or directory full path] [destination parent directory full path] [flags]

**to move a file**

python hashmove.py C:/path/to/file.ext C:/path/to/parent/dir

**to move a directory**

python hashmove.py /home/path/to/dir/a /home/path/to/dir/b

**to copy a file**

python hashmove.py -c C:/path/to/file.ext C:/path/to/parent/dir

**log the transfer**

python hashmove.py -l /home/path/to/dir/a /home/path/to/dir/b

**verify against another hash or set of hashes**

python hashmove.py -v "/home/path to/dir/you question" /home/path/to/dir/with/hashes



##ffmpeg strings
these aren't implemented quite as they are written here, everything in brackets is a variable for example, but if you wanted to make each of these derivatives with ffmpeg, this is what you would use:

**concatenate**

`ffmpeg -f concat -i concat.txt -map 0:v -map 0:a -c:v copy -c:a copy -timecode 00:00:00:00 rawconcat.mov`

**route channel 2 audio out and re-wrap**

`ffmpeg -i rawconcat.mov -map 0:a:1 -map -0:d -map -0:v -c:a copy rawconcat-as2.mov`

`ffmpeg -i rawconcat.mov -i concat-as2.mov -map 0:v -map 0:a:0 -map 1:a:0 -map 0:d -c copy concat.mov`


**flv**

`ffmpeg -i concat.mov -i [/path/to/watermark.png] -filter_complex "scale=320:180,overlay=0:0;[0:a:0][0:a:1]amerge=inputs=2[a]" -c:v libx264 -preset fast -b:v 700k -r 29.97 -pix_fmt yuv420p -c:a aac -ac 2 -map 0:v -map "[a]" -timecode 00:00:00:00 -threads 0 [accessionNumber.flv]`

**mpeg**

`ffmpeg -i concat.mov -target ntsc-dvd -filter_complex "[0:a:0][0:a:1]amerge=inputs=2[a]" -b:v 5000k -vtag xvid -vf "drawtext=fontfile='[/path/to/fontfile.ttf]': timecode='00\:00\:00\:00': r=29.97: x=(w-tw)/2: y=h-(2*lh): fontcolor=white: fontsize=72: box=1: boxcolor=0x00000099,scale=720:480" -map 0:v -map "[a]" -ac 2 -threads 0 [accessionNumber.mpeg]`

**mp4**

`ffmpeg -i concat.mov -c:v mpeg4 -b:v 372k -pix_fmt yuv420p -r 29.97 -vf "drawtext=fontfile='[/path/to/fontfile.ttf]': timecode='00\:00\:00\:00': r=29.97: x=(w-tw)/2: y=h-(2*lh): fontcolor=white: fontsize=72: box=1: boxcolor=0x00000099,scale=420:270" -filter_complex "[0:a:0][0:a:1]amerge=inputs=2[a]" -c:a aac -ar 44100 -ac 2 -map 0:v -map "[a]" -threads 0 [accessionNumber.mp4]`

**test input*

if you want to generate a test input file for this situation here's how.

first, make a video file in the usual way

ffmpeg -f lavfi -i "testsrc=duration=10:size=1920x1080:rate=29.97" -c:v mpeg2video -timecode 00:00:00.0 [vout].mov

then make an audio file and wrap it in a mov

ffmpeg -f lavfi -i "sine=frequency=1000:sample_rate=48000:duration=10" -c:a pcm_s24be [aout].mov

then warp the video file with the audio file mapped to two different streams, with timecode track

ffmpeg -i [vout].mov -i [aout].mov -c:v copy -c:a pcm_s24be -map 0:v:0 -map 1:a:0 -map 2:a:0 -timecode 00:00:00:00 [out].mov

import requests
r = requests.post('https://litterbox.catbox.moe/resources/internals/api.php', data={'reqtype': 'fileupload', 'time': '1h'}, files={'fileToUpload': open('core/audio/my_voice.wav', 'rb')})
print(r.text)

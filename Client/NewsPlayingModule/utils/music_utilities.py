import os
from pygame import mixer
mixer.init()

class MusicUtilites:

    news_channel = mixer.Channel(0)
    news_playing = False

    music_channel = mixer.Channel(1)
    music_playing = False

    def start_music(music_folder):

        for file in os.listdir(music_folder):
            assert type(file) == str

            filepath = os.path.join(music_folder, file)
            if not os.path.isfile(filepath):
                continue
            if not (file.endswith(".wav") or file.endswith(".mp3")):
                continue
            print(f"[+] loading into queue the music {filepath}")
            MusicUtilites.music_channel.queue(mixer.Sound(filepath))

        MusicUtilites.music_channel.set_volume(0.15)
        MusicUtilites.music_channel.unpause()
        MusicUtilites.music_playing = True
        

    def play_news(sound_path):
        try:
            MusicUtilites.news_channel.play(mixer.Sound(sound_path))
        except Exception as e:
            print(e)
        MusicUtilites.news_playing = True
        
    def pause_news():
        """
        pauses news
        """
        MusicUtilites.news_channel.pause()
        MusicUtilites.news_playing = False
        
    def unpause_news():
        """
        unpauses news
        """
        MusicUtilites.news_channel.unpause()
        MusicUtilites.news_playing = True
        
    def stop_news():
        """
        stops news
        """
        MusicUtilites.news_channel.stop()
        MusicUtilites.news_playing = False

    def pause_music():
        """
        pauses ambient music
        """
        MusicUtilites.music_channel.pause()
        MusicUtilites.music_playing = False
        
    def unpause_music():
        """
        unpauses music
        """
        MusicUtilites.music_channel.unpause()
        MusicUtilites.music_playing = True
        
    def stop_music():
        """
        stops music
        """
        MusicUtilites.music_channel.stop()
        MusicUtilites.music_playing = False

    def pause_sounds():
        """
        pauses both music and news reproduction
        """
        #print(f"[-] news paused [-]")
        MusicUtilites.news_channel.pause()
        MusicUtilites.news_playing = False
        MusicUtilites.music_channel.pause()
        MusicUtilites.music_playing = False


    def unpause_sounds():
        """
        unpauses both music and news reproduction
        """
        #print(f"[+] news unpause method call [+]")
        MusicUtilites.news_channel.unpause()
        MusicUtilites.news_playing = True
        MusicUtilites.music_channel.unpause()
        MusicUtilites.music_playing = True
        
    def stop_sounds():
        """
        stops both music and news reproduction
        """
        #print(f"[!] news stop method call [!]")
        MusicUtilites.news_channel.stop()
        MusicUtilites.news_playing = False
        MusicUtilites.music_channel.stop()
        MusicUtilites.music_playing = False


    def is_news_playing():
        if MusicUtilites.news_channel.get_busy() == True:
            return MusicUtilites.news_playing
        return False
    
    def is_music_playing():
        if MusicUtilites.music_channel.get_busy() == True:
            return MusicUtilites.music_playing
        return False
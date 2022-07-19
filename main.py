import parselmouth
from parselmouth import praat

import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd

# import pyaudio 
import wave
# audio = pyaudio.PyAudio()
# stream = audio.open(format=pyaudio.paInt16, channels = 1, rate = 44100, input = True, frames_per_buffer = 1024)

def acquire_formants(file_path, speaker_gen = 'f'):
  f1_list, f2_list, f3_list  = [], [], []

  if speaker_gen == 'f': 
      sgen = 5500
  elif speaker_gen == 'm':
      sgen = 5000
  else: 
      sgen = 5250
      
  f0min, f0max  = 75, 300

  sound = parselmouth.Sound.extract_part(parselmouth.Sound(file_path))
  pointProcess = praat.call(sound, "To PointProcess (periodic, cc)", f0min, f0max)
  numPoints = praat.call(pointProcess, "Get number of points")
  
  
  formants = praat.call(sound, "To Formant (burg)", 0, 5, sgen, 0.1, 50)

  for point in range(0, numPoints):
      point += 1
      t = praat.call(pointProcess, "Get time from index", point)
      f1 = praat.call(formants, "Get value at time", 1, t, 'Hertz', 'Linear')
      f2 = praat.call(formants, "Get value at time", 2, t, 'Hertz', 'Linear')
      f3 = praat.call(formants, "Get value at time", 3, t, 'Hertz', 'Linear')
      f1_list.append(f1)
      f2_list.append(f2)
      f3_list.append(f3)
    
  return f1_list, f2_list, f3_list

def get_words(file_speaker, formant_lists): 
    ##using the intensity of the sound, we will find where the words are said, 
   
    snd = parselmouth.Sound(file_speaker)
    intensity = snd.to_intensity(time_step = 0.01)
    int_vals = intensity.values.T
    int_t = intensity.xs()
    
    sensitivity = 0.19
    time_stamps = []
  
    for i in range(len(int_vals)): #going through the decible list 
        
        if int_vals[i] >= 50: #if the sound is loud enough
            t = int_t[i] #retrieve the time stamp 
            time_stamps.append(t) #add time stamp to list 

    # time_stamps = [0.1,0.2,0.3, 5,5.1, 5.4,5.5,5.6, 6.1,6.2,6.3, 'stop']
    time_stamps.append('stop')
    word_list = []
    word = []
    
    for i in range(0, len(time_stamps)): 
        if (time_stamps[i+1] == 'stop'): #if it is the 
            word.append(time_stamps[i])
            word_list.append(word)
            break
        
        elif (time_stamps[i+1] - time_stamps[i] >= sensitivity): #if the diff between a timestamp and the next one is greater than 0.2s, we know silence has occurred
            word.append(time_stamps[i])      
                  
            if (len(word) > 2): #if it's long enough
                word_list.append(word) #append it 
            word = [] #clear the word 
            
        else: 
            word.append(time_stamps[i])
      
    wl=[]      
    for words in word_list: 
        word = [words[0], words[-1]]
        wl.append(word)

    return wl

def get_word_formants(word_list):
    sound = parselmouth.Sound.extract_part(parselmouth.Sound(file_path))
    formants = praat.call(sound, "To Formant (burg)", 0, 5, 5500, 0.01, 50)
    df = pd.DataFrame()

    f1, f2, f3 = [],[],[]
    
    # f1.append(formant_list[0])
    # f2.append(formant_list[1])
    # f3.append(formant_list[2])

    df['f1'] = f1
    df['f2'] = f2
    df['f3'] = f3
    
    for word in word_list: 
        for ts in word: 
            f1 = praat.call(formants, "Get value at time", 1, t, 'Hertz', 'Linear')
            f2 = praat.call(formants, "Get value at time", 2, t, 'Hertz', 'Linear')
            f3 = praat.call(formants, "Get value at time", 3, t, 'Hertz', 'Linear')
    
    return 
        # print(f1,f2,f3)
            

# get_word_formants(word_list)
    
file_path = 'c:/Users/bridg/Documents/GitHub/form-a-formant/vowel_formants.wav'
formants = acquire_formants(file_path)    
 # for trial in word: 
    #     form1 = [f1, f2, f3]
    # word = [forms1, forms2, forms3] 
    
    
def add_formants(formant_list):
    df = pd.DataFrame()

    f1, f2, f3 = [],[],[]
    
    f1.append(formant_list[0])
    f2.append(formant_list[1])
    f3.append(formant_list[2])

    df['f1'] = f1
    df['f2'] = f2
    df['f3'] = f3

    return df
 
 
 
file_path = 'c:/Users/bridg/Documents/GitHub/form-a-formant/vowel_formants.wav'

formants = add_formants(acquire_formants(file_path))

pitches = get_words(file_path, formants)










import parselmouth
from parselmouth import praat

from numpy import array, average
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd

import seaborn as sns
import pandas as pd
import matplotlib.pyplot as plt



# import pyaudio 
import wave
# audio = pyaudio.PyAudio()
# stream = audio.open(format=pyaudio.paInt16, channels = 1, rate = 44100, input = True, frames_per_buffer = 1024)

decible_threshold = 50 #given the nature of the words given, the decible of the /h/ sound and /d/ sounds will be far quieter than the nuclear vowel
silence_tolerance = 0.2
file = '17vowelstest2.wav'

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

def get_words(file_speaker): 
    ##using the intensity of the sound, we will find where the words are said, 
   
    snd = parselmouth.Sound(file_speaker)
    intensity = snd.to_intensity(time_step = 0.01)
    int_vals = intensity.values.T
    int_t = intensity.xs()
    
    
    time_stamps = []
  
    for i in range(len(int_vals)): #going through the decible list 
        
        if int_vals[i] >= decible_threshold: #if the sound is loud enough
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
        
        elif (time_stamps[i+1] - time_stamps[i] >= silence_tolerance): #if the diff between a timestamp and the next one is greater than 0.2s, we know silence has occurred
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
    
    word_dict = {}
    
    f1_list, f2_list, f3_list  = [], [], []
    
    count = 0
    
    for word in word_list: 
        f1_list, f2_list, f3_list  = [], [], []
        count+=1
        sound = parselmouth.Sound.extract_part(parselmouth.Sound(file_path), from_time=word[0], to_time=word[1])
        formants = praat.call(sound, "To Formant (burg)", 0, 5, 5500, 0.01, 50)
        
        f0min, f0max = 75, 300

        pointProcess = praat.call(sound, "To PointProcess (periodic, cc)", f0min, f0max)
        numPoints = praat.call(pointProcess, "Get number of points")
        
        for point in range(0, numPoints):
            point += 1
            t = praat.call(pointProcess, "Get time from index", point)
            f1 = praat.call(formants, "Get value at time", 1, t, 'Hertz', 'Linear')
            f2 = praat.call(formants, "Get value at time", 2, t, 'Hertz', 'Linear')
            f3 = praat.call(formants, "Get value at time", 3, t, 'Hertz', 'Linear')
            
            f1_list.append(f1)
            f2_list.append(f2)
            f3_list.append(f3)
            
        word_dict[count] = [np.array(f1_list[4:-4]), np.array(f2_list[4:-4]), np.array(f3_list[4:-4])]
        # print("analysis", count, "of", len(word_list),"complete!") 
            
    return word_dict

def formant_averager(word_dict):    
    avgs_dict = {}
    count = 0 
    
    # print(word_dict[1][0]) #this is [f1 arr, f2 arr, f3 arr] for first word 
    for i in range(1, len(word_dict)):  #i is the word elicitations 1-51     
        count+=1
        word = word_dict[i]
        
        wf1, wf2, wf3 = word[0], word[1], word[2]
        awf1, awf2, awf3 = average(wf1), average(wf2), average(wf3) 
        
        avgs_dict[count] =[awf1, awf2, awf3]

    sound_avgs = {}
    count = 0
    
    for i in range(1, len(avgs_dict)-1, 3): 
        count+=1        
        sound_avg = np.mean(np.array([avgs_dict[i], avgs_dict[i+1], avgs_dict[i+2]]), axis=0) 
        sound_avgs[count] = sound_avg

    sound_avgs[count+1] = np.mean(np.array([avgs_dict[i-3], avgs_dict[i-2], avgs_dict[i-1]]), axis=0) #just adding the last one instead of fixing oob error lmao   
    return sound_avgs 
    
def plot_vowels(sound_avgs): 
    
    f1_vals,f2_vals = [], []
    for x in sound_avgs: 
        f1_vals.append(sound_avgs[x][0])
        f2_vals.append(sound_avgs[x][1])

    x = np.array(f2_vals)
    y = np.array(f1_vals)
    
    fig = plt.figure()
    ax = fig.add_subplot(1, 1, 1)
    ax.xaxis.set_ticks_position('top')
    
    ax.invert_yaxis()
    ax.invert_xaxis()
    ax.scatter(x, y, linestyle='None')

    plt.xlabel("F2")
    plt.ylabel("F1")
    plt.scatter(x, y)
    vowels = ['i', 'ɪ', 'ɛ', 'æ', 'ɑ', 'ɔ', 'ʌ', 'ʊ', 'u', 'aʊ', 'oj', 'aj', 'ow', 'aj', 'ej', 'ɚ', 'ə'] 

    for i, label in enumerate(vowels):
        plt.annotate(label, (x[i], y[i]))
    plt.show()
    
    
    
            
        
        
    
file_path = 'c:/Users/bridg/Documents/GitHub/form-a-formant/'+file
# formants = acquire_formants(file_path)    
# formants = add_formants(acquire_formants(file_path))

word_list = get_words(file_path)

word_formants = get_word_formants(word_list)

formant_averages = formant_averager(word_formants)

plot_vowels(formant_averages)












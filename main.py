import parselmouth
from parselmouth import praat

from numpy import array, average
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd

## TODO: fix diphthong issue 
## TODO: add internal recording option
## TODO: write readme 
# import pyaudio
import wave
# audio = pyaudio.PyAudio()
# stream = audio.open(format=pyaudio.paInt16, channels = 1, rate = 44100, input = True, frames_per_buffer = 1024)


file = '17vowelstest.wav'
decible_threshold = 50  # given the nature of the words given, the decible of the /h/ sound and /d/ sounds will be far quieter than the nuclear vowel
silence_tolerance = 0.2
#('m', 'w', 'o')
speaker_gen = 'w'

schwa_len = 15
num_reps = 3  # default 3

def acquire_formants(file_path, speaker_gen='w'):
  f1_list, f2_list, f3_list = [], [], []

  if speaker_gen == 'w':
      sgen = 5500
  elif speaker_gen == 'm':
      sgen = 5000
  else:
      sgen = 5250

  f0min, f0max = 75, 300
  sound = parselmouth.Sound.extract_part(parselmouth.Sound(file_path))
  pointProcess = praat.call(
      sound, "To PointProcess (periodic, cc)", f0min, f0max)
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
    intensity = snd.to_intensity(time_step=0.01)
    int_vals = intensity.values.T
    int_t = intensity.xs()
    time_stamps = []

    for i in range(len(int_vals)):  # going through the decible list

        if int_vals[i] >= decible_threshold:  # if the sound is loud enough
            t = int_t[i]  # retrieve the time stamp
            time_stamps.append(t)  # add time stamp to list

    time_stamps.append('stop')
    word_list = []
    word = []

    for i in range(0, len(time_stamps)):
        if (time_stamps[i+1] == 'stop'):  # stops before oob, lists of variable lengths
            word.append(time_stamps[i])
            word_list.append(word)
            break

        # if the diff between a timestamp and the next one is greater than 0.2s, we know silence has occurred
        elif (time_stamps[i+1] - time_stamps[i] >= silence_tolerance):
            word.append(time_stamps[i])

            if (len(word) > 2):  # if it's long enough
                word_list.append(word)  # append it
            word = []  # clear the word

        else:
            word.append(time_stamps[i])

    wl = []
    for words in word_list:
        word = [words[0], words[-1]]
        wl.append(word)
    return wl

def get_word_formants(word_list):
    word_dict = {}
    count = 0

    for word in word_list:
        f1_list, f2_list, f3_list = [], [], []
        count += 1
        sound = parselmouth.Sound.extract_part(
            parselmouth.Sound(file_path), from_time=word[0], to_time=word[1])
        formants = praat.call(sound, "To Formant (burg)", 0, 5, 5500, 0.01, 50)

        f0min, f0max = 75, 300

        pointProcess = praat.call(
            sound, "To PointProcess (periodic, cc)", f0min, f0max)
        numPoints = praat.call(pointProcess, "Get number of points")

        for point in range(0, numPoints):
            point += 1
            t = praat.call(pointProcess, "Get time from index", point)
            f1 = praat.call(formants, "Get value at time",
                            1, t, 'Hertz', 'Linear')
            f2 = praat.call(formants, "Get value at time",
                            2, t, 'Hertz', 'Linear')
            f3 = praat.call(formants, "Get value at time",
                            3, t, 'Hertz', 'Linear')

            f1_list.append(f1)
            f2_list.append(f2)
            f3_list.append(f3)

        word_dict[count] = [np.array(f1_list[4:-4]), np.array(f2_list[4:-4]), np.array(f3_list[4:-4]), np.array(
            f1_list[:schwa_len]), np.array(f2_list[:schwa_len]), np.array(f3_list[:schwa_len])]
        # print("analysis", count, "of", len(word_list), "complete!")

    return word_dict

def formant_averager(word_dict):
    mono_dict = {}
    diph_dict = {}
    shwa_dict = {}
    count = 0

    # print(word_dict[1][0]) #this is [f1 arr, f2 arr, f3 arr] for first word
    #gets averages of monophtongs
    for i in range(1, len(word_dict)):  # i is the word elicitations 1-51
        count += 1
        word = word_dict[i]

        wf1, wf2, wf3, sf1, sf2, sf3 = word[0], word[1], word[2], word[3], word[4], word[5]
        awf1, awf2, awf3 = average(wf1), average(wf2), average(wf3)
        schwaf1, schwaf2, schwaf3 = average(sf1), average(sf2), average(sf3)

        shwa_dict[count] = [schwaf1, schwaf2, schwaf3]
        mono_dict[count] = [awf1, awf2, awf3] #average of 
        diph_dict[count] = [wf1, wf2, wf3] #full track of all three formants 

    sound_avgs = {}
    count = 0

    #only useful for the monophtongs
    # goes in chunks of 3 through the avgs_dict to find the average of the three elicitations, 
    for i in range(1, len(mono_dict)-1, num_reps):
        count += 1
        sound_avg = np.mean(np.array([mono_dict[i], mono_dict[i+1], mono_dict[i+2]]), axis=0)
        sound_avgs[count] = sound_avg
        
    #within sound_avgs, this overwrites vowels 10-16 
    for i in range(10, len(sound_avgs)+1): 
        sound_avgs[i] = diph_dict[i]

    #the last sound in the recording is the schwa, so it needs to be processed
    #schwa just adding the last one instead of fixing oob error lmao
    sound_avgs[count+1] = np.mean(np.array([shwa_dict[i-4], shwa_dict[i-3], shwa_dict[i-2]]), axis=0)

    return sound_avgs

def plot_vowels(sound_avgs): 
    f1_vals, f2_vals, f3_vals = [], [], []
    
    #create x,y for monophthongs 
    for i in range(1, len(sound_avgs)+1):
        f1_vals.append(sound_avgs[i][0])
        f2_vals.append(sound_avgs[i][1])
        f3_vals.append(sound_avgs[i][2])
        
    # monoxf1 = f1_vals[-1:] + f1_vals[:9]    
    # monoxf2 = f2_vals[-1:] + f2_vals[:9]
    # monoxf3 = f3_vals[-1:] + f3_vals[:9]
        
    mx, my, mz = np.array(f2_vals[-1:] + f2_vals[:9], dtype=object), np.array(f1_vals[-1:] + f1_vals[:9], dtype=object), np.array(f3_vals[-1:] + f3_vals[:9], dtype=object)
    dx, dy, dz = np.array(f2_vals[9:16], dtype=object), np.array(f1_vals[9:-1],dtype=object), np.array(f3_vals[9:-1],dtype='object')
     
    print(dy)
    
    # plt.plot(dx,dy)
    # plt.show()
    
    fig = plt.figure()
    ax = fig.add_subplot(1, 1, 1)

    ax.scatter(mx, my, c=mx, cmap='gist_rainbow_r', alpha=0.8)
    
    ax.set_ylabel('F1')
    ax.set_xlabel('F2')
    ax.xaxis.set_ticks_position('top')
    ax.xaxis.set_label_position('top')
    ax.yaxis.set_ticks_position('right')
    ax.yaxis.set_label_position('right')
    ax.invert_yaxis()
    ax.invert_xaxis()
    
    vowels = ['ə', 'i', 'ɪ', 'ɛ', 'æ', 'ɑ', 'ɔ', 'ʌ', 'ʊ', 'u', 'aʊ', 'oj', 'aj', 'ow', 'aj-t', 'ej', 'ɚ']
    
    monos = ['ə', 'i', 'ɪ', 'ɛ', 'æ', 'ɑ', 'ɔ', 'ʌ', 'ʊ', 'u']
    diphs = ['aʊ', 'oj', 'aj', 'ow', 'aj-t', 'ej', 'ɚ']

    # for i in range(len(x)):
    #     print(vowels[i], ":", x[i], y[i])
 

    for i, label in enumerate(monos):
        plt.annotate(label, (mx[i], my[i]))
    plt.show()
    
    return


file_path = 'c:/Users/bridg/Documents/GitHub/form-a-formant/' + file
# formants = acquire_formants(file_path)
# formants = add_formants(acquire_formants(file_path))

word_list = get_words(file_path)

word_formants = get_word_formants(word_list)

formant_averages = formant_averager(word_formants)

vowels = plot_vowels(formant_averages)

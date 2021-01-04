"""Captures x samples.

This script captures x number of samples, to be comited later using commit.py.
Each sample is captured x amount of time, with a x seconds sleep in between.
The sleep is implemented to capture time invariance in the samples.
This script needs elevated privilidges, as it makes use of the lowlevel fatures.
All string keywords are NOT case sensitive.

Arguments:
    Type(str): Argument to select type A or type C(default) samples
    N_samples(int): The amount of samples you will collect (if not provided, you will be prompted)
    ledcolor(str): The color of the LED. Can be Red,Green,Blue,White(default) or UV
    capturetime(int): The time window to capture each sample. Defaults to 300(seconds)
    captureinterval(int): The interval between each picture. Defaults to 3(seconds)


Example:
    $ sudo python3 capture.py

    $ sudo python3 capture.py --n_samples=<number_samples>

    $ sudo python3 capture.py --type=A --ledcolor=UV --n_samples=<number_samples>

    $ sudo python3 capture.py --type=a --ledcolor=uv --n_samples=<number_samples> --capturetime=300 --captureinterval=3
"""


import sys
import os
import argparse

# Update PYTHONPATH
sys.path.append("/usr/src/app/pythonmodules")

from cameracontrol import Camera
from colortable import colortable
from tqdm import tqdm
from datetime import datetime, timedelta

# The directory parameter is not part of the args,
# as changes needs to be reflected in the codebase of ndt-preprocessing
directory = 'raw_images'


def capture_typeA_image(S1, S2, S3, S4, S5):
  """Captures an image with the expected naming format.

  This functon captures an image, and saves it in the folowing naming convention:
  <spot1_concentration>_<spot2_concentration>_<spot3_concentration>_<spot4_concentration>_<spot5_concentration>_<Unixtimestamp>.png

  Arguments:
      S1(str): Spot1 conecntration (e.g 100)
      S2(str): Spot2 concentration (e.g 60)
      S3(str): Spot3 concentration (e.g 60)
      S4(str): Spot4 concentration (e.g 30)
      S5(str): Spot5 concentration (e.g 30)
  """
  basename = '{}/{}_{}_{}_{}_{}'.format(directory, S1, S2, S3, S4, S5)

  if args.bayer:
    camera.capture_bayer_image(basename)
  else:
    camera.capture_image()
    camera.save_stamped_image(basename)


def capture_typeC_image(N, A, P):
  """Captures an image with the expected naming format.
  This functon captures an image, and saves it in the folowing naming convention:
  <Nitrogen_concentration>_<Amonium_concentration>_<Potasium_concentration>_<Unixtimestamp>.png

  Arguments:
      N(str): Nitrogen conecntration (e.g 100)
      A(str): Amonium concentration (e.g 60)
      P(str): Potasium concentration (e.g 60)
  """
  basename = '{}/{}_{}_{}'.format(directory, N, A, P)
  camera.capture_image()
  camera.save_stamped_image(basename)


def capture_typeRGB_image(N, A, P, C):
  """Captures an image with the expected naming format.
  This functon captures an image, and saves it in the folowing naming convention:
  <Nitrogen_concentration>_<Amonium_concentration>_<Potasium_concentration>_<Unixtimestamp>.png

  Arguments:
      N(str): Nitrogen conecntration (e.g 100)
      A(str): Amonium concentration (e.g 60)
      P(str): Potasium concentration (e.g 60)
      C(str): Color of light. One letter code (R, G, B)
  """
  basename = '{}/{}_{}_{}_{}'.format(directory, N, A, P, C)
  camera.capture_image()
  camera.save_stamped_image(basename)


def capture():
  """Captures an image with the expected naming format with cust settings.

  The code will pull its arguments from the argument dictionary, and capture accordingly.
  Before sampling is started, the script will check if the output folder is already populated,
  and prompt the user if files are found.
  """
  captureWindow = arg_dict['capturetime']
  captureInterval = arg_dict['captureinterval']
  N_samples = arg_dict['N_samples']

  camera.cam.shutter_speed = args.shutter_speed[0]
  camera.cam.awb_gains = args.gain

  if args.ledcolor == "uv":
    camera.setlight(colortable["off"], uv=1)
  else:
    camera.setlight(colortable[args.ledcolor])

  # test if folder exist, and is empty.
  if not os.path.exists(directory):
    os.mkdir(directory)
  else:
    if os.listdir(directory):
      answer = input('raw_images is already populated! delete content before capture? (y/n):')
      if answer.lower() == 'y':
        print('Deleting images')

        for the_file in os.listdir(directory):
          file_path = os.path.join(directory, the_file)
          try:
            if os.path.isfile(file_path):
              os.unlink(file_path)
          except Exception as e:
            print(e)
            break

  camera.start_preview(fullscreen=False, window=(400, 0, 400, 400))
  input('Press Enter to start capturing.')

  for j in range(N_samples):
    correct = False

    S1 = S2 = S3 = S4 = S5 = 0

    for i in tqdm(range(int(captureWindow / captureInterval))):
      try:
        now = datetime.now()
        capture_typeA_image(S1, S2, S3, S4, S5)
        while datetime.now() < now + timedelta(seconds=captureInterval):
          pass
      except KeyboardInterrupt:
        print("\nKeyboard interupt, process is shutting down.\n")
        LEDoff()
        camera.stop_preview()
        sys.exit(1)

  LEDoff()
  camera.stop_preview()
  print("Program ended ok")


def capture_rgb():
  """Captures a sequence of images alternating red, green and blue lights.
  """
  # test if folder exist, and is empty.
  if not os.path.exists(directory):
    os.mkdir(directory)
  else:
    if os.listdir(directory):
      answer = input('raw_images is already populated! delete content before capture? (y/n):')
      if answer.lower() == 'y':
        print('Deleting images')

        for the_file in os.listdir(directory):
          file_path = os.path.join(directory, the_file)
          try:
            if os.path.isfile(file_path):
              os.unlink(file_path)
          except Exception as e:
            print(e)
            break

  # ask for the values of each sample and preview
  for j in range(N_samples):
    camera.start_preview(fullscreen=False, window=(400, 0, 400, 400))
    print("\nsample number {}".format(j + 1))
    inputs_not_accepted = True
    while inputs_not_accepted:
      try:
        N = int(input('Input Nitrate: '))
        A = int(input('Input Ammonium: '))
        P = int(input('Input Phosphate: '))

        # accept inputs if all could be casted to int
        inputs_not_accepted = False

      except KeyboardInterrupt:
        print('\nInturrupted, exiting')
        LEDoff()
        camera.stop_preview()
        sys.exit(1)
      except Exception:
        print('Some inputs where not a number. Please try again')

    # run the lights and change a variable according to the light
    for i in tqdm(range(int(3 / 1))):
      try:
        now = datetime.now()
        # run the lights and change a variable according to the light

        camera.setlight(colortable['green'])
        basename = '{}/{}_{}_{}_G'.format(directory, N, A, P)
        camera.capture(basename, range(60), wait_first=True, bayer=args.bayer)
        # C = "G"
        # for i in range(60):
        #     capture_typeRGB_image(N, A, P, C)
        camera.setlight(colortable['off'])

        camera.setlight(colortable['red'])
        basename = '{}/{}_{}_{}_R'.format(directory, N, A, P)
        camera.capture(basename, range(60), wait_first=True, bayer=args.bayer)
        # C = "R"
        # for i in range(60):
        #     capture_typeRGB_image(N, A, P, C)
        camera.setlight(colortable['off'])

        '''
        camera.setlight(colortable['blue'])
        basename = '{}/{}_{}_{}_B'.format(directory, N, A, P)
        camera.capture(basename, range(60), wait_first=True)
        #C = "B"
        #for i in range(10):
        #    capture_typeRGB_image(N, A, P, C)
        camera.setlight(colortable['off'])
        '''

        while datetime.now() < now + timedelta(seconds=1):
          pass
      except KeyboardInterrupt:
        print("\nKeyboard interupt, process is shutting down.\n")
        LEDoff()
        camera.stop_preview()
        sys.exit(1)


def capture_white(type):
  # test if folder exist, and is empty.
  if not os.path.exists(directory):
    os.mkdir(directory)
  else:
    if os.listdir(directory):
      answer = input('raw_images is already populated! delete content before capture? (y/n):')
      if answer.lower() == 'y':
        print('Deleting images')

        for the_file in os.listdir(directory):
          file_path = os.path.join(directory, the_file)
          try:
            if os.path.isfile(file_path):
              os.unlink(file_path)
          except Exception as e:
            print(e)
            break

  # ask for the values of each sample and preview
  for j in range(N_samples):
    camera.start_preview(fullscreen=False, window=(400, 0, 400, 400))
    print("\nsample number {}".format(j + 1))
    inputs_not_accepted = True
    while inputs_not_accepted:
      try:
        S1 = 0
        S2 = int(input('Input spot2 (pH): ')) if type == "pH" else 0
        S3 = int(input('Input spot3 (K): ')) if type == "K" else 0
        S4 = 0
        S5 = 0

        # accept inputs if all could be casted to int
        inputs_not_accepted = False

      except KeyboardInterrupt:
        print('\nInturrupted, exiting')
        LEDoff()
        camera.stop_preview()
        sys.exit(1)
      except Exception:
        print('Some inputs where not a number. Please try again')

    # capture images with white light
    try:
      now = datetime.now()

      if type == "pH":
        camera.cam.shutter_speed = 1000
        camera.cam.awb_gains = (1.0, 1.2)
      elif type == "K":
        camera.cam.shutter_speed = 500
        camera.cam.awb_gains = (1.0, 1.2)
      else:
        raise Exception("Type must be either pH or K")

      camera.setlight(colortable['white'])
      basename = '{}/{}_{}_{}_{}_{}_W'.format(directory, S1, S2, S3, S4, S5)
      camera.capture(basename, range(60 * 2), wait_first=True)
      camera.setlight(colortable['off'])

      while datetime.now() < now + timedelta(seconds=1):
        pass
    except KeyboardInterrupt:
      print("\nKeyboard interupt, process is shutting down.\n")
      LEDoff()
      camera.stop_preview()
      sys.exit(1)

  LEDoff()
  camera.stop_preview()
  print("Program ended ok")


def capture_test(shutter_speed, gain):
  # ask for the values of each sample and preview
  for j in range(N_samples):
    camera.start_preview(fullscreen=False, window=(400, 0, 400, 400))
    print("\nsample number {}".format(j + 1))
    inputs_not_accepted = True
    while inputs_not_accepted:
      try:
        S1 = int(input('Input spot1: '))
        S2 = int(input('Input spot2: '))
        S3 = int(input('Input spot3: '))
        S4 = int(input('Input spot4: '))
        S5 = int(input('Input spot5: '))

        # accept inputs if all could be casted to int
        inputs_not_accepted = False

      except KeyboardInterrupt:
        print('\nInturrupted, exiting')
        LEDoff()
        camera.stop_preview()
        sys.exit(1)
      except Exception:
        print('Some inputs where not a number. Please try again')

    for sp in shutter_speed:
      for i in range(0, len(gain), 2):
        g = (gain[i], gain[i + 1])
        test_directory = os.path.join(directory, "%d_%.1f_%.1f" % (sp, *g))

        # create folder if it does not exist.
        if not os.path.exists(test_directory):
          os.mkdir(test_directory)

        camera.cam.shutter_speed = sp
        camera.cam.awb_gains = g
        # capture images with white light
        try:
          now = datetime.now()

          camera.setlight(colortable['off'], uv=1.0)
          basename = '{}/{}_{}_{}_{}_{}_W'.format(test_directory, S1, S2, S3, S4, S5)
          camera.capture(basename, range(60 * 2), wait_first=True)
          camera.setlight(colortable['off'])

          while datetime.now() < now + timedelta(seconds=1):
            pass
        except KeyboardInterrupt:
          print("\nKeyboard interupt, process is shutting down.\n")
          LEDoff()
          camera.stop_preview()
          sys.exit(1)

  LEDoff()
  camera.stop_preview()
  print("Program ended ok")


def LEDoff():
  """Turns the LED off."""
  camera.setlight((0, 0, 0), 0)


if __name__ == "__main__":
  camera = Camera()
  parser = argparse.ArgumentParser(description='Arguments for collecting samples')
  parser.add_argument('--type', type=str, default='c', choices=["A", "C", "test", "custom"],
                      help='Argument to select capture type.')
  parser.add_argument('--n_samples', type=int,
                      help='The amount of samples you will collect (if not provided, you will be prompted)')
  parser.add_argument('--ledcolor', type=str, default='white',
                      help='The color of the LED. Can be Red,Green,Blue,White(default) or UV')
  parser.add_argument('--capturetime', type=int, default=300,
                      help='The time window to capture each sample. Defaults to 300(seconds)')
  parser.add_argument('--captureinterval', type=int, default=3,
                      help='The interval between each picture. Defaults to 3(seconds')
  parser.add_argument('--shutter_speed', type=int, default=[500], nargs='+', help='The list of shutter speeds to test')
  parser.add_argument('--gain', type=float, default=(1.0, 1.0), nargs='+',
                      help='The list of white balance gains to test')
  parser.add_argument("--no_bayer", action="store_false", help="Append bayer data to pictures")
  parser.add_argument('--dataset_name', type=str,
                      help='The dataset name to be stored locally.')
  args = parser.parse_args()

  arg_dict = {'Type': args.type.lower(), 'N_samples': args.n_samples,
              'ledcolor': args.ledcolor.lower(), 'capturetime': args.capturetime,
              'captureinterval': args.captureinterval, 'bayer': not args.no_bayer}
  # get n_samples if they are forgotten
  if arg_dict['N_samples'] == None:
    print('\nOops! Looks like you forgot the argument N_samples! Please provide it below.')
    correct = False
    while (not correct):
      try:
        N_samples = 1  # int(input("How many chips will you use: "))
        correct = True
      except ValueError:
        print('Not a number, try again\n')
      except KeyboardInterrupt:
        print('\nInturrupted, exiting')
        camera.setlight(colortable['off'])
        sys.exit(1)
    arg_dict['N_samples'] = N_samples

  try:
    if args.type == 'c':
      capture_rgb()
    elif args.type == 'a':
      capture_white(args.type)
    elif args.type == 'test':
      capture_test(args.shutter_speed, args.gain)
    else:
      capture()

  except KeyboardInterrupt:
    LEDoff()
    sys.exit(1)

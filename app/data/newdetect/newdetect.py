'''
Author:       Jordan Ringenberg
  *(End numerical results calculations are primarily
   based on a script from Keenan Pinto)

Last Updated: Feb. 24, 2018

Updated throughout spring of 2018, and further updated in July 2018

This script will process a lab image containing 5
circles and return the average pixel intensity
of each circle

IMPORTANT: This script currently depends on the synthetic image
'circleBinTemplate.png' to perform template matching. This template may be
automatically created in future iterations of this script if desired

For 'lab' mode, run with:
python detectCircles.py [imagePath/imageName]

For 'calibrate' mode, run with:
python detectCircles.py calibrate [imagePath]/Pot.png [imagePath]/Phos.png [imagePath]/Nitra.png [imagePath]/Ammo.png

For 'operational' mode, run with:
python detectCircles.py operational [imagePath]/Pot.png [imagePath]/Phos.png [imagePath]/Nitra.png [imagePath]/Ammo.png
'''

from __future__ import print_function
from builtins import range

from skimage.transform import hough_ellipse, hough_circle
from skimage.morphology import skeletonize
from skimage import img_as_ubyte
from skimage.feature import peak_local_max, canny
from skimage.draw import circle_perimeter

import cv2
import numpy as np
from scipy.ndimage import morphology
import sys
from glob import glob
import math
import time
import os

#****************************Notes to Keenan:*********************************
#Switch this to True if you would like to see the intermediate images/results
debugFlag = False

#This controls the size of the output squares in training mode, relative to the
#size of the circles used in detection
#Making this higher will make the output square smaller, making it
#smaller (i.e. negative) will make the output square bigger
trainingMode_SquareRadiusShrink = 4
#Note on above^^^^ - there is no bounds checking, so making that value too big
#or too small can cause an exception to occur (for example if the shrink ammount
#was set to something like -1000, it would most likely extend outside of the
#bounds of the original image)

# This should at least make it compatible with opencv 2, 3 and 4
cv_version = [ int(x) for x in cv2.__version__.split('.') ]
if cv_version[0] == 3:
    cntsNum = 1
else:
    cntsNum = 0
#**************************End Notes to Keenan:*******************************

#find the 5 circles in the image
def findCircles(imgOrig, sampleType, circleBinList=None, bkgroundCircles=None):
  imgOrigHeight, imgOrigWidth = imgOrig.shape[:2]
  print("Original Image height & width:", imgOrigHeight, imgOrigWidth)

  if debugFlag:
      cv2.namedWindow('Original Image (displayed to fit on screen)', cv2.WINDOW_NORMAL)
      cv2.imshow('Original Image (displayed to fit on screen)', imgOrig)
      cv2.waitKey()

  returnMasks = False

  if debugFlag:
    finalDisplayImg = imgOrig.copy()

  #############################################################################
  #Compute circle masks from scratch if they weren't passed in
  #############################################################################
  if circleBinList == None:
    returnMasks = True

    #Note that these three values were given by Keenan as contants and will
    #need to be updated if the image sizes are ever updated
    circleRadiusRangeMin = 190*0.25
    circleRadiusRangeMax = 240*0.25
    detectedCirclesMeasurementRadius = 80*0.25

    templateCirclesMeasurementRadius = 208*0.25

    #used as the size to shrink the images down to (makes detecting circles and
    #other computations faster)
    newWidth    = 360

    #used to crop out the noise on the right and left sides of the circles
    leftCutoff  = 50
    rightCutoff = 20

    #approximate location in the shrunk, cropped images where we are
    #looking for the circle centers
    defaultCenters = [(141, 52), (210, 95), (189, 171), (92, 172), (70, 94)]
    #circlesFound   = [False, False, False, False, False]

    sizeRatio   = float(newWidth)/imgOrigWidth
    circleRadiusRangeMin             *= sizeRatio
    circleRadiusRangeMax             *= sizeRatio
    detectedCirclesMeasurementRadius *= sizeRatio

    #resize and crop to get rid of the border noise
    img = cv2.resize(imgOrig, (0,0), fx=sizeRatio, fy=sizeRatio)

    #finalImgSmall = img.copy()
    #grayImgSmall  = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    img = img[::,leftCutoff:newWidth - rightCutoff,::]

    imgHeight, imgWidth = img.shape[:2]
    print("Resized Cropped Image height & width:", imgHeight, imgWidth)

    print("Size ratio:", sizeRatio)

    if debugFlag:
      cv2.imshow('Resized and Cropped Image', img)
      cv2.waitKey()

    img = cv2.bilateralFilter(img, 9, 9, 9)

    if debugFlag:
      cv2.imshow('Resized and Cropped Image After Filtering', img)
      cv2.waitKey()

    bin = np.zeros([img.shape[0], img.shape[1]], dtype=np.uint8)
    im  = bin.copy()
    for i in cv2.split(img):
      #Inner morphological gradient.
      im = np.maximum(im, morphology.grey_dilation(i, (9, 9)) - i)
      im.reshape(img.shape[0], img.shape[1])
      mean, std = im.mean(), im.std()
      bin = np.maximum(bin, im)
      bin.reshape(img.shape[0], img.shape[1])

    #binarize the edge map
    mean, std = bin.mean(), bin.std()
    ret, bin = cv2.threshold(bin, mean + .3 * std, 255, cv2.THRESH_BINARY)

    #skeleton image of edge map
    skeletonImg = bin.copy()
    skeletonImg[skeletonImg == 255] = 1
    skel = skeletonize(skeletonImg)
    skel = img_as_ubyte(skel)

    if debugFlag:
      cv2.imshow('Binary Image', bin)
      cv2.imshow('Skeleton Image', skel)
      cv2.waitKey()


    #use the skeleton image to template match on
    img =  skel.copy()
    img2 = img.copy()
    templateOrig = cv2.imread('circleBinTemplate.png',0)
    w, h = templateOrig.shape[::-1]

    bestScore = 0
    bestTemplate = np.zeros((imgHeight,imgWidth), np.uint8)

    #cycle through tempate rotations from -10 to 10 degrees and get the best match
    method = cv2.TM_CCOEFF_NORMED
    for i in range(-10, 11, 2):
        img = img2.copy()

        M = cv2.getRotationMatrix2D((w/2,h/2), -i, 1)
        template = cv2.warpAffine(templateOrig, M, (w, h))

        # Apply template Matching
        res = cv2.matchTemplate(img, template, method)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)

        top_left = max_loc
        bottom_right = (top_left[0] + w, top_left[1] + h)

        cv2.rectangle(img,top_left, bottom_right, 255, 2)

        if max_val > bestScore:
            bestScore = max_val
            bestTemplate = np.zeros((imgHeight,imgWidth), np.uint8)
            bestTemplate[max_loc[1]:max_loc[1]+h, max_loc[0]:max_loc[0]+w] += template
        if debugFlag:
            print(min_val, max_val, min_loc, max_loc)
            cv2.imshow('Template Image ', template)
            cv2.imshow('Matched Image ', img)
            img[max_loc[1]:max_loc[1]+h, max_loc[0]:max_loc[0]+w] += template
            cv2.imshow('Matched Image2 ', img)
            cv2.imshow('Best Template', bestTemplate)
            cv2.waitKey()


    #array to hold each individual circle image
    circleBinList = []

    circleBin       = np.zeros((imgHeight,imgWidth), np.uint8)
    bkgroundCircles = np.zeros((imgHeight,imgWidth), np.uint8)

    #go through each of the five contours in the template and get the centroids,
    #storing the resulting circle in the appropriate circleBin variables
    avgx = 0
    avgy = 0

    lastX = 0
    lastY = 0

    #this detects contours from bottom to top of image
    cnts = cv2.findContours(bestTemplate.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    #IMPORTANT! different versions of OpenCV have different return order in
    # findContours. Change this to cnts[1] if this step is not working
    cnts = cnts[cntsNum]
    for c in cnts:
        M = cv2.moments(c)
        cX = int(M["m10"] / M["m00"])
        cY = int(M["m01"] / M["m00"])
        print(cX, cY)
        avgx += cX
        avgy += cY

        newCircle = np.zeros((imgHeight,imgWidth), np.uint8)
        cv2.circle(newCircle, (cX, cY), int(detectedCirclesMeasurementRadius), 255, -1)
        circleBin = cv2.bitwise_or(circleBin, newCircle)

        #looking at the bottom two circles, we want the one on the right to
        #be first
        if len(circleBinList) == 1 and lastX < cX:
                circleBinList.insert(0, newCircle.copy())
        #looking at the middle two circles, we want the one on the right to be
        #first overall
        elif (len(circleBinList) == 2 or len(circleBinList) == 3) and lastX < cX:
                circleBinList.insert(0, newCircle.copy())
        #the one closest to the top should be the first one in the sequence
        elif len(circleBinList) == 4:
                circleBinList.insert(0, newCircle.copy())
        else:
           circleBinList.append(newCircle.copy())

        lastX = cX
        lastY = cY
    #find the average position of the circles so that the first backround
    #circle can be put right in the center of the "circle pentagon"
    avgx = avgx // 5
    avgy = avgy // 5

    #print("Circles found by Hough:", circlesFound)
    #print("(False = Circles that Hough couldn't find, which will be drawn with default coordinates)")

    #print("DEBUG - center average:", avgx, avgy)
    #draw the center background circle
    cv2.circle(bkgroundCircles, (avgx, avgy), int(detectedCirclesMeasurementRadius * .8), 255, -1)

    #find the distance of where the bottom-most background circle should go
    dist = imgHeight - int(detectedCirclesMeasurementRadius * 1.25) - avgy

    #pythagorean theorem to find the x/y 45 degree distance for the other two
    #background circles
    pyth_dist = int(math.sqrt( dist * dist / 2 ))

    #draw the bottom background circle
    cv2.circle(bkgroundCircles, (avgx, avgy + dist), int(detectedCirclesMeasurementRadius * .8), 255, -1)
    #draw the upper left background circle
    cv2.circle(bkgroundCircles, (avgx - pyth_dist, avgy - pyth_dist), int(detectedCirclesMeasurementRadius * .8), 255, -1)
    #draw the upper right background circle
    cv2.circle(bkgroundCircles, (avgx + pyth_dist, avgy - pyth_dist), int(detectedCirclesMeasurementRadius * .8), 255, -1)

    #add back what was cropped off and resize to original size
    circleBin = cv2.copyMakeBorder(circleBin, 0, 0, leftCutoff, rightCutoff, cv2.BORDER_CONSTANT)
    circleBin = cv2.resize(circleBin, (imgOrigWidth, imgOrigHeight))

    #add back what was cropped off and resize to original size
    bkgroundCircles = cv2.copyMakeBorder(bkgroundCircles, 0, 0, leftCutoff, rightCutoff, cv2.BORDER_CONSTANT)
    bkgroundCircles = cv2.resize(bkgroundCircles, (imgOrigWidth, imgOrigHeight))

    if debugFlag:
      cv2.namedWindow('circleBinList Item (displayed to fit on screen)', cv2.WINDOW_NORMAL)

    #add back what was cropped off and resize to original size (do for each circle)
    for i in range(0, len(circleBinList)):
      circleBinList[i] = cv2.copyMakeBorder(circleBinList[i],0,0,leftCutoff,rightCutoff,cv2.BORDER_CONSTANT)
      circleBinList[i] = cv2.resize(circleBinList[i], (imgOrigWidth, imgOrigHeight))

      if debugFlag:
        cv2.imshow('circleBinList Item (displayed to fit on screen)', circleBinList[i])
        cv2.waitKey()
  #end compute circles from scratch
  #############################################################################

  #gray image used to detect intensity of the circles
  print("Sample type:", sampleType)
  if sampleType == "POT":
    #singleChannelImg = imgOrig[:, :, 0]
    singleChannelImg = cv2.cvtColor(imgOrig, cv2.COLOR_BGR2HSV)[:, :, 0] #extract the hue (from HSV) channel pixels
    bgimg = cv2.imread("potbg.png")
    bgimg = cv2.cvtColor(bgimg, cv2.COLOR_BGR2HSV)[:, :, 0]
    singleChannelImg = cv2.subtract(bgimg, singleChannelImg)
    cv2.namedWindow('Subtracted image', cv2.WINDOW_NORMAL)
    cv2.imshow('Subtracted image', singleChannelImg)
    cv2.waitKey()
  elif sampleType == "AMMO":
    #singleChannelImg = imgOrig[:, :, 0]
    singleChannelImg = cv2.cvtColor(imgOrig, cv2.COLOR_BGR2HSV)[:, :, 0] #extract the hue (from HSV) channel pixels
    bgimg = cv2.imread("ammobg.png")
    bgimg = cv2.cvtColor(bgimg, cv2.COLOR_BGR2HSV)[:, :, 0]
    singleChannelImg = cv2.subtract(bgimg, singleChannelImg)
    cv2.namedWindow('Subtracted image', cv2.WINDOW_NORMAL)
    cv2.imshow('Subtracted image', singleChannelImg)
    cv2.waitKey()
  elif sampleType == "NITRA":
    singleChannelImg = imgOrig[:, :, 0] #Extract the blue channel pixels
    bgimg = cv2.imread("nitrabg.png")
    bgimg = bgimg[:, :, 0]
    singleChannelImg = cv2.subtract(bgimg, singleChannelImg)
    cv2.namedWindow('Subtracted image', cv2.WINDOW_NORMAL)
    cv2.imshow('Subtracted image', singleChannelImg)
    cv2.waitKey()
  elif sampleType == "PHOS":
    singleChannelImg = imgOrig[:, :, 2] #Extract the red channel pixels
    bgimg = cv2.imread("phosbg.png")
    bgimg = cv2.cvtColor(bgimg, cv2.COLOR_BGR2HSV)[:, :, 2]
    singleChannelImg = cv2.subtract(bgimg, singleChannelImg)
    cv2.namedWindow('Subtracted image', cv2.WINDOW_NORMAL)
    cv2.imshow('Subtracted image', singleChannelImg)
    cv2.waitKey()
  else:
    singleChannelImg = cv2.cvtColor(imgOrig, cv2.COLOR_BGR2GRAY)
    singleChannelImg = cv2.bitwise_not(singleChannelImg)

  imgSingleChannelHeight, imgSingleChannelWidth = imgOrig.shape[:2]
  print("Single Channel Image height & width:", imgSingleChannelHeight, imgSingleChannelWidth)

  bkgroundIntensityAvg = cv2.mean(singleChannelImg, bkgroundCircles)[0]
  print("Average intensity for background circles: ", bkgroundIntensityAvg)

  if debugFlag:
    circleBin = np.zeros((imgOrigHeight,imgOrigWidth), np.uint8)

  intensityAverages = []
  #for each circle, get it's average graylevel intensity.
  #Store in 'averages' list for later use
  for i in range(0, len(circleBinList)):
    avg = cv2.mean(singleChannelImg, circleBinList[i])[0]
    print("Average intensity for circle " + str(i + 1) + ": ", avg)
    intensityAverages.append(avg)

    if debugFlag:
      circleBin = cv2.bitwise_or(circleBin, circleBinList[i])

  #Final debugging visuals
  if debugFlag:
    finalDisplayImg[circleBin == 0] /= 3
    finalDisplayImg[bkgroundCircles > 0] *= 2

    cv2.namedWindow('Highlighted Circles on Original Image (displayed to fit on screen)', cv2.WINDOW_NORMAL)
    cv2.imshow('Highlighted Circles on Original Image (displayed to fit on screen)', finalDisplayImg)

    cv2.namedWindow('Transformed Image (displayed to fit on screen)', cv2.WINDOW_NORMAL)
    cv2.imshow('Transformed Image (displayed to fit on screen)', singleChannelImg)

    #for display purposes only
    #if sampleType == "POT":
    #  blueChannelImg = np.zeros([imgOrigHeight, imgOrigWidth, 3], dtype=np.uint8)
    #  blueChannelImg[:,:,0] = singleChannelImg
    #  cv2.namedWindow('Potassium Hue Channel Image (displayed to fit on screen)', cv2.WINDOW_NORMAL)
    #  cv2.imshow('Potassium Hue Channel Image (displayed to fit on screen)', blueChannelImg)

    cv2.namedWindow('circleBin All (displayed to fit on screen)', cv2.WINDOW_NORMAL)
    cv2.imshow('circleBin All (displayed to fit on screen)', circleBin)

    cv2.namedWindow('Background Circles (displayed to fit on screen)', cv2.WINDOW_NORMAL)
    cv2.imshow('Background Circles (displayed to fit on screen)', bkgroundCircles)

    cv2.waitKey()

  #return:
  #1) an array (size 5) of average intensity values for each circle
  #2) the average intensity value of the 4 background circles
  #3) an array (size 5) of masks for each of the five detected circles (clockwise ordering)
  #4) a mask containing the four background circles

  if returnMasks == True:
    return intensityAverages, bkgroundIntensityAvg, circleBinList, bkgroundCircles
  else:
      #3) and 4) are not returned if they are already known and used
      #as input into this function
      return intensityAverages, bkgroundIntensityAvg


def writeCirclesToFiles(imgOrig, circleBinList, sampleTypeUniqueName):
  shrinkAmt = trainingMode_SquareRadiusShrink

  print("Sample type unique id for training mode: " + sampleTypeUniqueName)
  circleNum = 1
  for circleImg in circleBinList:
    #this detects contours from bottom to top of image
    cnts = cv2.findContours(circleImg.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    #IMPORTANT! different versions of OpenCV have different return order in
    # findContours. Change this to cnts[1] if this step is not working
    cnts = cnts[cntsNum]
    for cnt in cnts:
      x, y, w, h = cv2.boundingRect(cnt)

    print(x, y, w, h)
    circleCutoutFromOrig = imgOrig[y+shrinkAmt:y+h-shrinkAmt, x+shrinkAmt:x+w-shrinkAmt]
    cv2.imwrite(sampleTypeUniqueName + '_' + str(circleNum) + '.png', circleCutoutFromOrig)

    if debugFlag:
      cv2.namedWindow('Circle Cut Out From Original', cv2.WINDOW_NORMAL)
      cv2.imshow('Circle Cut Out From Original', circleCutoutFromOrig)

      cv2.namedWindow('Circle Bin Image (displayed to fit on screen)', cv2.WINDOW_NORMAL)
      cv2.imshow('Circle Bin Image (displayed to fit on screen)', circleImg)
      cv2.waitKey()

    circleNum += 1

#example usage: python detectCircles.py [calibrate or operational] images/imgsamples/imgsamples/standards/originals/Pot.png images/imgsamples/imgsamples/standards/originals/Phos.png images/imgsamples/imgsamples/standards/originals/Nitra.png images/imgsamples/imgsamples/standards/originals/Ammo.png
if __name__== "__main__":

  if len(sys.argv) < 2:
    print("Not enough arguments!")
  elif len(sys.argv) != 2 and len(sys.argv) != 3 and len(sys.argv) != 6:
    print("(exiting...) Please conform to the following sample usage:")
    print("python detectCircles.py Pot.png")
    print("OR")
    print("python detectCircles.py calibrate Pot.png Phos.png Nitra.png Ammo.png")
    print("OR")
    print("python detectCircles.py operational Pot.png Phos.png Nitra.png Ammo.png")
    print("OR")
    print("python detectCircles.py training Nitra.png")
    sys.exit(1)


  modeType = 'lab'

  if sys.argv[1] == 'training':
    modeType = 'training'
  if sys.argv[1] == 'calibrate':
    modeType = 'calibrate'
  if sys.argv[1] == 'operational':
    modeType = 'operational'

  print("*********************************")
  print("Mode:", modeType)
  print("*********************************")

  if modeType == 'lab':
    inputFile = sys.argv[1]
  else:
    inputFile = sys.argv[2]

  #get the sample type from the file name (pot's manipulated image calculation
  #is different from the others)
  sampleType = inputFile[inputFile.rfind('/') + 1:inputFile.rfind('.')].upper()
  fileFolder = inputFile[0:inputFile.rfind('/')]

  print('\nInput File: ', str(inputFile))
  imgOrig = cv2.imread(str(inputFile))
  intensityAverages, bkgroundIntensityAvg, circleBinList, bkgroundCircles = findCircles(imgOrig, sampleType)

  if modeType == 'lab':
    #Add an output text file for "lab" mode with specs provided by Keenan
    g = open(sampleType + "_results_" + str(time.time()) + ".txt", "w")
    g.write("Spot1: %f" %intensityAverages[0])
    g.write("\n")
    g.write("Spot2: %f" %intensityAverages[1])
    g.write("\n")
    g.write("Spot3: %f" %intensityAverages[2])
    g.write("\n")
    g.write("Spot4: %f" %intensityAverages[3])
    g.write("\n")
    g.write("Spot5: %f" %intensityAverages[4])
    g.write("\n")
    g.write("Background Average: %f" %bkgroundIntensityAvg)
    g.write("\n")
    g.close()

  if modeType == 'training':
    trainingResultsFolder = fileFolder + "/training_results/"
    if not os.path.exists(trainingResultsFolder):
      os.makedirs(trainingResultsFolder)

    uniqueID = int(time.time())
    sampleTypeUniqueName = trainingResultsFolder + sampleType + "_" + str(uniqueID)
    #Add an output text file for "training" mode with specs provided by Keenan
    g = open(sampleTypeUniqueName + ".csv", "w")
    g.write(sampleTypeUniqueName + "_1,%f" %intensityAverages[0])
    g.write("\n")
    g.write(sampleTypeUniqueName + "_2,%f" %intensityAverages[1])
    g.write("\n")
    g.write(sampleTypeUniqueName + "_3,%f" %intensityAverages[2])
    g.write("\n")
    g.write(sampleTypeUniqueName + "_4,%f" %intensityAverages[3])
    g.write("\n")
    g.write(sampleTypeUniqueName + "_5,%f" %intensityAverages[4])
    g.write("\n")
    g.close()

    writeCirclesToFiles(imgOrig, circleBinList, sampleTypeUniqueName)

  #keep consistent with Keenan's variable names:
  ck_avg = bkgroundIntensityAvg #potassium background circles avg
  ck     = intensityAverages[4] #potassium circle avg

  if len(sys.argv) == 6:
    inputFile = sys.argv[3]
    #get the sample type from the file name
    sampleType = inputFile[inputFile.rfind('/') + 1:inputFile.rfind('.')].upper()
    print('\nInput File: ', str(inputFile))
    imgOrig = cv2.imread(str(inputFile))
    intensityAverages, bkgroundIntensityAvg = findCircles(imgOrig, sampleType, circleBinList, bkgroundCircles)

    #keep consistent with Keenan's variable names:
    cp_avg = bkgroundIntensityAvg #phosphate background circles avg
    cp     = intensityAverages[3] #phosphate circle avg

    inputFile = sys.argv[4]
    #get the sample type from the file name
    sampleType = inputFile[inputFile.rfind('/') + 1:inputFile.rfind('.')].upper()
    print('\nInput File: ', str(inputFile))
    imgOrig = cv2.imread(str(inputFile))
    intensityAverages, bkgroundIntensityAvg = findCircles(imgOrig, sampleType, circleBinList, bkgroundCircles)

    #keep consistent with Keenan's variable names:
    cn_avg = bkgroundIntensityAvg   #nitrate background circles avg
    cn    = intensityAverages[2]   #nitrate circle avg

    inputFile = sys.argv[5]
    #get the sample type from the file name
    sampleType = inputFile[inputFile.rfind('/') + 1:inputFile.rfind('.')].upper()
    print('\nInput File: ', str(inputFile))
    imgOrig = cv2.imread(str(inputFile))
    intensityAverages, bkgroundIntensityAvg = findCircles(imgOrig, sampleType, circleBinList, bkgroundCircles)

    #keep consistent with Keenan's variable names:
    ca_avg = bkgroundIntensityAvg  #ammonia background circles avg
    ca    = intensityAverages[1]   #ammonia circle avg

  cv2.destroyAllWindows()

  if modeType == 'calibrate':
    c = open("calibration.txt", "w")   #Create a text file and open for adding calibration results
    c.write("%f\n" %cp_avg)
    c.write("%f\n" %cp)
    c.write("%f\n" %cn_avg)
    c.write("%f\n" %cn)
    c.write("%f\n" %ca_avg)
    c.write("%f\n" %ca)
    c.write("%f\n" %ck_avg)
    c.write("%f\n" %ck)

    #Close the file after saving calibration results
    c.close()
  if modeType == 'operational':
    #keep consistent with Keenan's variable names. Since this is operational
    #mode, switch the 'c' variable names to 'm' variable names since the 'c'
    #variables will be read in from the calibration file
    mp_avg = cp_avg
    mp = cp

    mn_avg = cn_avg
    mnitra = cn

    ma_avg = ca_avg
    ma = ca

    mk_avg = ck_avg
    mk = ck

    #######################################################################
    #Read Calibration values from calibration.txt file ####################
    #######################################################################

    # Open the file for reading.
    calibrationFileName = 'calibration.txt'

    #Make sure file exists before trying to read
    try:
      with open(calibrationFileName, 'r') as infile:
          data = infile.read()  # Read the contents of the calibration file into memory.
    except IOError:
      print()
      print("***************************************************************")
      print("ERROR! Could not open", calibrationFileName, " for reading. Exiting...")
      print("***************************************************************")
      sys.exit(1)

    # Return a list of the lines, breaking at line boundaries.
    calib = data.splitlines()

    if len(calib) < 7:
      print()
      print("***************************************************************")
      print("ERROR! Unexpected format in", calibrationFileName, ". Exiting...")
      print("***************************************************************")
      sys.exit(1)

    cp_avg = float(calib[0])
    cp = float(calib[1])

    cn_avg = float(calib[2])
    cn = float(calib[3])

    ca_avg = float(calib[4])
    ca = float(calib[5])

    ck_avg = float(calib[6])
    ck = float(calib[7])

    infile.close()

    #######################################################################
    #Constant values from graphs ##########################################
    #######################################################################

    constant_p1 = 1
    constant_p2 = 1
    constant_n1 = 1
    constant_n2 = 1
    constant_a1 = 1
    constant_a2 = 1
    constant_k1 = 1
    constant_k2 = 1

    #############################################################################################
    #############################################################################################
    #Mathematical calculations ##################################################################
    #############################################################################################
    #############################################################################################


    #####PHOSPHATE VALUE##################

    #Case 1
    if mp_avg > cp_avg :
        bdp = mp_avg - cp_avg

        ap = mp - bdp

        value_p = ap - cp

        results_p = (value_p - constant_p1)/constant_p2

       #results_p = pow(10, power_p)

        f = open("results.txt", "w")   #Create a text file and open for adding results
        f.write("P: %.2f" %results_p)
        f.write("\n")

        #print("PHOSPHATE =   ")
        #print(results_p)
        #print("\n")

    #Case 2
    if mp_avg < cp_avg :
        bdp = abs(mp_avg - cp_avg)

        ap = mp + bdp

        value_p = ap - cp

        results_p = (value_p - constant_p1)/constant_p2

       #results_p = pow(10, power_p)

        f = open("results.txt", "w")   #Create a text file and open for adding results
        f.write("P: %.2f" %results_p)
        f.write("\n")

        #print("Phosphate =   ")
        #print(results_p)
        #print("\n")


    #Case 3
    if mp_avg == 0 :

        results_p = 0

        f = open("results.txt", "w")   #Create a text file and open for adding results
        f.write("P: %f" %results_p)
        f.write("\n")


    #####NITRATE VALUE####################
    #Use constants constant_n1 and n2 here

    #Case 1
    if mn_avg > cn_avg :
        bdn = mn_avg - cn_avg

        an = mnitra - bdn

        value_n = an - cn

        results_nitra = (value_n - constant_n1)/constant_n2

        #results_nitra = pow(10, power_n)

        f.write("N: %.2f" %results_nitra)
        f.write("\n")

        #print("NITRATE =   ")
        #print(results_nitra)
        #print("\n")

    #Case 2
    if mn_avg < cn_avg :
        bdn = abs(mn_avg - cn_avg)

        an = mnitra + bdn

        value_n = an - cn

        results_nitra = (value_n - constant_n1)/constant_n2

        #results_nitra = pow(10, power_n)

        f.write("N: %.2f" %results_nitra)
        f.write("\n")

        #print("NITRATE =   ")
        #print(results_nitra)
        #print("\n")

    #Case 3
    if mn_avg == 0 :

        results_nitra = 0

        f.write("N: %f" %results_nitra)
        f.write("\n")

    ########################################################################


    ##### AMMONIUM VALUE####################
    #Use constants constant_a1 and a2 here

    #Case 1
    if ma_avg > ca_avg :
        bda = ma_avg - ca_avg

        aa = ma - bda

        value_a = aa - ca


        results_ammo = (value_a - constant_a1)/constant_a2

        f.write("A: %.2f" %results_ammo)
        f.write("\n")

    #Case 2
    if ma_avg < ca_avg :
        bda = abs(ma_avg - ca_avg)

        aa = ma + bda


        value_a = aa - ca


        results_ammo = (value_a - constant_a1)/constant_a2


        f.write("A: %.2f" %results_ammo)
        f.write("\n")

    #Case 3
    if ma_avg == 0 :

        results_ammo = 0

        f.write("A: %f" %results_ammo)
        f.write("\n")

     #print("AMMO = ")
     #print(results_ammo)
     #print("\n")

    ########################################################################

    #####POTASSIUM VALUE##################

    #Case 1
    if mk_avg > ck_avg :
        bdk = mk_avg - ck_avg

        ak = mk - bdk

        value_k = ak - ck

        results_k = (value_k - constant_k1)/constant_k2

        #results_k = pow(10, power_k)

        f.write("K: %.2f" %results_k)
        f.write("\n")

        #print("POTASSIUM =   ")
        #print(results_k)
        #print("\n")

    #Case 2
    if mk_avg < ck_avg :
        bdk = abs(mk_avg - ck_avg)

        ak = mk + bdk

        value_k = ak - ck

        results_k = (value_k - constant_k1)/constant_k2

        #results_k = pow(10, power_k)

        f.write("K: %.2f" %results_k)
        f.write("\n")

        #print("POTASSIUM =   ")
        #print(results_k)
        #print("\n")

    #Case 3
    if mk_avg == 0 :

        results_k = 0

        f.write("K: %f" %results_k)
        f.write("\n")




    #Close the file after storing values.
    #Note that this method replaces previous results on each run
    f.close()

    g = open("raw_results.txt", "w")   #Create a text file and open for adding raw results

    g.write("MP_AVG: %f" %mp_avg)
    g.write("\n")
    g.write("MP: %f" %mp)
    g.write("\n")
    g.write("MN_AVG: %f" %mn_avg)
    g.write("\n")
    g.write("MNITRA: %f" %mnitra)
    g.write("\n")
    g.write("MA_AVG: %f" %ma_avg)
    g.write("\n")
    g.write("MA: %f" %ma)
    g.write("\n")
    g.write("MK_AVG: %f" %mk_avg)
    g.write("\n")
    g.write("MK: %f" %mk)
    g.write("\n")

    g.close()



    #print("Meauring done")

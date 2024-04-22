import numpy as np
import matplotlib.pyplot as plt

"""
Script to test the plots used in gameAntiCaptcha.py
"""

def createPlot(userID, difficulty):
        RNG = np.random.default_rng()
        #numPoints = int(RNG.random(1)[0]*25)
        numPoints = 28 - 3*difficulty
        slope = RNG.uniform(-difficulty, difficulty)
        intercept = RNG.uniform(0, 5) + np.abs(slope)
        print(slope, intercept)
        x = RNG.uniform(0, 10, numPoints)
        if slope>0:
            maxAllowedX = (10 - intercept)/slope
        else:
            maxAllowedX = -intercept/slope
        x = x*maxAllowedX/10
        y = slope*x + intercept
        tildeX = x + RNG.uniform(-0.6*difficulty, 0.6*difficulty, numPoints)
        Fig, ax = plt.subplots()
        ax.scatter(tildeX,y)
        ax.set_xlim(min(0, np.min(tildeX)), max(10, np.max(tildeX)))
        ax.set_ylim(min(0, np.min(tildeX)), max(10, np.max(tildeX)))
        plt.show()
        return tildeX, y
        #print(len(tildeX))
        #print(len(tildeX[np.logical_and(tildeX>0, tildeX<10)]))
        #return tildeX[np.logical_and(tildeX>0, tildeX<10)], y[np.logical_and(tildeX>0, tildeX<10)]

def resultPlot(x, y, predCoef):
            coef = np.polyfit(x,y,1)
            poly1d_fn = np.poly1d(coef)
            poly1d_fn2 = np.poly1d(predCoef)
            Fig, ax = plt.subplots()
            ax.scatter(x, y)
            points = np.linspace(min(0, np.min(x)),max((max(10, np.max(x))-coef[1])/coef[0], (min(0, np.min(x))-coef[1])/coef[0]))
            points2 = np.linspace(min(0, np.min(x)),max((max(10, np.max(x))-predCoef[1])/predCoef[0], (min(0, np.min(x))-predCoef[1])/predCoef[0]))
            ax.plot(points, poly1d_fn(points), linestyle="--", color="k")
            ax.plot(points2, poly1d_fn2(points2), linestyle="--", color="tab:green")
            ax.set_xlim(min(0, np.min(x)), max(10, np.max(x)))
            ax.set_ylim(min(0, np.min(x)), max(10, np.max(x)))
            plt.show()



if __name__ == "__main__":
        x, y = createPlot(1231, 2)
        resultPlot(x,y, (1,2))
"""
Script Name:    Regr_ZScore

Description:    Computes a composite predictor by
                converting each predictor to a z-score,
                then regressing the z scores against 
                the target, then createing one predictor
                as the r2 weighted sums of the 
                z score predictors

"""

import numpy as np
from resources.modules.StatisticalModelsTab import CrossValidationAlgorithms, ModelScoring

class Regressor(object):
    """
    """
    name = "Z-Score Regression"

    def __init__(self, crossValidation = None, scoringParameters = None):
        """
        Class Initializer.

        arguments:
            -crossValidation:   string describing which cross validation
                                method to use when using this regression
                                class. As of this writing, the options are
                                "KFOLD_5" (5 fold cross validation)
                                "KFOLD_10" (10 fold cross validation)
                                "LOO" (Leave-one-out AKA jacknife)
            -scoringParameters: list of scoring metrics to score models.
                                e.g. ['ADJ_R2', 'MSE', 'AIC_C']
        """

        # Parse arguments
        self.crossValidation = crossValidation if crossValidation != None else "KFOLD_5"
        self.scoringParameters = scoringParameters if scoringParameters != None else ["ADJ_R2"]

        # Data Initializations
        self.x = np.array([[]])     # Raw X Data
        self.y = np.array([])       # Raw Y Data
        self.y_p = np.array([])     # Model Predictions

        # Fitting Parameters
        self.coef = []
        self.intercept = 0

        # Set up cross validator, and scorers
        self.scorers = [getattr(ModelScoring, param) for param in self.scoringParameters]
        self.crossValidator = getattr(CrossValidationAlgorithms, self.crossValidation)
        
        # Intialize dictionaries to store scores
        self.cv_scores = {}
        self.scores = {}
        self.y_p_cv = []

        return

    def regress(self, x, y):
        """
        """

        # Convert all the x data to z-scores
        self.z = (self.x - np.nanmean(self.x)) / np.nanstd(self.x)

        # Create a 10-fold cross-validator
        TenFoldValidator = getattr(CrossValidationAlgorithms, "KFOLD_10")

        # Create an R2 Scorer
        scorer = getattr(ModelScoring, 'R2')

        # Regress the z scores against the y data and store the cross validated r2 scores
        self.r_scores = []
        for i in range(self.z.shape[1]):

            # Create a list to store cross validated predictions
            y_p_cv = np.array([], dtype=np.float32)

            # Iterate over the cross validation samples and compute regression scores
            for xsample, ysample, xtest, _ in TenFoldValidator.yield_samples(X = self.z[:,i], Y = self.y):

                 # Concatenate a row of 1's to the data so that we can compute an intercept
                X_ = np.concatenate((np.ones(shape=xsample.shape[0]).reshape(-1,1), xsample), 1)

                # Compute the least squares solution
                coef_all = np.linalg.inv(X_.transpose().dot(X_)).dot(X_.transpose()).dot(ysample)
                coef = coef_all[1:]
                intercept = coef_all[0]
                
                # Append Cross Validated data to the array
                y_p_cv = np.append(y_p_cv, np.dot(xtest, coef) + intercept)
                
            # Compute CV Score
            self.r_scores.append(scorer(self.y, y_p_cv, 1))

        # Note at this point that some r2 scores may be negative
        # To combat that, we 

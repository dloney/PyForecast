"""
Script Name:    FeatSel_SequentialBackwardFloating.py

Description:    Sequential Backward Floating Selection is a feature
                selection scheme that iteratively removes features 
                to an initially full model. Features are removed if
                thier removal to the model increases the model's
                score. Features are then added iteratively and
                the best resulting model is kept. A rough algorith 
                for this scheme is as follows 
                (taken from: http://research.cs.tamu.edu/prism/lectures/pr/pr_l11.pdf):

                For a system with 6 possible predictors

                1) Y = "111111" [no predictors in model]

                2) Select the best feature to remove from the model:
                    predictor_to_remove = maximize_score(Y - k)
                        (where k is one of the 6 predictors)
                    Y = Y - predictor_to_remove 

                3) Select the best feature to add:
                    predictor_to_add = maximize_score(Y + k)

                4) if score(Y+k) > score(Y) then 
                    Y = Y + predictor_to_add
                    goto 3
                   else
                    goto 2
"""

import bitarray as ba
import importlib
from resources.modules.StatisticalModelsTab import ModelScoring
import numpy as np


class FeatureSelector(object):

    name = "Sequential Backward Floating Selection"

    def __init__(self, parent = None, **kwargs):
        """
        """

        #

        # Create References to the predictors and the target
        self.predictorPool = parent.modelRunTableEntry['PredictorPool']
        self.target = parent.modelRunTableEntry['Predictand']
        self.parent = parent

        # Set up the Regression and Cross Validation
        self.regressionName = kwargs.get("regression", "Regr_MultipleLinearRegressor")
        module = importlib.import_module("resources.modules.StatisticalModelsTab.RegressionAlgorithms.{0}".format(self.regressionName))
        regressionClass = getattr(module, 'Regressor')
        self.regression = regressionClass(crossValidation = kwargs.get("crossValidation", None), scoringParameters = kwargs.get("scoringParameters", None))
        
        # Create variables to store the current predictors and performance
        self.numPredictors = len(self.predictorPool)
        self.currentPredictors = kwargs.get("initialModel", ba.bitarray([True] * self.numPredictors))

        # Add in any forced predictors
        self.currentPredictors = self.currentPredictors | self.parent.forcedPredictors
        
        self.previousPredictors = self.currentPredictors.copy()
        self.currentScores = {}

        # 

        return
    

    def scoreModel(self, model):
        """
        Scores the model using the provided
        regression scheme. 
        """

        # Compile the data to fit with the regression method
        x = self.parent.xTraining[:, list(model)]
        y = self.parent.yTraining[~np.isnan(x).any(axis=1)]
        x = x[~np.isnan(x).any(axis=1)]


        # Fit the model with the regression method and get the resulting score
        _, _, score, _ = self.regression.fit(x, y, crossValidate = True)

        return score
    

    def logCombinationResult(self, model_str = None, score = None):
        """
        Under-defined function. Currently just adds the model to 
        the model list. Theoretically, we could use this 
        function to update graphics of model building, or
        do real-time analysis of models as they are being 
        built
        """
        self.parent.computedModels[model_str] = score
        
        return


    def iterate(self):
        """
        Iterates to perform the Sequential Forward Selection.
        The loop continues until the algorithm declines adding
        or subtracting any predictors from the model (i.e. adding
        or subtracting predictors is not increasing the score
        of the model.)
        """

        # Set up an iteration
        while True:
            
            # Search for new predictors to add
            self.trySubtraction()

            # Search for predictors to remove
            self.tryAddition()

            # Check if we've added any new predictors or removed predictors
            if self.previousPredictors == self.currentPredictors:
            
                # If the model has not changed, we're done!
                break
            
            # The model has changed, so we iterate again
            else:
                self.previousPredictors = self.currentPredictors
        
        return
        

    def tryAddition(self):
        """
        Attempt to add a predictor to the model. A predictor
        is added if it increases the score of the overall model.
        This function checks which remaining predictor (if any)
        increases the score the most, and adds that one.
        
        For example.

        1) The initial model is 001011
        2) We can potentially add the 1st, 2nd and 4th predictors
        3) compute the scores of adding each predictor individaully
        4) If any of the scores is greater than the initial score,
           that predictor is added and the function tries to remove another one.
        """

        # Make a copy of the predictors that we can manipulate
        model = self.currentPredictors.copy()

        # Keep track of whether we added a predictor
        predictorAdded = False

        # Iterate over the predictors
        for i in range(self.numPredictors):

            # Check that the predictor is not currently in the model (i.e. it is '0')
            if not model[i]:

                # Add the predictor to the model
                model[i] = True
                model_str = model.to01()

                # Check that we haven't already computed this model combination
                if model_str in self.parent.computedModels:
                
                    # Get the score from the list of models
                    score = self.parent.computedModels[model_str]
                    
                else:
                
                    # Compute the model score
                    score = self.scoreModel(model)

                    # Log the model results so that we don't try it again if we can avoid it
                    self.logCombinationResult(model_str, score)

                # Check if this model has a higher score than the current model
                if ModelScoring.scoreCompare(newScores = score, oldScores = self.currentScores):
                    self.currentScores = score
                    self.currentPredictors = model.copy()
                    predictorAdded = True

                # Revert the model
                model[i] = False

        # If we added a predictor, try to add another one
        if predictorAdded:
            self.tryAddition()

        # Otherwise, return
        else:
            return
        
    

    def trySubtraction(self):
        """
        Attempt to remove a predictor to the model. A predictor
        is removed if it increases the score of the overall model.
        This function checks which current predictor (if any)
        increases the score the most when removed, and removes that one.
        
        For example.

        1) The initial model is 001011
        2) We can potentially remove the 3rd, 4th and 5th predictors
        3) compute the scores of removing each predictor individaully
        4) If any of the scores is greater than the initial score,
           that predictor is removed
        """

        # Make a copy of the predictors that we can manipulate
        model = self.currentPredictors.copy()

        # Iterate over the predictors
        for i in range(self.numPredictors):

            # Check that the predictor is currently in the model (i.e. it is '1') and it's not forced
            if model[i] and not self.parent.forcedPredictors[i]:
                
                # Remove the predictor from the model
                model[i] = False
                model_str = model.to01()

                 # Check that we haven't already computed this model combination
                if model_str in self.parent.computedModels:
                
                    # Get the score from the list of models
                    score = self.parent.computedModels[model_str]
                    
                else:
                
                    # Compute the model score
                    score = self.scoreModel(model)

                    # Log the model results so that we don't try it again if we can avoid it
                    self.logCombinationResult(model_str, score)

                # Check if this model has a higher score than the current model
                if ModelScoring.scoreCompare(newScores = score, oldScores = self.currentScores):
                    self.currentScores = score
                    self.currentPredictors = model.copy()

                # Revert the model
                model[i] = True
        
        return



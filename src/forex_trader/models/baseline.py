from dataclasses import dataclass

import numpy as np
from sklearn.calibration import CalibratedClassifierCV
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


@dataclass
class ProbabilityModel:
    model_type: str = "logistic"
    calibration: str = "sigmoid"
    seed: int = 42

    def __post_init__(self):
        if self.model_type == "logistic":
            estimator = LogisticRegression(max_iter=1000, random_state=self.seed)
        elif self.model_type == "gradient_boosting":
            estimator = HistGradientBoostingClassifier(random_state=self.seed)
        elif self.model_type == "xgboost":
            from xgboost import XGBClassifier

            estimator = XGBClassifier(
                n_estimators=300,
                max_depth=4,
                learning_rate=0.03,
                subsample=0.8,
                colsample_bytree=0.8,
                random_state=self.seed,
                eval_metric="logloss",
            )
        else:
            raise ValueError(f"Unsupported model type: {self.model_type}")
        steps = [("imputer", SimpleImputer(strategy="median"))]
        if self.model_type == "logistic":
            steps.append(("scaler", StandardScaler()))
        steps.append(("model", estimator))
        self.pipeline = Pipeline(steps)
        self.calibrator = None

    def fit(self, x_train, y_train, x_validation=None, y_validation=None):
        self.pipeline.fit(x_train, y_train)
        if x_validation is not None and len(np.unique(y_validation)) > 1:
            self.calibrator = CalibratedClassifierCV(self.pipeline, method=self.calibration, cv="prefit")
            self.calibrator.fit(x_validation, y_validation)
        return self

    def predict_proba(self, x):
        model = self.calibrator or self.pipeline
        return model.predict_proba(x)[:, 1]

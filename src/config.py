# Stores the settings and variables used by the other Python files

from pathlib import Path

# Project directory
BASE_DIR = Path(__file__).resolve().parent.parent
    # Location of current Python file and then converts that location to a Path object
    # .resolve() converts it to an absolute path
    # Goes up two parents to reach main project directory (ASL ML Code)

# Dataset location
DATA_PATH = BASE_DIR / "data" / "dataset.csv"
    # Will know where to find measurements

# Model storage
MODEL_DIR = BASE_DIR / "models"
    # Will know where model is saved

MODEL_PATH = MODEL_DIR / "random_forest.joblib"
    # Will know where RF is saved
    # .joblib is the trained model (can load this)

# 11 Flex Sensors
FLEX_COLUMNS = [
    f"flex_{i}" for i in range(1, 12)
]

# 5 Contact Sensors
CONTACT_COLUMNS = []

# BNO085 IMU
IMU_COLUMNS = []

# Combine all sensor columns
FEATURE_COLUMNS = (
    FLEX_COLUMNS
)

NUM_FEATURES = len(FEATURE_COLUMNS)

# Target variable
TARGET_COLUMN = "letter"
    # This is a labeled column in CSV

# Dataset splitting
TEST_SIZE = 0.20
    # 20% of data will be reserved for testing
    # Want to avoid placing sensor measurements from the same recording
    # trial in both training and testing
RANDOM_STATE = 42
    # Keep this integer consistent so it makes it easier to 
    # compare experiments 

# Random Forest parameters
N_ESTIMATORS = 100 # How many decision trees RF will have
    # Increasing trees improves stability but increases training time and memory usage
MAX_DEPTH = None # Trees continue growing until other stopping conditions reached
    # Deeper trees can learn more complicated relationships but may overfit
MIN_SAMPLES_SPLIT = 2 # Node must contain 2 ssamples to be considered for splitting
    # Increasing this value can restrict tree complexity
MIN_SAMPLES_LEAF = 1 # Min num of training samples that must remain in each resulting leaf
    # Large min leaf sizes can help reduce overfitting

# I got this numbers from:m https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.RandomForestClassifier.html

# ESP32 serial communication
SERIAL_PORT = "COM3" #Change this from Arduino (Tools-->Port)
BAUD_RATE = 115200 # Communication speed must be the same in Arduino
    # Serial communication rate


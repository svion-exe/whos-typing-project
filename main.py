import uvicorn
import random
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path

# Import the project's custom modules
from model_manager import load_assets, get_prediction
from keystroke_processor import process_live_keystrokes, save_keystroke_data, TARGET_WORDS
from pydantic_models import LivePredictionRequest, DataSubmissionRequest

# --- Configuration ---
BASE_DIR = Path(__file__).parent
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Use the modern 'lifespan' context manager for startup and shutdown events
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handles application startup and shutdown events."""
    logger.info("Application startup...")
    # Load all machine learning assets into the app's state
    app.state.assets = load_assets(BASE_DIR)
    if not app.state.assets["loaded"]:
        logger.error(f"FATAL STARTUP ERROR: {app.state.assets['error_message']}")
    else:
        logger.info("Machine learning assets loaded successfully.")
    yield
    logger.info("Application shutdown...")

app = FastAPI(lifespan=lifespan)

# Mount the 'static' directory to serve CSS and JS files
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
# Set up Jinja2 to render the HTML template
templates = Jinja2Templates(directory=BASE_DIR / "templates")

# --- API Endpoints ---
@app.get("/", response_class=HTMLResponse)
async def serve_frontend(request: Request):
    """Serves the main index.html page with random words for each section."""
    if not app.state.assets["loaded"]:
        raise HTTPException(status_code=503, detail=f"Service Unavailable: {app.state.assets['error_message']}")

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "known_styles": app.state.assets["known_styles"],
            "live_target_word": random.choice(TARGET_WORDS),
            "submit_target_word": random.choice(TARGET_WORDS)
        }
    )

@app.post("/predict_live")
async def predict_live(request: LivePredictionRequest):
    """API endpoint to perform a prediction on live captured keystroke data."""
    logger.info(f"Received /predict_live request for word: '{request.target_word}'")
    if not app.state.assets["loaded"]:
        raise HTTPException(status_code=503, detail="Model assets are not currently loaded.")

    # The processor no longer needs the feature_columns argument
    live_features_df = process_live_keystrokes(request.events, request.target_word)

    if live_features_df is None:
        logger.warning("Feature engineering for live data failed.")
        raise HTTPException(status_code=400, detail="Invalid keystroke data received. Please type the target word correctly.")

    logger.info("Live features engineered successfully. Getting prediction...")
    prediction = get_prediction(live_features_df, app.state.assets["model"], app.state.assets["scaler"])
    logger.info(f"Prediction result: {prediction}")
    return prediction

@app.post("/submit_data")
async def submit_data(request: DataSubmissionRequest):
    """API endpoint to save a new typing sample to the raw data CSV file."""
    logger.info(f"Received /submit_data request for style: '{request.style_id}'")
    result = save_keystroke_data(request.style_id, request.target_word, request.events, BASE_DIR)
    if "error" in result:
        logger.error(f"Error saving data: {result['error']}")
        raise HTTPException(status_code=500, detail=result["error"])
    logger.info("Data submitted successfully.")
    return result

# --- Main entry point to run the app ---
if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)


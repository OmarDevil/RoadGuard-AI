# RoadGuard AI

RoadGuard AI is an end-to-end computer vision system for smart traffic monitoring and road analytics. It analyzes traffic videos using YOLO-based object detection, object tracking, lane-zone mapping, and rule-based violation detection. The system detects vehicles, tracks their movement, counts vehicles by lane, estimates congestion, identifies wrong-way driving, detects helmet violations, and flags pedestrian zone violations. Results are visualized through a web dashboard powered by FastAPI and JavaScript.

## Features

- Vehicle, motorcycle, bicycle, and pedestrian detection with Ultralytics YOLO.
- Multi-object tracking through Ultralytics `track` mode with ByteTrack by default.
- Lane-based vehicle counting with one count per track per lane.
- Wrong-way driving detection from track movement direction.
- Congestion estimation from active vehicle count and optional pixel-space speed.
- Helmet/no-helmet detection hook for a separate motorcycle rider model.
- Pedestrian road-zone violation detection.
- Annotated processed video output.
- Violation screenshots.
- SQLite storage for uploaded videos, analytics, and violations.
- FastAPI backend and plain JavaScript dashboard with Chart.js.
- CSV and JSON reports.
- Pytest coverage for geometry, lane counting, and violation rules.

## Demo Screenshots

Place dashboard and annotated-video screenshots in `data/samples/` as the project evolves.

## System Architecture

Video Upload  
-> Frame Extraction  
-> YOLO Detection  
-> Object Tracking  
-> Lane Zone Mapping  
-> Violation Rule Engine  
-> Analytics Storage  
-> FastAPI Backend  
-> JavaScript Dashboard

## Tech Stack

- Python
- Ultralytics YOLO
- OpenCV
- ByteTrack / BoT-SORT through Ultralytics
- FastAPI
- SQLite
- Pandas, NumPy
- HTML, CSS, JavaScript
- Chart.js
- Pytest

## Project Structure

```text
RoadGuard-AI/
├── api/
├── data/
├── frontend/
├── models/
├── notebooks/
├── outputs/
├── src/
├── tests/
├── config.yaml
├── requirements.txt
└── README.md
```

## Installation

```bash
cd RoadGuard-AI
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

On Linux or macOS, activate with:

```bash
source venv/bin/activate
```

## Usage

Run the API:

```bash
uvicorn api.main:app --reload
```

Windows quick start:

```bat
run.bat
```

Open the frontend:

```text
http://127.0.0.1:8000/frontend/index.html
```

Run the pipeline directly:

```bash
python -m src.main_pipeline --video data/raw/videos/test.mp4 --config config.yaml
```

Run tests:

```bash
pytest tests/
```

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/health` | API status |
| POST | `/upload-video` | Upload a traffic video |
| POST | `/analyze/{video_id}` | Run the CV pipeline |
| GET | `/videos` | List uploaded videos |
| GET | `/videos/{video_id}` | Get one video |
| GET | `/analytics/{video_id}` | Get analytics summary |
| GET | `/violations/{video_id}` | Get violations |
| GET | `/processed-video/{video_id}` | Stream processed video |
| GET | `/screenshots/{filename}` | View a violation screenshot |

## Configuration

Edit `config.yaml` to set:

- YOLO model paths and confidence threshold.
- ByteTrack or BoT-SORT tracker config.
- Input/output video paths.
- Vehicle and pedestrian classes.
- Lane polygons and expected directions.
- Road and crosswalk zone polygons.
- Wrong-way and congestion thresholds.

Lane directions support `up`, `down`, `left`, and `right`.

## Dataset Sources

Useful public sources for experiments:

- COCO-pretrained YOLO models for general object detection.
- Public traffic camera videos for road analytics prototyping.
- Helmet detection datasets from Roboflow, Kaggle, or custom annotated motorcycle rider data.

Always verify dataset licenses before publishing trained weights or demo videos.

## Results

The pipeline writes:

- Annotated videos to `outputs/processed_videos/`.
- Violation screenshots to `outputs/screenshots/`.
- CSV and JSON reports to `outputs/reports/`.
- SQLite records to `database/roadguard.db`.

## Limitations

- Wrong-way detection depends on manually configured lane direction.
- Speed is estimated in pixel-space, not real-world km/h.
- Helmet detection accuracy depends on video angle and resolution.
- Pedestrian violation detection requires predefined road and crosswalk zones.
- The system is a portfolio/research prototype, not a legal enforcement tool.

## Future Work

- Real-world camera calibration.
- Automatic lane detection.
- Real speed estimation.
- Better helmet detection model.
- Cloud deployment.
- Real-time camera stream support.
- License plate detection with privacy controls.

## Author

AI Engineering Student Portfolio Project

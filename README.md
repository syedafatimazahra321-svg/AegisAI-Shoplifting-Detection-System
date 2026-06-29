# AegisAI

AegisAI is a shoplifting detection system that analyzes retail CCTV footage using deep learning. It processes video through a YOLOv8 person detector, extracts RGB and optical flow features using MobileNetV3, and classifies suspicious behaviour using an attention-based LSTM model.

Detected incidents are logged to a web dashboard built with FastAPI and React, where security staff can review evidence clips, mark false alarms, and download PDF reports.

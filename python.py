import cv2
import numpy as np
import os
import logging
import uuid
from flask import Flask, request, render_template_string, send_from_directory

logging.basicConfig(level=logging.INFO)

UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "outputs"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

app = Flask(__name__)

# ------------------------------------------------
# FRAME EXTRACTION
# ------------------------------------------------

def extract_frames(video_path, skip=10):

    cap = cv2.VideoCapture(video_path)

    frames = []
    frame_id = 0

    while True:

        ret, frame = cap.read()

        if not ret:
            break

        if frame_id % skip == 0:
            frames.append(frame)

        frame_id += 1

    cap.release()

    return frames


# ------------------------------------------------
# SCENE CHANGE DETECTION
# ------------------------------------------------

def detect_scene_changes(frames):

    scores = []
    prev = None

    for i, frame in enumerate(frames):

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        if prev is not None:

            diff = cv2.absdiff(gray, prev)

            score = np.mean(diff)

            scores.append((score, i))

        prev = gray

    return scores


# ------------------------------------------------
# KEYFRAME SELECTION
# ------------------------------------------------

def select_keyframes(frames, k=5):

    scores = detect_scene_changes(frames)

    scores.sort(reverse=True)

    indices = [x[1] for x in scores[:k]]

    indices.sort()

    return [frames[i] for i in indices]


# ------------------------------------------------
# FEATHER PANORAMA
# ------------------------------------------------

def feather_panorama(frames):

    base = frames[0]

    for img in frames[1:]:

        h = min(base.shape[0], img.shape[0])

        base = cv2.resize(base,(int(base.shape[1]*h/base.shape[0]),h))
        img = cv2.resize(img,(int(img.shape[1]*h/img.shape[0]),h))

        overlap = 60

        left = base[:,:-overlap]
        right = img[:,overlap:]

        blend1 = base[:,-overlap:]
        blend2 = img[:,:overlap]

        alpha = np.linspace(0,1,overlap)

        blended = np.zeros_like(blend1)

        for i in range(overlap):
            blended[:,i]=(1-alpha[i])*blend1[:,i]+alpha[i]*blend2[:,i]

        base = np.hstack([left,blended,right])

    return base.astype(np.uint8)


# ------------------------------------------------
# PANORAMA
# ------------------------------------------------

def build_panorama(frames):

    stitcher=cv2.Stitcher_create()

    status,pano=stitcher.stitch(frames)

    if status==0:
        return pano

    return feather_panorama(frames)


# ------------------------------------------------
# PIPELINE
# ------------------------------------------------

def process_video(video_path):

    frames=extract_frames(video_path)

    keyframes=select_keyframes(frames)

    pano=build_panorama(keyframes)

    name=f"{uuid.uuid4().hex}.jpg"

    path=os.path.join(OUTPUT_FOLDER,name)

    cv2.imwrite(path,pano)

    return name


# ------------------------------------------------
# UI
# ------------------------------------------------

HTML="""

<!DOCTYPE html>
<html>

<head>

<title>Project • Video Panorama</title>

<style>

body{
margin:0;
font-family:Inter,Arial;
background:#f1f5f9;
color:#0f172a;
}

nav{
display:flex;
justify-content:space-between;
padding:20px 60px;
background:white;
box-shadow:0 2px 6px rgba(0,0,0,0.05);
}

.logo{
font-weight:700;
font-size:20px;
}

.hero{
text-align:center;
padding:60px 20px;
}

.hero h1{
font-size:40px;
}

.hero p{
color:#64748b;
}

.container{
width:900px;
margin:auto;
}

.card{
background:white;
padding:40px;
border-radius:12px;
box-shadow:0 6px 18px rgba(0,0,0,0.08);
}

.drop-zone{
border:2px dashed #94a3b8;
padding:50px;
border-radius:10px;
text-align:center;
cursor:pointer;
}

.drop-zone:hover{
background:#f8fafc;
}

.file-preview{
display:none;
align-items:center;
justify-content:space-between;
background:#f8fafc;
padding:10px 15px;
border-radius:8px;
margin-top:10px;
}

.remove{
cursor:pointer;
color:red;
font-weight:bold;
}

button{
padding:14px 28px;
background:#2563eb;
border:none;
border-radius:8px;
color:white;
font-size:16px;
margin-top:20px;
cursor:pointer;
}

button:hover{
background:#1d4ed8;
}

.progress{
width:100%;
background:#e2e8f0;
height:10px;
border-radius:10px;
margin-top:20px;
display:none;
}

.bar{
height:100%;
width:0%;
background:#2563eb;
border-radius:10px;
}

img{
max-width:100%;
margin-top:30px;
border-radius:8px;
}

footer{
text-align:center;
margin-top:60px;
padding:30px;
color:#64748b;
}

</style>

</head>

<body>

<nav>
<div class="logo">Project</div>
<div>Video Panorama Generator</div>
</nav>

<section class="hero">

<h1>Create Panorama From Video</h1>

<p>Generate panoramic visual summaries using computer vision.</p>

</section>

<div class="container">

<div class="card">

<form action="/process" method="post" enctype="multipart/form-data" onsubmit="startProgress()">

<div class="drop-zone" onclick="document.getElementById('file').click()">

<p id="uploadText"><b>Click to select video</b><br>or drag video here</p>

<input id="file" type="file" name="video" required style="display:none" onchange="showFile()">

<div class="file-preview" id="filePreview">

<span id="fileName"></span>

<span class="remove" onclick="removeFile()">✖</span>

</div>

</div>

<center>

<button type="submit">Generate Panorama</button>

</center>

<div class="progress" id="progress">

<div class="bar" id="bar"></div>

</div>

</form>

{% if result %}

<h2>Panorama Result</h2>

<img src="/outputs/{{result}}">

<br>

<a href="/outputs/{{result}}" download>

<button>Download Image</button>

</a>

{% endif %}

</div>

</div>

<footer>

Made by Arnav And Amit • Group-6.3 • EE-VDT • 3rd Year

</footer>

<script>

function showFile(){

let file=document.getElementById("file").files[0]

document.getElementById("fileName").innerText=file.name

document.getElementById("filePreview").style.display="flex"

document.getElementById("uploadText").style.display="none"

}

function removeFile(){

document.getElementById("file").value=""

document.getElementById("filePreview").style.display="none"

document.getElementById("uploadText").style.display="block"

}

function startProgress(){

let bar=document.getElementById("bar")
let prog=document.getElementById("progress")

prog.style.display="block"

let width=0

let id=setInterval(function(){

if(width>=90) clearInterval(id)
else{

width+=5
bar.style.width=width+"%"

}

},200)

}

</script>

</body>

</html>

"""

# ------------------------------------------------
# ROUTES
# ------------------------------------------------

@app.route("/")
def home():
    return render_template_string(HTML)


@app.route("/process",methods=["POST"])
def process():

    file=request.files["video"]

    path=os.path.join(UPLOAD_FOLDER,file.filename)

    file.save(path)

    result=process_video(path)

    return render_template_string(HTML,result=result)


@app.route("/outputs/<filename>")
def output_file(filename):
    return send_from_directory(OUTPUT_FOLDER,filename)


if __name__=="__main__":
    port = int(os.environ.get("PORT", 8080))

    app.run(host="0.0.0.0", port=port)
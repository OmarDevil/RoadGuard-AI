const API_BASE = window.localStorage.getItem("roadguard:apiBase") || "http://127.0.0.1:8000";

document.addEventListener("DOMContentLoaded", () => {
  if (document.getElementById("uploadBtn")) {
    initUploadPage();
  }
  if (document.getElementById("processedVideo")) {
    initDashboardPage();
  }
});

function initUploadPage() {
  const fileInput = document.getElementById("videoFile");
  const fileName = document.getElementById("fileName");
  const uploadBtn = document.getElementById("uploadBtn");
  const analyzeBtn = document.getElementById("analyzeBtn");
  const statusMessage = document.getElementById("statusMessage");
  const dashboardLink = document.getElementById("dashboardLink");
  const progressPanel = document.getElementById("analysisProgress");
  let uploadedVideoId = null;
  let selectedVideoDurationSeconds = null;
  let progressController = null;

  fileInput.addEventListener("change", async () => {
    const file = fileInput.files[0];
    fileName.textContent = file ? file.name : "Choose MP4, AVI, MOV, MKV, or WebM";
    analyzeBtn.disabled = true;
    uploadedVideoId = null;
    selectedVideoDurationSeconds = null;
    dashboardLink.classList.add("hidden");
    resetAnalysisProgress();

    if (file) {
      selectedVideoDurationSeconds = await readVideoDuration(file);
      const durationText = selectedVideoDurationSeconds
        ? ` - ${formatDuration(selectedVideoDurationSeconds)}`
        : "";
      fileName.textContent = `${file.name}${durationText}`;
    }
  });

  uploadBtn.addEventListener("click", async () => {
    const file = fileInput.files[0];
    if (!file) {
      setStatus(statusMessage, "Choose a video file first.", true);
      return;
    }

    const formData = new FormData();
    formData.append("file", file);
    setStatus(statusMessage, "Uploading video...");
    resetAnalysisProgress();

    try {
      const response = await fetch(`${API_BASE}/upload-video`, {
        method: "POST",
        body: formData,
      });
      const data = await readJson(response);
      uploadedVideoId = data.video_id;
      analyzeBtn.disabled = false;
      setStatus(statusMessage, `Uploaded ${data.filename}. Video ID: ${uploadedVideoId}.`);
    } catch (error) {
      setStatus(statusMessage, error.message, true);
    }
  });

  analyzeBtn.addEventListener("click", async () => {
    if (!uploadedVideoId) {
      setStatus(statusMessage, "Upload a video before analysis.", true);
      return;
    }

    analyzeBtn.disabled = true;
    uploadBtn.disabled = true;
    setStatus(statusMessage, "Analysis running. This can take several minutes for longer videos...");
    progressPanel.classList.remove("hidden");
    progressController = startAnalysisProgressEstimate(fileInput.files[0], selectedVideoDurationSeconds);

    try {
      const response = await fetch(`${API_BASE}/analyze/${uploadedVideoId}`, { method: "POST" });
      const result = await readJson(response);
      finishAnalysisProgress(progressController);
      window.localStorage.setItem(`roadguard:lastResult:${uploadedVideoId}`, JSON.stringify(result));
      dashboardLink.href = `dashboard.html?video_id=${uploadedVideoId}`;
      dashboardLink.classList.remove("hidden");
      setStatus(statusMessage, "Analysis complete.");
    } catch (error) {
      failAnalysisProgress(progressController);
      setStatus(statusMessage, error.message, true);
    } finally {
      analyzeBtn.disabled = false;
      uploadBtn.disabled = false;
      progressController = null;
    }
  });
}

async function initDashboardPage() {
  const videoId = await resolveVideoId();
  if (!videoId) {
    setDashboardStatus("No video selected. Upload and analyze a video first.", true);
    return;
  }

  try {
    const [video, analytics, violations] = await Promise.all([
      fetchJson(`${API_BASE}/videos/${videoId}`),
      fetchJson(`${API_BASE}/analytics/${videoId}`).catch(() => null),
      fetchJson(`${API_BASE}/violations/${videoId}`).catch(() => []),
    ]);

    const cachedResult = getCachedResult(videoId);
    const laneCounts = analytics?.lane_counts || cachedResult?.lane_counts || {};
    const totalVehicles = analytics?.total_vehicles ?? cachedResult?.total_vehicles ?? 0;
    const congestionLevel = analytics?.congestion_level || cachedResult?.congestion_summary?.max_level || "Low";

    document.getElementById("videoTitle").textContent = video.filename;
    document.getElementById("processedVideo").src = `${API_BASE}/processed-video/${videoId}`;
    setDashboardStatus(video.status === "completed" ? "Processed video ready." : `Status: ${video.status}`);

    document.getElementById("totalVehicles").textContent = totalVehicles;
    document.getElementById("congestionLevel").textContent = congestionLevel;
    document.getElementById("totalViolations").textContent = violations.length;
    document.getElementById("busiestLane").textContent = findBusiestLane(laneCounts);

    renderViolationCounts(violations);
    renderViolationsTable(violations);
    renderLaneChart(laneCounts);
    renderViolationChart(violations);
    renderCongestionChart(cachedResult?.congestion_timeline || []);
  } catch (error) {
    setDashboardStatus(error.message, true);
  }
}

async function resolveVideoId() {
  const params = new URLSearchParams(window.location.search);
  const fromQuery = params.get("video_id");
  if (fromQuery) {
    return fromQuery;
  }

  const videos = await fetchJson(`${API_BASE}/videos`).catch(() => []);
  return videos.length ? videos[0].id : null;
}

function renderViolationCounts(violations) {
  const counts = countBy(violations, "violation_type");
  document.getElementById("wrongWayCount").textContent = counts.WRONG_WAY || 0;
  document.getElementById("helmetCount").textContent = counts.NO_HELMET || 0;
  document.getElementById("pedestrianCount").textContent = counts.PEDESTRIAN_OUTSIDE_CROSSWALK || 0;
}

function renderViolationsTable(violations) {
  const table = document.getElementById("violationsTable");
  if (!violations.length) {
    table.innerHTML = `<tr><td colspan="5">No violations detected.</td></tr>`;
    return;
  }

  table.innerHTML = violations.map((violation) => {
    const confidence = violation.confidence === null || violation.confidence === undefined
      ? "-"
      : Number(violation.confidence).toFixed(2);
    const screenshot = violation.screenshot_path
      ? `<a href="${screenshotUrl(violation.screenshot_path)}" target="_blank" rel="noreferrer">Open</a>`
      : "-";

    return `
      <tr>
        <td>${escapeHtml(violation.frame_number)}</td>
        <td>${escapeHtml(violation.track_id ?? "-")}</td>
        <td>${escapeHtml(violation.violation_type)}</td>
        <td>${confidence}</td>
        <td>${screenshot}</td>
      </tr>
    `;
  }).join("");
}

function renderLaneChart(laneCounts) {
  const labels = Object.keys(laneCounts);
  const values = Object.values(laneCounts);
  new Chart(document.getElementById("laneChart"), {
    type: "bar",
    data: {
      labels,
      datasets: [{
        label: "Vehicles",
        data: values,
        backgroundColor: "#34c7a0",
        borderRadius: 6,
      }],
    },
    options: baseChartOptions(),
  });
}

function renderViolationChart(violations) {
  const counts = countBy(violations, "violation_type");
  new Chart(document.getElementById("violationChart"), {
    type: "pie",
    data: {
      labels: Object.keys(counts),
      datasets: [{
        data: Object.values(counts),
        backgroundColor: ["#ff5f6d", "#ffca5f", "#4aa3ff", "#34c7a0"],
      }],
    },
    options: baseChartOptions(),
  });
}

function renderCongestionChart(timeline) {
  const levelScore = { Low: 1, Medium: 2, High: 3 };
  const labels = timeline.map((item) => item.frame_number);
  const values = timeline.map((item) => levelScore[item.level] || 1);

  new Chart(document.getElementById("congestionChart"), {
    type: "line",
    data: {
      labels,
      datasets: [{
        label: "Congestion Level",
        data: values,
        borderColor: "#4aa3ff",
        backgroundColor: "rgba(74, 163, 255, 0.18)",
        tension: 0.25,
        fill: true,
      }],
    },
    options: {
      ...baseChartOptions(),
      scales: {
        x: { ticks: { color: "#94a4b2" }, grid: { color: "#2d3945" }, title: { display: true, text: "Frame", color: "#94a4b2" } },
        y: {
          min: 0,
          max: 3,
          ticks: {
            color: "#94a4b2",
            stepSize: 1,
            callback: (value) => ["", "Low", "Medium", "High"][value] || "",
          },
          grid: { color: "#2d3945" },
        },
      },
    },
  });
}

function baseChartOptions() {
  return {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        labels: { color: "#d8e3ea" },
      },
    },
    scales: {
      x: { ticks: { color: "#94a4b2" }, grid: { color: "#2d3945" } },
      y: { ticks: { color: "#94a4b2" }, grid: { color: "#2d3945" } },
    },
  };
}

async function fetchJson(url) {
  const response = await fetch(url);
  return readJson(response);
}

async function readJson(response) {
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(data.detail || `Request failed with status ${response.status}`);
  }
  return data;
}

function getCachedResult(videoId) {
  try {
    return JSON.parse(window.localStorage.getItem(`roadguard:lastResult:${videoId}`));
  } catch {
    return null;
  }
}

function countBy(items, key) {
  return items.reduce((acc, item) => {
    const value = item[key] || "UNKNOWN";
    acc[value] = (acc[value] || 0) + 1;
    return acc;
  }, {});
}

function findBusiestLane(laneCounts) {
  const entries = Object.entries(laneCounts);
  if (!entries.length) {
    return "-";
  }
  return entries.sort((a, b) => b[1] - a[1])[0][0];
}

function screenshotUrl(path) {
  const filename = String(path).split(/[\\/]/).pop();
  return `${API_BASE}/screenshots/${encodeURIComponent(filename)}`;
}

function setStatus(element, message, isError = false) {
  element.textContent = message;
  element.style.color = isError ? "#ff5f6d" : "#94a4b2";
}

function setDashboardStatus(message, isError = false) {
  setStatus(document.getElementById("videoStatus"), message, isError);
}

function startAnalysisProgressEstimate(file, durationSeconds) {
  const startedAt = Date.now();
  const estimatedSeconds = estimateAnalysisDurationSeconds(file, durationSeconds);
  const controller = { timerId: null, done: false };

  updateProgressBar({
    percent: 1,
    label: "Preparing analysis...",
    elapsedSeconds: 0,
    remainingSeconds: estimatedSeconds,
  });

  controller.timerId = window.setInterval(() => {
    const elapsedSeconds = (Date.now() - startedAt) / 1000;
    const rawPercent = (elapsedSeconds / estimatedSeconds) * 95;
    const percent = Math.min(95, Math.max(1, rawPercent));
    const remainingSeconds = Math.max(0, estimatedSeconds - elapsedSeconds);
    const label = percent >= 95 ? "Finalizing output video..." : "Analyzing video...";

    updateProgressBar({
      percent,
      label,
      elapsedSeconds,
      remainingSeconds,
    });
  }, 500);

  return controller;
}

function finishAnalysisProgress(controller) {
  stopProgressTimer(controller);
  updateProgressBar({
    percent: 100,
    label: "Analysis complete",
    elapsedSeconds: null,
    remainingSeconds: 0,
  });
}

function failAnalysisProgress(controller) {
  stopProgressTimer(controller);
  const progressLabel = document.getElementById("progressLabel");
  if (progressLabel) {
    progressLabel.textContent = "Analysis failed";
  }
}

function resetAnalysisProgress() {
  document.getElementById("analysisProgress")?.classList.add("hidden");
  updateProgressBar({
    percent: 0,
    label: "Analysis pending",
    elapsedSeconds: 0,
    remainingSeconds: null,
  });
}

function stopProgressTimer(controller) {
  if (controller?.timerId) {
    window.clearInterval(controller.timerId);
  }
}

function updateProgressBar({ percent, label, elapsedSeconds, remainingSeconds }) {
  const safePercent = Math.round(Math.max(0, Math.min(100, percent)));
  const progressFill = document.getElementById("progressFill");
  const progressTrack = document.getElementById("progressTrack");
  const progressLabel = document.getElementById("progressLabel");
  const progressPercent = document.getElementById("progressPercent");
  const elapsedTime = document.getElementById("elapsedTime");
  const remainingTime = document.getElementById("remainingTime");

  if (progressFill) {
    progressFill.style.width = `${safePercent}%`;
  }
  if (progressTrack) {
    progressTrack.setAttribute("aria-valuenow", String(safePercent));
  }
  if (progressLabel) {
    progressLabel.textContent = label;
  }
  if (progressPercent) {
    progressPercent.textContent = `${safePercent}%`;
  }
  if (elapsedTime && elapsedSeconds !== null) {
    elapsedTime.textContent = `Elapsed: ${formatDuration(elapsedSeconds)}`;
  }
  if (remainingTime) {
    remainingTime.textContent = remainingSeconds === null
      ? "Remaining: estimating..."
      : `Remaining: ${formatDuration(remainingSeconds)}`;
  }
}

function estimateAnalysisDurationSeconds(file, durationSeconds) {
  const fileSizeMb = file ? file.size / (1024 * 1024) : 0;
  const durationEstimate = durationSeconds ? durationSeconds * 2.5 : 0;
  const sizeEstimate = fileSizeMb * 1.4;
  return clamp(Math.max(20, durationEstimate, sizeEstimate), 20, 30 * 60);
}

function readVideoDuration(file) {
  return new Promise((resolve) => {
    const objectUrl = URL.createObjectURL(file);
    const video = document.createElement("video");
    video.preload = "metadata";
    video.onloadedmetadata = () => {
      URL.revokeObjectURL(objectUrl);
      resolve(Number.isFinite(video.duration) ? video.duration : null);
    };
    video.onerror = () => {
      URL.revokeObjectURL(objectUrl);
      resolve(null);
    };
    video.src = objectUrl;
  });
}

function formatDuration(totalSeconds) {
  const seconds = Math.max(0, Math.round(totalSeconds));
  const minutes = Math.floor(seconds / 60);
  const remainingSeconds = seconds % 60;
  return `${String(minutes).padStart(2, "0")}:${String(remainingSeconds).padStart(2, "0")}`;
}

function clamp(value, min, max) {
  return Math.min(max, Math.max(min, value));
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

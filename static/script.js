const form = document.getElementById("uploadForm");
const loader = document.getElementById("loader");
const downloadLink = document.getElementById("downloadLink");
const loadingText = document.getElementById("loadingText");
const alphaSlider = document.getElementById("alpha");
const alphaValue = document.getElementById("alphaValue");

alphaSlider.addEventListener("input", function () {
  alphaValue.textContent = alphaSlider.value;
});

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  loader.style.display = "block";
  loadingText.style.display = "flex";
  loadingText.textContent = "Processing ...";
  downloadLink.innerHTML = "";

  const formData = new FormData(form);
  const backgroundColor = document.getElementById("color").value.slice(1);
  const r = parseInt(backgroundColor.slice(0, 2), 16);
  const g = parseInt(backgroundColor.slice(2, 4), 16);
  const b = parseInt(backgroundColor.slice(4, 6), 16);
  const alpha = parseInt(alphaSlider.value);

  formData.append("color_r", r);
  formData.append("color_g", g);
  formData.append("color_b", b);
  formData.append("alpha", alpha); // Using alpha from slider

  const response = await fetch("/process", {
    method: "POST",
    body: formData,
  });
  const data = await response.json();

  loader.style.display = "none";
  loadingText.style.display = "none";

  if (data.client_id) {
    const link = document.createElement("a");
    link.href = `/download/${data.client_id}`;
    link.textContent = "Download Images";
    link.className = "download-link"; // Add a class to the link
    link.download = "processed_images.zip";
    downloadLink.appendChild(link);
  } else {
    downloadLink.textContent = "Error processing images.";
  }
});

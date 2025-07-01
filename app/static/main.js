document.addEventListener("DOMContentLoaded", () => {
    // --- Elements ---
    const qrColorInput = document.getElementById("qrColor");
    const bgColorInput = document.getElementById("bgColor");
    const qrColorPreview = document.getElementById("qrColorPreview");
    const bgColorPreview = document.getElementById("bgColorPreview");
    const qrSwatches = document.querySelectorAll(".qr-swatch");
    const bgSwatches = document.querySelectorAll(".bg-swatch");
    const qrResult = document.getElementById("qrResult");
    const qrActions = document.getElementById("qrActions");
    const qrColorValue = document.getElementById("qrColorValue");
    const bgColorValue = document.getElementById("bgColorValue");
    let currentCanvas = null;

    // --- Utility ---
    function updatePreview(input, preview, swatches, type) {
        const color = input.value;
        preview.style.backgroundColor = color;
        // Accessibility: add border for light backgrounds
        if (type === "bg" && ["#ffffff", "#f9fafb", "#eff6ff", "#ecfdf5", "#f5f3ff"].includes(color.toLowerCase())) {
            preview.classList.add("border-gray-300");
        } else {
            preview.classList.remove("border-gray-300");
        }
        // Highlight swatch if color matches, else remove all highlights
        let found = false;
        swatches.forEach(btn => {
            if (btn.dataset.color.toLowerCase() === color.toLowerCase()) {
                btn.classList.add("ring-2", "ring-blue-500");
                btn.setAttribute("aria-checked", "true");
                found = true;
            } else {
                btn.classList.remove("ring-2", "ring-blue-500");
                btn.setAttribute("aria-checked", "false");
            }
        });
        if (!found) {
            swatches.forEach(btn => btn.classList.remove("ring-2", "ring-blue-500"));
        }
    }

    // --- Swatch click logic ---
    function handleSwatchClick(e, input, preview, swatches, type) {
        const color = e.target.dataset.color;
        input.value = color;
        input.dispatchEvent(new Event("input", { bubbles: true }));
        // Animation
        e.target.style.transform = "scale(0.95)";
        setTimeout(() => { e.target.style.transform = ""; }, 120);
    }

    // --- Color picker open on preview click ---
    qrColorPreview.addEventListener("click", () => qrColorInput.click());
    bgColorPreview.addEventListener("click", () => bgColorInput.click());

    // --- Swatch click events ---
    qrSwatches.forEach(btn => {
        btn.addEventListener("click", e => handleSwatchClick(e, qrColorInput, qrColorPreview, qrSwatches, "qr"));
        btn.addEventListener("touchstart", e => handleSwatchClick(e, qrColorInput, qrColorPreview, qrSwatches, "qr"), { passive: true });
    });
    bgSwatches.forEach(btn => {
        btn.addEventListener("click", e => handleSwatchClick(e, bgColorInput, bgColorPreview, bgSwatches, "bg"));
        btn.addEventListener("touchstart", e => handleSwatchClick(e, bgColorInput, bgColorPreview, bgSwatches, "bg"), { passive: true });
    });

    // --- Color input events (manual pick) ---
    qrColorInput.addEventListener("input", () => {
        updatePreview(qrColorInput, qrColorPreview, qrSwatches, "qr");
        qrColorValue.textContent = qrColorInput.value;
        generateQRCode();
    });
    bgColorInput.addEventListener("input", () => {
        updatePreview(bgColorInput, bgColorPreview, bgSwatches, "bg");
        bgColorValue.textContent = bgColorInput.value;
        generateQRCode();
    });

    // --- QR code regeneration on data change ---
    document.getElementById("qrData").addEventListener("input", generateQRCode);
    document.getElementById("qrSize").addEventListener("change", generateQRCode);

    // --- QR code generation ---
    function generateQRCode() {
        const data = document.getElementById("qrData").value.trim();
        const size = parseInt(document.getElementById("qrSize").value);
        const color = qrColorInput.value;
        const bgColor = bgColorInput.value;
        if (!data) return;
        qrResult.innerHTML = "";
        qrActions.classList.add("hidden");
        const qrContainer = document.createElement("div");
        new QRCode(qrContainer, {
            text: data,
            width: size,
            height: size,
            colorDark: color,
            colorLight: bgColor,
            correctLevel: QRCode.CorrectLevel.H,
        });
        qrResult.appendChild(qrContainer);
        currentCanvas = qrContainer.querySelector("canvas");
        if (currentCanvas) qrActions.classList.remove("hidden");
    }

    // --- Initial state ---
    updatePreview(qrColorInput, qrColorPreview, qrSwatches, "qr");
    updatePreview(bgColorInput, bgColorPreview, bgSwatches, "bg");
    generateQRCode();

    // Download and copy logic
    document.getElementById("downloadBtn").addEventListener("click", () => {
        if (!currentCanvas) return;
        const link = document.createElement("a");
        link.download = "qr-code.png";
        link.href = currentCanvas.toDataURL("image/png");
        link.click();
    });
    document.getElementById("copyBtn").addEventListener("click", () => {
        if (!currentCanvas) return;
        currentCanvas.toBlob((blob) => {
            const item = new ClipboardItem({ "image/png": blob });
            navigator.clipboard.write([item]).then(() => {
                const copyBtn = document.getElementById("copyBtn");
                const originalText = copyBtn.innerHTML;
                copyBtn.innerHTML = `
                    <svg class="w-5 h-5" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                        <path d="M5 13l4 4L19 7" stroke-linecap="round" stroke-linejoin="round"/>
                    </svg>
                    Copied!
                `;
                setTimeout(() => {
                    copyBtn.innerHTML = originalText;
                }, 1500);
            });
        });
    });

    // Initialize on load
    qrColorValue.textContent = qrColorInput.value;
    bgColorValue.textContent = bgColorInput.value;
});
  
  
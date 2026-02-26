const glyphMap = {
    "sun": "☉", "moon": "☽", "mercury": "☿", "venus": "♀", "mars": "♂", 
    "jupiter": "♃", "saturn": "♄", "uranus": "♅", "neptune": "♆", "pluto": "♇",
    "chiron": "⚷", "juno": "⚵", "rising": "ASC", "part_of_fortune": "⊗", "regulus": "★"
};

let planetSignText = {};
let planetHouseText = {};
let chartData = {};

const canvas = document.getElementById('starCanvas');
const ctx = canvas.getContext('2d');
let stars = [];

function resize() { 
    canvas.width = window.innerWidth; 
    canvas.height = window.innerHeight; 
}
window.onresize = resize; resize();

for(let i=0; i<150; i++) {
    stars.push({
        x: Math.random() * canvas.width,
        y: Math.random() * canvas.height,
        size: Math.random() * 1.5,
        speed: Math.random() * 0.2 + 0.05,
        opacity: Math.random()
    });
}

function animate() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    stars.forEach(s => {
        ctx.fillStyle = `rgba(26, 42, 68, ${s.opacity})`; 
        ctx.beginPath(); ctx.arc(s.x, s.y, s.size, 0, Math.PI * 2); ctx.fill();
        s.y -= s.speed;
        if (s.y < 0) s.y = canvas.height;
    });
    requestAnimationFrame(animate);
}
animate();

async function loadInterpretations() {
    const res = await fetch("/interpretations");
    const data = await res.json();
    planetSignText = data.planet_sign;
    planetHouseText = data.planet_house;
}
loadInterpretations();

flatpickr("#date", { dateFormat: "Y-m-d" });
flatpickr("#time", { enableTime:true, noCalendar:true, dateFormat:"H:i", time_24hr:true });

const cityInput = document.getElementById("city");
const suggestions = document.getElementById("suggestions");

cityInput.addEventListener("input", async () => {
    const q = cityInput.value;
    if(q.length < 3) { suggestions.innerHTML = ""; return; }
    const res = await fetch(`https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(q)}&limit=5`);
    const data = await res.json();
    suggestions.innerHTML = "";
    data.forEach(place => {
        const li = document.createElement("li");
        li.textContent = place.display_name;
        li.onclick = () => { cityInput.value = place.display_name; suggestions.innerHTML = ""; };
        suggestions.appendChild(li);
    });
});


document.getElementById("astroForm").onsubmit = async e => {
    e.preventDefault();
    const submitBtn = e.target.querySelector('button');
    submitBtn.innerText = "CALCULATING...";

    const res = await fetch("/chart", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({
            date: document.getElementById("date").value, 
            time: document.getElementById("time").value, 
            city: document.getElementById("city").value
        })
    });
    
    const data = await res.json();
    chartData = data.chart;
    submitBtn.innerText = "GENERATE CHART";
    
    const resultsDiv = document.getElementById("results");
    resultsDiv.innerHTML = "";

    const order = ["sun","moon","mercury","venus","mars","jupiter","saturn","uranus","neptune","pluto","chiron","part_of_fortune","regulus","juno","rising"];

    order.forEach(key => {
        const obj = chartData[key];
        if(!obj) return;
        const card = document.createElement("div");
        card.className = "card";
        card.innerHTML = `
            <span class="glyph">${glyphMap[key] || ""}</span>
            <h2>${key.replace(/_/g,' ').toUpperCase()}</h2>
            <p style="font-weight:600; font-size: 1.1rem;">${obj.sign}</p>
            <small style="color:var(--accent-soft);">House ${obj.house}</small>
        `;
        card.onclick = () => showDetail(key);
        resultsDiv.appendChild(card);
    });
    document.getElementById("pdf-section").style.display = "block";
};

async function downloadPDF() {
    const btn = document.getElementById("pdfBtn");
    btn.innerText = "PREPARING REPORT...";
    
    const res = await fetch("/export-pdf", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({ 
            chart: chartData, 
            user: {
                date: document.getElementById("date").value, 
                time: document.getElementById("time").value, 
                city: document.getElementById("city").value
            } 
        })
    });
    
    const blob = await res.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `Cosmic_Report.pdf`;
    a.click();
    btn.innerText = "DOWNLOAD COSMIC REPORT (PDF)";
}


function showDetail(key) {
    const obj = chartData[key];
    const nameMap = { "part_of_fortune": "Part of Fortune", "regulus": "Regulus", "rising": "Rising" };
    const planetName = nameMap[key] || key.charAt(0).toUpperCase()+key.slice(1);
    
    document.getElementById("mainUI").style.display = "none";
    document.getElementById("detailView").style.display = "block";
    
    document.getElementById("detailGlyph").innerText = glyphMap[key] || "";
    document.getElementById("detailTitle").innerText = planetName;
    
    const sText = planetSignText[planetName]?.[obj.sign] || "";
    const hText = planetHouseText[planetName]?.[obj.house] || "";

    document.getElementById("detailBody").innerHTML = `
        <p style="font-size:18px; font-weight:bold; color:var(--ink-blue); text-align:center;">${obj.sign} — ${obj.degree}° — House ${obj.house}</p>
        <hr style="border:0; border-top:1px solid var(--ink-blue); opacity:0.2; margin:30px 0;">
        ${sText ? `<p>${sText}</p>` : ""}${hText ? `<p>${hText}</p>` : ""}`;
    window.scrollTo(0,0);
}

function showGrid() {
    document.getElementById("detailView").style.display = "none";
    document.getElementById("mainUI").style.display = "block";
}
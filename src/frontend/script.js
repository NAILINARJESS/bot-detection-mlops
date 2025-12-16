const form = document.getElementById("predict-form");
const result = document.getElementById("result");

form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const features = JSON.parse(document.getElementById("features").value);

    try {
        const response = await fetch("http://localhost:8000/predict", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(features)
        });

        if (!response.ok) throw new Error(await response.text());

        const data = await response.json();
        result.textContent = JSON.stringify(data, null, 2);
    } catch (err) {
        result.textContent = "Erreur : " + err;
    }
});


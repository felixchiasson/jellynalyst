async function fetchStats() {
  const response = await fetch("/api/stats");
  const data = await response.json();
  // Will implement chart rendering here
  console.log("Stats data:", data);
}

document.addEventListener("DOMContentLoaded", fetchStats);
